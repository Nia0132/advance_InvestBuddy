import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Pastikan root direktori ada di sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import init_db, get_system_metadata, clear_session_state
from nlu.classifier import get_intent
from nlu.state_machine import StateMachine
from llm.client import generate_grounded_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InvestBuddyApp")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inisialisasi database SQLite jika belum ada
    logger.info("Memulai InvestBuddy Web Server...")
    init_db()
    yield
    logger.info("Mematikan InvestBuddy Web Server...")

app = FastAPI(
    title="InvestBuddy Chatbot API",
    description="Asisten Edukasi & Simulasi Investasi Berbasis Data Pasar Indonesia",
    version="2.0.0",
    lifespan=lifespan
)

# Static & Templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    quick_replies: list[str] = []

@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message.strip()
    session_id = req.session_id

    # 1. Klasifikasi Intent dengan TF-IDF + LinearSVC (<5ms latency)
    predicted_intent, confidence = get_intent(user_msg)
    logger.info(f"Session: {session_id} | Input: '{user_msg}' | Intent: {predicted_intent} ({confidence:.2f})")

    # 2. Eksekusi State Machine (Multi-Turn State Tracking)
    sm = StateMachine(session_id)
    execution_result = sm.process_message(user_msg, predicted_intent)

    # 3. Grounded NLG / Template Assembly
    bot_reply = generate_grounded_response(
        intent=predicted_intent,
        user_message=user_msg,
        execution_result=execution_result
    )

    # 4. Generate kontekstual quick replies
    quick_replies = []
    res_type = execution_result.get("type") if execution_result else None

    if res_type == "trend_result":
        quick_replies = ["Hitung DCA pakai hasil itu", "Sentimen aset ini?", "Aset klaster apa ini?"]
    elif res_type == "sentiment_result":
        quick_replies = ["Berita apa saja?", "Tren harganya?", "Aset klaster apa ini?"]
    elif res_type == "risk_result":
        quick_replies = ["Kalkulator DCA", "Kalkulator dana pensiun", "Aset apa untuk profil saya?"]
    elif res_type == "quick_reply":
        quick_replies = ["1", "2", "3", "4"]
    elif predicted_intent == "greeting":
        quick_replies = ["Mulai tes profil risiko", "Tren IHSG bagaimana?", "Kalkulator DCA", "Data dari mana?"]

    return ChatResponse(
        response=bot_reply,
        intent=predicted_intent,
        confidence=confidence,
        quick_replies=quick_replies
    )

@app.get("/api/status")
async def get_status():
    last_update = get_system_metadata("data_last_update") or "Belum sinkron"
    pipeline_status = get_system_metadata("batch_pipeline_status") or "Standby"
    return {
        "status": "online",
        "last_update": last_update,
        "pipeline_status": pipeline_status,
        "environment": "FastAPI + Hybrid NLU/LLM"
    }

@app.post("/api/reset")
async def reset_session(session_id: str):
    clear_session_state(session_id)
    return {"status": "success", "message": f"Sesi {session_id} telah direset."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
