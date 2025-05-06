import datetime
import asyncio

async def save_message(db, user_id: str, conversation_id: str, message: dict):
    message["timestamp"] = datetime.datetime.utcnow()
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
