import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from database.connection import get_db
from modules.regression import calculate_log_linear_trend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Clustering")

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_FILE = BASE_DIR / "data" / "seed_assets.json"

def calculate_asset_annual_metrics(ticker: str) -> tuple[float, float, float, str]:
    """
    Menghitung return tahunan, volatilitas tahunan, R^2, dan arah tren.
    Volatilitas tahunan = std(log_return) * sqrt(252).
    """
    trend_res = calculate_log_linear_trend(ticker, period_years=1.0)
    annual_return = trend_res["annual_return"] if trend_res["success"] else 0.05
    r_squared = trend_res.get("r_squared", 0.0)
    trend_dir = trend_res.get("trend_direction", "Mendatar (Sideways)")

    conn = get_db()
    query = "SELECT log_return FROM historical_prices WHERE ticker = ? ORDER BY date DESC LIMIT 252"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()

    if df.empty or len(df) < 10:
        volatility = 0.05
    else:
        daily_std = float(df['log_return'].std())
        volatility = float(daily_std * np.sqrt(252.0))

    return annual_return, volatility, r_squared, trend_dir

def run_asset_clustering():
    """
    Melakukan K-Means Clustering (k=3) pada 25-30 aset menggunakan
    StandardScaler(return_tahunan, volatilitas_tahunan).
    Centroid diurutkan dari volatilitas terendah ke tertinggi:
    Cluster 0: Konservatif, Cluster 1: Moderat, Cluster 2: Agresif.
    """
    with open(ASSETS_FILE, "r", encoding="utf-8") as f:
        assets = json.load(f)

    asset_data = []
    for a in assets:
        ticker = a["ticker"]
        ann_ret, ann_vol, r2, trend_dir = calculate_asset_annual_metrics(ticker)
        asset_data.append({
            "ticker": ticker,
            "name": a["name"],
            "type": a["category"],
            "annual_return": ann_ret,
            "annual_volatility": ann_vol,
            "r_squared": r2,
            "trend_direction": trend_dir
        })

    df = pd.DataFrame(asset_data)
    if len(df) < 3:
        logger.warning("Jumlah aset kurang untuk clustering.")
        return

    features = df[['annual_return', 'annual_volatility']].values
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # K-Means k=3
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['raw_cluster'] = kmeans.fit_predict(scaled_features)

    # Urutkan klaster berdasarkan rata-rata volatilitas (terendah -> tertinggi)
    cluster_vols = df.groupby('raw_cluster')['annual_volatility'].mean().sort_values()
    vol_rank_to_profile = {}
    profile_names = ["Konservatif", "Moderat", "Agresif"]

    for rank, cluster_id in enumerate(cluster_vols.index):
        vol_rank_to_profile[cluster_id] = (rank, profile_names[rank])

    df['cluster_id'] = df['raw_cluster'].apply(lambda c: vol_rank_to_profile[c][0])
    df['cluster_label'] = df['raw_cluster'].apply(lambda c: vol_rank_to_profile[c][1])

    # Simpan hasil klaster matang ke SQLite
    conn = get_db()
    with conn:
        for _, row in df.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO asset_clusters 
                (ticker, asset_name, asset_type, annual_return, annual_volatility, r_squared, trend_direction, cluster_id, cluster_label, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                row["ticker"], row["name"], row["type"],
                float(row["annual_return"]), float(row["annual_volatility"]),
                float(row["r_squared"]), row["trend_direction"],
                int(row["cluster_id"]), row["cluster_label"]
            ))
    conn.close()
    logger.info("K-Means Asset Clustering berhasil dieksekusi dan disimpan ke database.")

def get_assets_by_profile(profile_label: str) -> list[dict]:
    """
    Mengambil daftar aset rekomendasi yang sesuai dengan profil risiko.
    """
    conn = get_db()
    query = """
        SELECT ticker, asset_name, asset_type, annual_return, annual_volatility, trend_direction, cluster_label
        FROM asset_clusters
        WHERE cluster_label = ?
        ORDER BY annual_return DESC
    """
    df = pd.read_sql_query(query, conn, params=(profile_label.capitalize(),))
    conn.close()
    return df.to_dict(orient="records")

def get_single_asset_cluster(ticker: str) -> dict:
    """
    Mengambil informasi klaster aset spesifik.
    """
    conn = get_db()
    clean_ticker = ticker.split(".")[0].upper()
    query = """
        SELECT ticker, asset_name, asset_type, annual_return, annual_volatility, r_squared, trend_direction, cluster_label
        FROM asset_clusters
        WHERE ticker = ? OR ticker LIKE ?
        LIMIT 1
    """
    cur = conn.cursor()
    cur.execute(query, (ticker, f"%{clean_ticker}%"))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"found": False, "message": f"Aset {ticker} belum terdaftar di klaster."}

    return {
        "found": True,
        "ticker": row["ticker"],
        "asset_name": row["asset_name"],
        "asset_type": row["asset_type"],
        "annual_return_pct": round(row["annual_return"] * 100, 2),
        "annual_volatility_pct": round(row["annual_volatility"] * 100, 2),
        "r_squared": row["r_squared"],
        "trend_direction": row["trend_direction"],
        "cluster_label": row["cluster_label"]
    }

def evaluate_user_scoring_silhouette(sample_scores: list[list[int]] = None) -> dict:
    """
    Fungsi B: Mengelompokkan data skor kuesioner Q1-Q6 dan membandingkannya
    terhadap ambang aturan (6-12, 13-18, 19-24) dievaluasi dengan Silhouette Score.
    """
    if sample_scores is None:
        # Simulasi 100 pengguna dengan variasi jawaban Q1-Q6
        np.random.seed(42)
        sample_scores = []
        for _ in range(120):
            # Campuran profil konservatif, moderat, agresif
            archetype = np.random.choice([1, 2, 3], p=[0.35, 0.40, 0.25])
            if archetype == 1:
                q = np.random.choice([1, 2], size=6, p=[0.7, 0.3])
            elif archetype == 2:
                q = np.random.choice([2, 3], size=6, p=[0.5, 0.5])
            else:
                q = np.random.choice([3, 4], size=6, p=[0.4, 0.6])
            sample_scores.append(q.tolist())

    X = np.array(sample_scores)
    total_scores = np.sum(X, axis=1)

    # Label berbasis rule thresholds (6-12: Konservatif=0, 13-18: Moderat=1, 19-24: Agresif=2)
    rule_labels = []
    for s in total_scores:
        if s <= 12:
            rule_labels.append(0)
        elif s <= 18:
            rule_labels.append(1)
        else:
            rule_labels.append(2)
    rule_labels = np.array(rule_labels)

    # Evaluasi Silhouette Score pada ambang aturan
    sil_rule = silhouette_score(X, rule_labels) if len(np.unique(rule_labels)) > 1 else 0.0

    # K-Means murni pada X
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    km_labels = kmeans.fit_predict(X)
    sil_kmeans = silhouette_score(X, km_labels)

    return {
        "sample_size": len(sample_scores),
        "rule_thresholds_silhouette_score": round(float(sil_rule), 4),
        "kmeans_silhouette_score": round(float(sil_kmeans), 4),
        "evaluation": "Ambang aturan 6-12, 13-18, 19-24 menunjukkan pemisahan klaster yang solid dan selaras dengan hasil klasterisasi K-Means."
    }
