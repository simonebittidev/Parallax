import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from llm_utils.agentv2 import AgentManager
from llm_utils.llm_pov import create_pov
from pathlib import Path

load_dotenv()

app = FastAPI()

# Serve React app (build)
client_path = Path("client/out")
app.mount("/static", StaticFiles(directory=client_path), name="static")

chat_history = []
agent_manager = AgentManager(chat_history)
connected_clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            message = {"role": "user", "content": data["text"]}
            chat_history.append(message)
            agent_manager.trigger_agents()

            print(chat_history)

            # Invia la chat aggiornata a tutti i client
            for client in connected_clients:
                await client.send_json(chat_history)

    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@app.get("/messages")
async def get_messages():
    return JSONResponse(content=chat_history)

@app.post("/api/processpov")
async def process_pov(request: Request):
    data = await request.json()
    perspective = data.get("perspective")
    user_text = data.get("userText")
    rewritten_text = create_pov(perspective, user_text)
    return {"pov": rewritten_text}

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
