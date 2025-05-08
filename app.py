import base64
import os
from typing import Dict, List
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from llm_utils.agentv2 import AgentManager
from llm_utils.llm_pov import create_pov
from pathlib import Path
from llm_utils.llm_chat import ChatAgent, OppositeChatAgent, NeutralChatAgent, EmphaticChatAgent, AgentMessage
import asyncio
import firebase_admin
from firebase_admin import firestore, credentials
import json
from utils.chat import load_chat_history, save_message, serialize_chat_history_to_json
from langchain.schema import HumanMessage

load_dotenv()

app = FastAPI()

firebase_account_json_str = base64.b64decode(os.environ['FIREBASE_SERVICE_ACCOUNT']).decode('utf-8')
print(firebase_account_json_str)

firebase_account_json_str = base64.b64decode(os.environ['FIREBASE_SERVICE_ACCOUNT']).decode('utf-8')
service_account_info = json.loads(firebase_account_json_str)

if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
db = firestore.client()

consecutive_agent_responses = 0
MAX_AGENT_CHAIN = 5

# Serve React app (build)
client_path = Path("client/out")
app.mount("/static", StaticFiles(directory=client_path), name="static")

connected_clients = []
active_agents_by_conversation: Dict[str, List[ChatAgent]] = {}

async def broadcast(chat_history):
    for client in connected_clients:
        await client.send_json(chat_history)

async def agent_loop(agent: ChatAgent, user_id):
    conversation_id = agent.conv_id
    last_seen = 0

    while True:
        global consecutive_agent_responses

        print(f"Consecutive agent responses: {consecutive_agent_responses}")

        if consecutive_agent_responses >= MAX_AGENT_CHAIN:
            await asyncio.sleep(1)
            
            # Fine loop → rimuovi agente
            active_agents_by_conversation[conversation_id].remove(agent)
            if not active_agents_by_conversation[conversation_id]:
                del active_agents_by_conversation[conversation_id]

            continue

        print(f"Agent {agent.agent_name} is running")

        chat_history = await load_chat_history(db, user_id, conversation_id)
        print(f"Chat history: {chat_history}")
        print(f"Last seen: {last_seen}")
        if len(chat_history) > last_seen:
            last_seen = len(chat_history)
            print("")
            response = agent.generate_chat_answer(chat_history)
            consecutive_agent_responses += 1
            if response:
                chat_history.append(response)
                await broadcast()

        await asyncio.sleep(1)
    

@app.websocket("/ws/{user_id}/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, conversation_id: str):
    global consecutive_agent_responses

    await websocket.accept()
    connected_clients.append(websocket)
    try:
        print(user_id)
        print(conversation_id)

        chat_history = await load_chat_history(db, user_id, conversation_id)

        await websocket.send_json(chat_history)
        while True:
            data = await websocket.receive_json()
            
            message = {"role": "user", "content": data["text"]}
            await save_message(user_id, conversation_id, message)
            chat_history.append(message)
            consecutive_agent_responses = 0

            print(f"chathistory: {chat_history}")

            await broadcast()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@app.get("/messages/{user_id}/{conversation_id}")
async def get_messages(user_id: str, conversation_id: str):
    print(f"Fetching messages for user {user_id} and conversation {conversation_id}")
    chat_history = await load_chat_history(db, user_id, conversation_id)

    chat_history_json = serialize_chat_history_to_json(chat_history)
    return JSONResponse(content=chat_history_json)

@app.post("/api/processpov")
async def process_pov(request: Request):
    data = await request.json()
    perspective = data.get("perspective")
    user_text = data.get("userText")
    conv_id = data.get("convId")
    user_id = data.get("userId")

    if not conv_id:
        print("No conversation ID provided, creating a new one.")
        conv_id =str(uuid.uuid4())

        #set first msg
        await save_message(db, user_id=user_id, conversation_id=conv_id,message=HumanMessage(content=user_text))

    rewritten_text = create_pov(perspective, user_text)

    print(f"Perspective: {perspective}")

    if perspective == "Opposite" or perspective == "Opposto":
        agent = OppositeChatAgent(conv_id, rewritten_text)
        print(f"Agent: {agent.conv_id}")

        start_agent(agent, user_id)
    elif perspective == "Neutral" or perspective == "Neutrale":
        agent = NeutralChatAgent(conv_id, rewritten_text)
        start_agent(agent, user_id)
    elif perspective == "Emphatic" or perspective == "Empatico":
        agent = EmphaticChatAgent(conv_id, rewritten_text)
        start_agent(agent, user_id)

    #set msg
    await save_message(db, user_id=user_id, conversation_id=conv_id, message= AgentMessage(agent_name=perspective, content=rewritten_text))

    return {"conv_id": conv_id, "pov": rewritten_text}

def start_agent(agent: ChatAgent, user_id):
    conversation_id = agent.conv_id

    if conversation_id not in active_agents_by_conversation:
        active_agents_by_conversation[conversation_id] = []

    # Evita duplicati
    if any(type(existing_agent) == type(agent) for existing_agent in active_agents_by_conversation[conversation_id]):
        return

    active_agents_by_conversation[conversation_id].append(agent)
    asyncio.create_task(agent_loop(agent, user_id))

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    target_path = client_path / full_path
    if target_path.is_dir():
        index = target_path / "index.html"
        if index.exists():
            return FileResponse(index)
    elif target_path.exists():
        return FileResponse(target_path)

    fallback_index = client_path / "index.html"
    return FileResponse(fallback_index)

