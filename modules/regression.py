import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from database.connection import get_db

def calculate_log_linear_trend(ticker: str, period_years: float = 1.0):
    """
    Melakukan regresi log-linear terhadap harga penutupan historis aset.
    Model: ln(Price_t) = alpha + beta * t
    Return Tahunan = exp(beta * 252) - 1
    R^2: Koefisien Determinasi
    Arah Tren: Naik (slope > 0.0002), Turun (slope < -0.0002), Mendatar
    """
    conn = get_db()
    # Hitung jumlah hari kalender kasar dari periode tahun
    days_back = int(period_years * 365)
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    query = """
        SELECT date, close_price 
        FROM historical_prices 
        WHERE ticker = ? AND date >= ? 
        ORDER BY date ASC
    """
    df = pd.read_sql_query(query, conn, params=(ticker, cutoff_date))
    conn.close()

    if len(df) < 20: # Minimal 20 hari perdagangan
        # Fallback jika data tidak mencukupi untuk periode requested
        conn = get_db()
        df = pd.read_sql_query(
            "SELECT date, close_price FROM historical_prices WHERE ticker = ? ORDER BY date ASC",
            conn, params=(ticker,)
        )
        conn.close()
        if len(df) < 10:
            return {
                "ticker": ticker,
                "success": False,
                "message": f"Data historis untuk {ticker} belum mencukupi (minimal 10 hari)."
            }

    # t = 0, 1, 2, ..., N-1
    t = np.arange(len(df)).reshape(-1, 1)
    # Logaritma natural harga
    log_prices = np.log(df['close_price'].values)

    model = LinearRegression()
    model.fit(t, log_prices)
    
    slope = float(model.coef_[0])
    intercept = float(model.intercept_)
    r_squared = float(model.score(t, log_prices))

    # Konversi kemiringan harian ke return tahunan (252 hari perdagangan)
    annual_return = float(np.exp(slope * 252.0) - 1.0)

    # Tentukan arah tren
    if slope > 0.0002:
        trend_direction = "Naik (Bullish)"
    elif slope < -0.0002:
        trend_direction = "Turun (Bearish)"
    else:
        trend_direction = "Mendatar (Sideways)"

    warning = None
    if annual_return <= 0.0:
        warning = f"Perhatian: Estimasi return tren {annual_return*100:.2f}% bernilai negatif atau 0%. Sebaiknya pertimbangkan instrumen pasar uang atau risiko lebih terukur sebelum DCA."

    return {
        "ticker": ticker,
        "success": True,
        "data_points": len(df),
        "period_years": period_years,
        "slope_daily": slope,
        "annual_return": annual_return,
        "annual_return_pct": round(annual_return * 100, 2),
        "r_squared": round(r_squared, 4),
        "trend_direction": trend_direction,
        "warning": warning,
        "disclaimer": "Catatan: Tren masa lalu bukan jaminan imbal hasil di masa depan."
    }

def project_inflation_rate(target_year_ahead: int = 1) -> dict:
    """
    Melakukan regresi linear data inflasi historis BI/BPS untuk proyeksi inflasi dinamis.
    """
    conn = get_db()
    df = pd.read_sql_query("SELECT year, inflation_rate FROM inflation_history ORDER BY year ASC", conn)
    conn.close()

    if df.empty or len(df) < 3:
        # Default fallback inflasi BI target jika dataset belum terisi
        return {"projected_inflation": 3.5, "r_squared": 0.0, "status": "default_fallback"}

    X = df[['year']].values
    y = df['inflation_rate'].values

    model = LinearRegression()
    model.fit(X, y)

    last_year = int(df['year'].max())
    future_year = last_year + target_year_ahead
    pred_inflation = float(model.predict([[future_year]])[0])
    
    # Batasan realistis inflasi Indonesia (1.5% - 8.0%)
    clamped_inflation = max(1.5, min(8.0, pred_inflation))
    r_squared = float(model.score(X, y))

    return {
        "future_year": future_year,
        "projected_inflation": round(clamped_inflation, 2),
        "raw_prediction": round(pred_inflation, 2),
        "r_squared": round(r_squared, 4),
        "historical_avg": round(float(np.mean(y)), 2),
        "status": "calculated"
    }
