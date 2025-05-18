import base64
import os
from typing import Dict, List
import uuid
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from langchain_google_firestore import FirestoreChatMessageHistory
from llm_utils.graph_executor import GraphExecutor, ActiveAgent, PovAgentMessage
from llm_utils.llm_pov import create_pov
from pathlib import Path
from llm_utils.llm_chat import ChatAgent
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

# Serve React app (build)
client_path = Path("client/out")
app.mount("/static", StaticFiles(directory=client_path), name="static")

connected_clients: Dict[str, List[WebSocket]] = {}
active_agents_by_conversation: Dict[str, List[ChatAgent]] = {}

def serialize_messages(messages):
    parsed_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            parsed_messages.append({
                "role": msg.type,
                "content": msg.content,
                "agent_name":  ""
            })
        else:
            parsed_messages.append({
                "role": msg.type,
                "content": msg.content,
                "agent_name": msg.agent_name
            })
    
    return json.dumps(parsed_messages)

@app.websocket("/ws/{user_id}/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, conversation_id: str):
    await websocket.accept()

    try:
        if conversation_id not in connected_clients:
            connected_clients[conversation_id] = []
            connected_clients[conversation_id].append(websocket)

        print(f"WebSocket connection established for user {user_id} and conversation {conversation_id}")

        while True:
            print(f"WebSocket received message for user {user_id} and conversation {conversation_id}")

            data = await websocket.receive_json()
            message=data["text"]
            print(f"Received message: {message}")

            graph_executor = GraphExecutor(conversation_id=conversation_id, db_client=db, active_agents=active_agents_by_conversation[conversation_id])
            await graph_executor.trigger_agents(connected_clients=connected_clients[conversation_id], msg=message)

    except WebSocketDisconnect:
        print(f"WebSocket disconnesso per user {user_id}, conv {conversation_id}")
        if conversation_id in connected_clients and websocket in connected_clients[conversation_id]:
            connected_clients[conversation_id].remove(websocket)

@app.get("/messages/{user_id}/{conversation_id}")
async def get_messages(user_id: str, conversation_id: str):
    print(f"Fetching messages for user {user_id} and conversation {conversation_id}")
    chat_history = GraphExecutor.get_chat_history(conversation_id, db)
    messages = serialize_messages(chat_history.messages)
    return JSONResponse(content=messages)

@app.post("/api/processpov")
async def process_pov(request: Request):
    data = await request.json()
    perspective = data.get("perspective")
    user_text = data.get("userText")
    conv_id = data.get("convId")
    user_id = data.get("userId")

    reload_graph = True
    chat_history = None

    if not conv_id:
        print("No conversation ID provided, creating a new one.")
        conv_id =str(uuid.uuid4())
        chat_history = GraphExecutor.get_chat_history(conv_id, db)
        chat_history.add_user_message(HumanMessage(content=user_text))
        reload_graph = False
    else:
        chat_history = GraphExecutor.get_chat_history(conv_id, db)

    rewritten_text = create_pov(perspective, user_text)

    if not rewritten_text:
        raise HTTPException(status_code=500, detail="Sorry, we couldn't generate the point of view at this time. Try rephrasing your input or please try again shortly.")

    print(f"Perspective: {perspective}")

    agent = ActiveAgent(name = perspective, pov = rewritten_text)

    if conv_id not in active_agents_by_conversation:
        active_agents_by_conversation[conv_id] = []

    active_agents_by_conversation[conv_id].append(agent)

    chat_history.add_message(PovAgentMessage(agent_name=perspective, content=rewritten_text))
    if reload_graph:
        # Force a reload of the graph
        graph_executor = GraphExecutor(conversation_id=conv_id, db_client=db, active_agents=active_agents_by_conversation[conv_id])
        await graph_executor.trigger_agents(connected_clients=connected_clients[conv_id], msg="")

    return {"conv_id": conv_id, "pov": rewritten_text}

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
