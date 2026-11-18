import os
import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "investbuddy.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
INFLATION_CSV = BASE_DIR / "data" / "bi_bps_inflation.csv"
ASSETS_JSON = BASE_DIR / "data" / "seed_assets.json"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for concurrency
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db()
    with conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        
        # Inisialisasi metadata jika belum ada
        conn.execute(
            "INSERT OR IGNORE INTO system_metadata (key, value, updated_at) VALUES (?, ?, ?)",
            ("data_last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB"), datetime.now().isoformat())
        )
        conn.execute(
            "INSERT OR IGNORE INTO system_metadata (key, value, updated_at) VALUES (?, ?, ?)",
            ("data_sources", "Yahoo Finance (Harga Aset), Google News RSS (Berita Sentimen), Bank Indonesia & BPS (Inflasi Historis)", datetime.now().isoformat())
        )

        # Muat data inflasi historis
        if INFLATION_CSV.exists():
            with open(INFLATION_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    conn.execute(
                        "INSERT OR REPLACE INTO inflation_history (year, inflation_rate, source) VALUES (?, ?, ?)",
                        (int(row["year"]), float(row["inflation_rate"]), row.get("source", "BI/BPS"))
                    )

    conn.close()

def get_system_metadata(key: str) -> str:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM system_metadata WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else ""

def set_system_metadata(key: str, value: str):
    conn = get_db()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO system_metadata (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat())
        )
    conn.close()

def save_session_state(session_id: str, intent: str, state_data: dict, last_ticker: str = None):
    conn = get_db()
    with conn:
        conn.execute("""
            INSERT INTO session_context (session_id, current_intent, state_data, last_ticker, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                current_intent = excluded.current_intent,
                state_data = excluded.state_data,
                last_ticker = COALESCE(excluded.last_ticker, session_context.last_ticker),
                updated_at = CURRENT_TIMESTAMP
        """, (session_id, intent, json.dumps(state_data), last_ticker))
    conn.close()

def get_session_state(session_id: str) -> dict:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM session_context WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"current_intent": None, "state_data": {}, "last_ticker": None}
    return {
        "current_intent": row["current_intent"],
        "state_data": json.loads(row["state_data"]) if row["state_data"] else {},
        "last_ticker": row["last_ticker"]
    }

def clear_session_state(session_id: str):
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM session_context WHERE session_id = ?", (session_id,))
    conn.close()
