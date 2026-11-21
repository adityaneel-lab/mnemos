
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ollama import chat

app = FastAPI(
    title="Real Memory Chatbot",
    description="A conversational AI with memory",
    version="0.1.0"
)

MODEL_NAME = "qwen3.5:4b"


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def home():
    return {"status": "running", "project": "Real Memory Chatbot"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):

    try:
        messages = [
            message.model_dump()
            for message in request.messages
        ]

        response = chat(
            model=MODEL_NAME,
            messages=messages
        )

        return ChatResponse(
            reply=response.message.content
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM request failed: {str(e)}"
        )
