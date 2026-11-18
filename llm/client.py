import requests
import json
import logging
from llm.fallback_templates import (
    FALLBACK_INTENT_TEMPLATES,
    format_trend_response,
    format_sentiment_response,
    format_sentiment_news_response,
    format_cluster_single_response,
    format_profile_recommendation_response,
    format_risk_result_response,
    format_dca_response,
    format_pension_response
)

logger = logging.getLogger("LLMClient")
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:1.5b"  # atau qwen:1.7b

SYSTEM_PROMPT = """
Anda adalah InvestBot, asisten finansial edukatif dan cerdas dari aplikasi web InvestBuddy.
Tugas Anda:
1. Menjelaskan konsep investasi pasar modal Indonesia (IHSG, saham LQ45, SBN, Reksa Dana, inflasi, regresi linear, sentimen berita, clustering) dengan ramah, komunikatif, dan mudah dipahami oleh mahasiswa dan pekerja muda.
2. DILARANG KERAS mengubah atau mereka-reka (halusinasi) angka hasil perhitungan yang diberikan oleh sistem Python.
3. Selalu pertahankan batasan edukasi: jangan memberikan nasihat spekulatif beli/jual secara mutlak, ingatkan diversifikasi dan profil risiko.
4. Gunakan Bahasa Indonesia yang natural, lugas, dan santun.
"""

def call_ollama(prompt: str, model: str = DEFAULT_MODEL, timeout: float = 5.0) -> str | None:
    """
    Memanggil API lokal Ollama dengan timeout 5 detik.
    Jika Ollama offline atau timeout, mengembalikan None agar fallback template digunakan.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_ctx": 2048
        },
        "keep_alive": "2m"
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        if response.status_code == 200:
            res_json = response.json()
            return res_json.get("response", "").strip()
    except Exception as e:
        logger.debug(f"Ollama tidak tersedia / timeout: {e}. Menggunakan fallback template.")
    return None

def generate_grounded_response(intent: str, user_message: str, execution_result: dict = None) -> str:
    """
    Menghasilkan respons terpadu:
    1. Memeriksa apakah execution_result merupakan objek terstruktur (DCA, tren, sentimen, pensiun, dll.)
    2. Jika ada LLM, dapat digunakan untuk memperluas edukasi (explain_*).
    3. Jika LLM offline atau lambat, fallback 100% deterministik.
    """
    if execution_result:
        res_type = execution_result.get("type")
        if res_type == "trend_result":
            return format_trend_response(execution_result["data"])
        elif res_type == "sentiment_result":
            return format_sentiment_response(execution_result["data"])
        elif res_type == "sentiment_news_result":
            return format_sentiment_news_response(execution_result["data"])
        elif res_type == "cluster_single_result":
            return format_cluster_single_response(execution_result["data"])
        elif res_type == "profile_recommendation_result":
            return format_profile_recommendation_response(
                execution_result["profile"], execution_result["assets"]
            )
        elif res_type == "risk_result":
            return format_risk_result_response(execution_result["data"])
        elif res_type == "dca_result":
            return format_dca_response(execution_result["data"])
        elif res_type == "pension_result":
            return format_pension_response(execution_result["data"], execution_result.get("inflation_metadata"))
        elif res_type == "quick_reply":
            return execution_result.get("text", "")
        elif res_type == "text":
            return execution_result.get("text", "")

    # Untuk intent bertipe edukasi/penjelasan (explain_*)
    fallback = FALLBACK_INTENT_TEMPLATES.get(intent)

    if intent.startswith("explain_") or intent in ["faq_ojk", "faq_sbn", "faq_reksadana", "faq_diversification"]:
        prompt = (
            f"Pertanyaan pengguna: '{user_message}'\n\n"
            f"Fakta rujukan baku:\n{fallback}\n\n"
            f"Instruksi: Jelaskan kembali poin-poin di atas dengan gaya bahasa yang santun, menarik, dan mudah dipahami."
        )
        llm_resp = call_ollama(prompt)
        if llm_resp:
            return llm_resp

    return fallback or FALLBACK_INTENT_TEMPLATES.get("help")
