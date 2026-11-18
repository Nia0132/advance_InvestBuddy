-- Database Schema untuk InvestBot (InvestBuddy)
-- Optimized for SQLite and concurrent reads

CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historical_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    close_price REAL NOT NULL,
    log_return REAL,
    volume REAL,
    UNIQUE(ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_hist_ticker_date ON historical_prices(ticker, date);

CREATE TABLE IF NOT EXISTS sentiment_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    published_date TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    source TEXT,
    sentiment_label TEXT NOT NULL, -- POSITIF, NETRAL, NEGATIF
    sentiment_score REAL NOT NULL,  -- Nilai kontinum -1.0 sampai 1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sentiment_ticker ON sentiment_logs(ticker, published_date);

CREATE TABLE IF NOT EXISTS asset_clusters (
    ticker TEXT PRIMARY KEY,
    asset_name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    annual_return REAL NOT NULL,
    annual_volatility REAL NOT NULL,
    r_squared REAL,
    trend_direction TEXT, -- Naik, Turun, Mendatar
    cluster_id INTEGER NOT NULL,
    cluster_label TEXT NOT NULL, -- Konservatif, Moderat, Agresif
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_context (
    session_id TEXT PRIMARY KEY,
    current_intent TEXT,
    state_data TEXT, -- JSON string menyimpan step kuesioner/kalkulator
    last_ticker TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inflation_history (
    year INTEGER PRIMARY KEY,
    inflation_rate REAL NOT NULL,
    source TEXT
);
