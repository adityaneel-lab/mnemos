
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ollama import chat
from backend.memory import build_context

from backend.database import (
    SessionLocal,
    Conversation,
    Message,
    create_tables,
)

app = FastAPI(
    title="Real Memory Chatbot",
    version="0.2.0",
)

MODEL_NAME = "qwen3.5:0.8b"

SYSTEM_PROMPT = (
    "You are a helpful conversational assistant. "
    "Give clear and concise answers."
)

create_tables()


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str


@app.get("/")
def home():
    return {
        "status": "running",
        "project": "Real Memory Chatbot",
    }


@app.post("/conversations")
def create_conversation():
    db: Session = SessionLocal()

    try:
        conversation = Conversation()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return {
            "id": conversation.id,
            "title": conversation.title,
        }
    finally:
        db.close()


@app.get("/conversations")
def get_conversations():
    db: Session = SessionLocal()

    try:
        conversations = (
            db.query(Conversation)
            .order_by(Conversation.id.desc())
            .all()
        )

        return [
            {
                "id": item.id,
                "title": item.title,
            }
            for item in conversations
        ]
    finally:
        db.close()


@app.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int):
    db: Session = SessionLocal()

    try:
        conversation = db.get(Conversation, conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in conversation.messages
        ]
    finally:
        db.close()


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    db: Session = SessionLocal()

    try:
        conversation = db.get(
            Conversation,
            request.conversation_id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        # Save the user's message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )
        db.add(user_message)

        # Set conversation title from its first message
        if conversation.title == "New conversation":
            conversation.title = request.message[:50]

        db.commit()

        # Retrieve the complete conversation history
        history = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id
            )
            .order_by(Message.id)
            .all()
        )

        history_data = [
            {
                "role": item.role,
                "content": item.content,
            }
            for item in history
        ]

        context = build_context(history_data)

        messages = context["messages"]

        print(
            f"Context tokens: {context['token_count']} | "
            f"Messages sent: {context['message_count']} | "
            f"Messages stored: {len(history_data)}"
        )

        # Generate response using Ollama
        response = chat(
            model=MODEL_NAME,
            messages=messages,
        )

        reply = response.message.content

        # Save the assistant's response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply,
        )

        db.add(assistant_message)
        db.commit()

        return ChatResponse(
            conversation_id=conversation.id,
            reply=reply,
        )

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to process chat request. Check backend logs.",
        )
    finally:
        db.close()
