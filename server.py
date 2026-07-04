"""FastAPI backend for the BD Knowledge Agent website.

Serves the JSON chat API the frontend (``web/index.html``) calls, and serves that
same frontend as static files — so the whole animated website ships as one process.

Run with:  ``uvicorn server:app --reload``
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.agent import build_agent
from src.config import provider_status

app = FastAPI(title="BD Knowledge Agent API")

_agent_cache: dict[str, object] = {}


def get_agent():
    """Build the agent once per process and reuse it across requests."""
    if "agent" not in _agent_cache:
        _agent_cache["agent"] = build_agent()
    return _agent_cache["agent"]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    tools: list[str]
    provider: str


@app.get("/api/status")
def status():
    return provider_status()


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message must not be empty")

    status_info = provider_status()
    if not status_info["has_key"]:
        raise HTTPException(
            status_code=503,
            detail=f"No {status_info['key_env']} configured on the server.",
        )

    try:
        agent = get_agent()
        result = agent.invoke({"input": message})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    tools_used = [
        action.tool for action, _observation in result.get("intermediate_steps", [])
    ]
    return ChatResponse(
        answer=result["output"],
        tools=tools_used,
        provider=status_info["provider"],
    )


WEB_DIR = Path(__file__).resolve().parent / "web"
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
