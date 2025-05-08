import datetime
import asyncio
import json
from langchain.schema import HumanMessage, BaseMessage
from llm_utils.llm_chat import  AgentMessage

async def save_message(db, user_id: str, conversation_id: str, message: BaseMessage):
    if isinstance(message, HumanMessage):
        message = {
            "role": "user",
            "content": message.content,
            "agent_name": None,
            "timestamp": datetime.datetime.utcnow()
        }
    else:
        message = {
            "role": "assistant",
            "content": message.content,
            "agent_name": message.agent_name,
            "timestamp": datetime.datetime.utcnow()
        }
    
    ref = db.collection("users").document(user_id)\
        .collection("conversations").document(conversation_id)\
        .collection("messages")
    
    await asyncio.to_thread(lambda: ref.add(message))

async def load_chat_history(db, user_id: str, conversation_id: str) -> list:
    ref = db.collection("users").document(user_id)\
        .collection("conversations").document(conversation_id)\
        .collection("messages")
    
    docs = await asyncio.to_thread(lambda: ref.order_by("timestamp").stream())
    return [doc.to_dict() for doc in docs]

def serialize_to_timestamp(obj):
    if hasattr(obj, 'timestamp'):
        return obj.timestamp()
    raise TypeError(f"Type {type(obj)} not serializable")

def serialize_chat_history_to_json(chat_history):
    return json.dumps(chat_history, default=serialize_to_timestamp)


