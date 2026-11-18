from modules.sentiment import get_overall_market_sentiment
from modules.clustering import get_assets_by_profile

RISK_QUESTIONS = [
    {
        "id": "q1",
        "question": "Apa tujuan utama investasi Anda?",
        "options": [
            {"score": 1, "text": "Menjaga nilai modal agar aman dari penurunan."},
            {"score": 2, "text": "Mendapatkan arus kas/penghasilan pasif yang teratur dan stabil."},
            {"score": 3, "text": "Pertumbuhan modal jangka menengah dengan fluktuasi wajar."},
            {"score": 4, "text": "Maksimalisasi keuntungan jangka panjang dan siap fluktuasi besar."}
        ]
    },
    {
        "id": "q2",
        "question": "Berapa lama horizon (jangka waktu) rencana investasi Anda?",
        "options": [
            {"score": 1, "text": "Sangat pendek (kurang dari 1 tahun)."},
            {"score": 2, "text": "Jangka pendek (1 hingga 3 tahun)."},
            {"score": 3, "text": "Jangka menengah (3 hingga 5 tahun)."},
            {"score": 4, "text": "Jangka panjang (lebih dari 5 tahun)."}
        ]
    },
    {
        "id": "q3",
        "question": "Bagaimana reaksi Anda jika nilai portofolio Anda turun 15% - 20% dalam sebulan?",
        "options": [
            {"score": 1, "text": "Sangat cemas dan langsung menjual seluruh aset untuk amankan modal."},
            {"score": 2, "text": "Khawatir dan menjual sebagian aset untuk membatasi kerugian."},
            {"score": 3, "text": "Tetap tenang, menahan portofolio, dan memantau pemulihan pasar."},
            {"score": 4, "text": "Melihatnya sebagai diskon dan menambah pembelian (Buy on Weakness)."}
        ]
    },
    {
        "id": "q4",
        "question": "Bagaimana pemahaman dan pengalaman investasi Anda?",
        "options": [
            {"score": 1, "text": "Pemula, belum pernah berinvestasi selain tabungan biasa."},
            {"score": 2, "text": "Memahami dasar deposito dan reksa dana pasar uang."},
            {"score": 3, "text": "Paham reksa dana saham/campuran, obligasi, dan saham bluechip."},
            {"score": 4, "text": "Sangat berpengalaman dalam analisis saham, ETF, kripto, atau derivatif."}
        ]
    },
    {
        "id": "q5",
        "question": "Berapa kecukupan dana darurat yang Anda miliki saat ini?",
        "options": [
            {"score": 1, "text": "Belum memiliki dana darurat."},
            {"score": 2, "text": "Cukup untuk 1 hingga 2 bulan pengeluaran."},
            {"score": 3, "text": "Cukup untuk 3 hingga 6 bulan pengeluaran."},
            {"score": 4, "text": "Sangat aman, lebih dari 6 bulan pengeluaran."}
        ]
    },
    {
        "id": "q6",
        "question": "Bagaimana stabilitas dan kepastian sumber pendapatan bulanan Anda?",
        "options": [
            {"score": 1, "text": "Sangat tidak menentu dan berfluktuasi tinggi."},
            {"score": 2, "text": "Fluktuatif namun memiliki batas pendapatan minimum."},
            {"score": 3, "text": "Relatif stabil (misal: pekerja tetap dengan gaji bulanan)."},
            {"score": 4, "text": "Sangat stabil dan memiliki beberapa sumber pendapatan."}
        ]
    }
]

def evaluate_risk_profile(answers: dict[str, int]) -> dict:
    """
    answers: dict berupa {'q1': score, 'q2': score, ..., 'q6': score} dengan nilai 1-4.
    """
    total_score = sum(answers.get(f"q{i}", 1) for i in range(1, 7))
    
    # 1. Base classification
    if total_score <= 12:
        profile = "Konservatif"
        description = "Anda mengutamakan keamanan modal pokok dengan risiko fluktuasi minimal."
    elif total_score <= 18:
        profile = "Moderat"
        description = "Anda siap menerima fluktuasi nilai pasar dalam batas wajar demi pertumbuhan aset menengah."
    else:
        profile = "Agresif"
        description = "Anda fokus pada imbal hasil tinggi jangka panjang dan siap menghadapi volatilitas signifikan."

    overrides = []
    # 2. Rule Overrides
    # Override Dana Darurat (Q5 < 3)
    q5_score = answers.get("q5", 1)
    if q5_score <= 2 and profile == "Agresif":
        profile = "Moderat"
        overrides.append(
            "Penyesuaian Dana Darurat: Karena dana darurat Anda belum mencapai 3-6 bulan pengeluaran, profil disesuaikan maksimal Moderat demi keamanan finansial."
        )
    elif q5_score == 1 and profile != "Konservatif":
        profile = "Konservatif"
        overrides.append(
            "Prioritas Utama: Anda belum memiliki dana darurat. Disarankan fokus mengumpulkan dana darurat di instrumen likuid (Pasar Uang) sebelum masuk ke aset berisiko."
        )

    # Override Horizon Waktu (Q2 == 1: < 1 tahun)
    q2_score = answers.get("q2", 1)
    if q2_score == 1 and profile != "Konservatif":
        profile = "Konservatif"
        overrides.append(
            "Penyesuaian Horizon Waktu: Rencana investasi kurang dari 1 tahun sangat berisiko jika ditempatkan di saham/kripto, sehingga dialokasikan ke instrumen Konservatif."
        )

    # 3. Market Sentiment Integration
    market_sentiment = get_overall_market_sentiment()
    sentiment_warning = None
    if market_sentiment == "NEGATIF":
        sentiment_warning = "Sentimen pasar saat ini sedang negatif/volatil. Disarankan menerapkan strategi akumulasi bertahap (Dollar Cost Averaging / DCA) untuk meminimalkan risiko waktu pasar."

    # 4. Rekomendasi Aset Terklaster
    recommended_assets = get_assets_by_profile(profile)

    return {
        "total_score": total_score,
        "profile": profile,
        "description": description,
        "overrides": overrides,
        "sentiment_warning": sentiment_warning,
        "recommended_assets": recommended_assets[:5]
    }
