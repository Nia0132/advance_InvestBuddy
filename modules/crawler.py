import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf
import feedparser

from database.connection import get_db, set_system_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Crawler")

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_FILE = BASE_DIR / "data" / "seed_assets.json"

def load_target_assets():
    with open(ASSETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def crawl_yahoo_finance(period: str = "2y"):
    """
    Mengambil data harga historis aset secara batch dari Yahoo Finance,
    menyelaraskan tanggal (date alignment), dan menghitung log-return.
    """
    assets = load_target_assets()
    yf_tickers = [a["ticker"] for a in assets if not a["ticker"].startswith("IDR_PU_") and not a["ticker"].startswith("SBN_")]
    
    logger.info(f"Mengunduh data batch dari Yahoo Finance untuk {len(yf_tickers)} ticker...")
    data = yf.download(yf_tickers, period=period, group_by='ticker', auto_adjust=True, threads=True)

    conn = get_db()
    total_inserted = 0

    with conn:
        for asset in assets:
            ticker = asset["ticker"]
            
            # Handler untuk aset nyata dari Yahoo Finance
            if ticker in yf_tickers:
                try:
                    df = data[ticker].dropna(subset=['Close']) if len(yf_tickers) > 1 else data.dropna(subset=['Close'])
                    if df.empty:
                        continue
                    
                    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
                    
                    for date_idx, row in df.iterrows():
                        date_str = date_idx.strftime("%Y-%m-%d")
                        close_price = float(row['Close'])
                        log_return = float(row['Log_Return']) if pd.notna(row['Log_Return']) else 0.0
                        volume = float(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0.0

                        conn.execute("""
                            INSERT OR REPLACE INTO historical_prices (ticker, date, close_price, log_return, volume)
                            VALUES (?, ?, ?, ?, ?)
                        """, (ticker, date_str, close_price, log_return, volume))
                        total_inserted += 1
                except Exception as e:
                    logger.warning(f"Gagal memproses data Yahoo Finance untuk {ticker}: {e}")

            # Handler untuk proxy Pasar Uang / SBN (Bunga stabil / volatilitas sangat rendah)
            elif ticker.startswith("IDR_PU_") or ticker.startswith("SBN_"):
                # Buat deret harga proxy berdasarkan imbal hasil tahunan rata-rata (5.5% - 6.5%)
                base_annual_return = 0.055 if "PU" in ticker else 0.065
                daily_return = base_annual_return / 252.0
                daily_std = 0.0002 if "PU" in ticker else 0.0010
                
                num_days = 504 # ~2 tahun bursa
                end_date = datetime.now()
                dates = [end_date - timedelta(days=i) for i in range(num_days*7//5)][:num_days]
                dates.reverse()

                price = 1000.0
                np.random.seed(abs(hash(ticker)) % 10000)
                simulated_returns = np.random.normal(daily_return, daily_std, num_days)

                for d, ret in zip(dates, simulated_returns):
                    price *= (1.0 + ret)
                    conn.execute("""
                        INSERT OR REPLACE INTO historical_prices (ticker, date, close_price, log_return, volume)
                        VALUES (?, ?, ?, ?, ?)
                    """, (ticker, d.strftime("%Y-%m-%d"), float(price), float(ret), 100000.0))
                    total_inserted += 1

    set_system_metadata("data_last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB"))
    logger.info(f"Selesai mengunduh harga historis. Total rekaman tersimpan: {total_inserted}")
    conn.close()

def crawl_google_news_rss():
    """
    Mengambil berita finansial legal & gratis via Google News RSS untuk tiap aset utama.
    """
    assets = load_target_assets()
    conn = get_db()
    total_news = 0

    with conn:
        for asset in assets:
            ticker = asset["ticker"]
            query_name = asset["name"].split()[0]
            # Format feed RSS Google News Bahasa Indonesia
            encoded_query = f"{ticker.split('.')[0]}+{query_name}+saham+investasi"
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"

            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:5]:  # Ambil hingga 5 berita teratas per ticker
                    title = entry.title
                    summary = getattr(entry, "summary", "")
                    pub_date = getattr(entry, "published", datetime.now().strftime("%Y-%m-%d"))
                    source = entry.source.title if hasattr(entry, "source") and hasattr(entry.source, "title") else "Google News"

                    # Dummy initial sentiment score to be updated by batch sentiment analysis
                    conn.execute("""
                        INSERT OR IGNORE INTO sentiment_logs (ticker, published_date, title, summary, source, sentiment_label, sentiment_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (ticker, pub_date, title, summary, source, "NETRAL", 0.0))
                    total_news += 1
            except Exception as e:
                logger.warning(f"Gagal mengambil RSS untuk {ticker}: {e}")

    logger.info(f"Selesai mengambil berita RSS. Total berita tersimpan: {total_news}")
    conn.close()

if __name__ == "__main__":
    crawl_yahoo_finance()
    crawl_google_news_rss()
