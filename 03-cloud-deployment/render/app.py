"""
Render-ready AI Agent demo.

This app is intentionally self-contained so Render can build it from
03-cloud-deployment/render without needing files from other lab folders.
"""
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


START_TIME = time.time()

app = FastAPI(title="Agent on Render", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def mock_ask(question: str) -> str:
    question_lower = question.lower()
    if "render" in question_lower:
        return "Render deploys this agent from render.yaml and routes traffic to the web service."
    if "deploy" in question_lower:
        return "Deployment moves the agent from localhost to a public cloud URL."
    return "This is a mock AI response from the Render-ready agent."


@app.get("/")
def root():
    return {
        "message": "AI Agent running on Render!",
        "platform": "Render",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/ask")
async def ask_agent(request: Request):
    body = await request.json()
    question = body.get("question", "")
    if not question:
        raise HTTPException(status_code=422, detail="question field is required")
    return {
        "question": question,
        "answer": mock_ask(question),
        "platform": "Render",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "platform": "Render",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
