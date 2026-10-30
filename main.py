from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from . import config, tickets
from .agent import SupportAgent
from .loader import SUPPORTED
from .watcher import start_watcher

STATIC = Path(__file__).resolve().parent.parent / "static"
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["agent"] = SupportAgent()
    state["observer"] = start_watcher(state["agent"].reindex)
    yield
    if state.get("observer"):
        state["observer"].stop()


app = FastAPI(title="Real-Time Customer Support RAG Agent", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class ChatIn(BaseModel):
    message: str
    session_id: str = "default"


class TicketIn(BaseModel):
    session_id: str = "default"
    email: str
    summary: str = ""


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    a = state["agent"]
    return {"status": "ok", "chunks": len(a.retriever.chunks), "retriever": config.RETRIEVER, "llm": a.llm.mode}


@app.post("/api/chat")
def chat(body: ChatIn):
    """Non-streaming endpoint (handy for curl / integrations)."""
    text, sources, esc, conf = "", [], False, 0.0
    for ev in state["agent"].handle(body.session_id, body.message):
        if ev["type"] == "token": text += ev["text"]
        elif ev["type"] == "sources": sources = ev["sources"]
        elif ev["type"] == "done": esc, conf = ev["escalate"], ev["confidence"]
    return {"answer": text, "sources": sources, "escalate": esc, "confidence": conf}


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            msg, sid = (data.get("message") or "").strip(), data.get("session_id", "default")
            if not msg:
                continue
            async for event in iterate_in_threadpool(state["agent"].handle(sid, msg)):
                await ws.send_json(event)
    except WebSocketDisconnect:
        pass


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    name = Path(file.filename or "").name
    if Path(name).suffix.lower() not in SUPPORTED:
        raise HTTPException(400, f"Unsupported type. Use: {', '.join(sorted(SUPPORTED))}")
    (config.KB_DIR / name).write_bytes(await file.read())
    n = await run_in_threadpool(state["agent"].reindex)
    return {"uploaded": name, "chunks": n}


@app.post("/api/reindex")
def reindex():
    return {"chunks": state["agent"].reindex()}


@app.post("/api/tickets")
def new_ticket(body: TicketIn):
    if "@" not in body.email:
        raise HTTPException(400, "A valid email is required")
    transcript = state["agent"].transcript(body.session_id)
    summary = body.summary or (transcript[:200] or "Customer requested human support")
    return {"ticket_id": tickets.create_ticket(body.session_id, body.email, summary, transcript)}


@app.get("/api/tickets")
def get_tickets():
    return tickets.list_tickets()
