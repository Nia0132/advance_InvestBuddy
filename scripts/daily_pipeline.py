import sys
import gc
import logging
from pathlib import Path

# Tambahkan direktori root proyek ke sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import init_db, set_system_metadata
from modules.crawler import crawl_yahoo_finance, crawl_google_news_rss
from modules.sentiment import run_batch_sentiment_analysis
from modules.clustering import run_asset_clustering, evaluate_user_scoring_silhouette
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DailyBatchPipeline")

def run_pipeline():
    logger.info("=== MEMULAI DAILY BATCH ML PIPELINE INVESTBUDDY ===")
    start_time = datetime.now()

    # 1. Inisialisasi Database
    logger.info("Tahap 1: Inisialisasi Database & Skema SQLite...")
    init_db()

    # 2. Crawling Yahoo Finance
    logger.info("Tahap 2: Crawling Harga Historis Aset (Yahoo Finance)...")
    try:
        crawl_yahoo_finance(period="2y")
    except Exception as e:
        logger.error(f"Peringatan saat crawling Yahoo Finance: {e}")

    # 3. Crawling Berita Google News RSS
    logger.info("Tahap 3: Crawling Berita Pasar Finansial (Google News RSS)...")
    try:
        crawl_google_news_rss()
    except Exception as e:
        logger.error(f"Peringatan saat crawling Google News RSS: {e}")

    # 4. Analisis Sentimen Batch
    logger.info("Tahap 4: Menjalankan Analisis Sentimen Berita Batch...")
    run_batch_sentiment_analysis()

    # 5. K-Means Asset Clustering
    logger.info("Tahap 5: Menjalankan K-Means Clustering Aset (k=3)...")
    run_asset_clustering()

    # 6. Evaluasi Silhouette Score Pengelompokan Pengguna Q1-Q6
    logger.info("Tahap 6: Evaluasi Silhouette Score Kuesioner Pengguna...")
    sil_eval = evaluate_user_scoring_silhouette()
    logger.info(f"Evaluasi Kuesioner: {sil_eval}")

    # 7. Update Metadata Sistem
    end_time = datetime.now()
    duration_sec = (end_time - start_time).total_seconds()
    status_msg = f"Selesai dalam {duration_sec:.1f} detik pada {end_time.strftime('%Y-%m-%d %H:%M:%S WIB')}"
    set_system_metadata("batch_pipeline_status", status_msg)

    # 8. Manajemen Memori: Garbage Collection untuk RAM 8GB
    logger.info("Tahap 8: Membersihkan memori RAM (gc.collect)...")
    gc.collect()

    logger.info(f"=== PIPELINE SELESAI SUKSES! ({status_msg}) ===")

if __name__ == "__main__":
    run_pipeline()
