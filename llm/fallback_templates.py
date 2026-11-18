from database.connection import get_system_metadata

def format_currency(val: float) -> str:
    return f"Rp {val:,.0f}".replace(",", ".")

FALLBACK_INTENT_TEMPLATES = {
    "greeting": (
        "Halo! Selamat datang di **InvestBot** (Aplikasi Web InvestBuddy) 📈\n\n"
        "Saya adalah asisten edukasi literasi keuangan dan simulasi investasi berbasis data Anda. "
        "Saya dapat membantu Anda mengecek tren harga historis, analisis sentimen berita, pengelompokan aset (K-Means), "
        "kuesioner profil risiko, serta simulasi kalkulator DCA & dana pensiun.\n\n"
        "Apa yang ingin Anda eksplorasi hari ini? Anda bisa ketik misal: **'Mulai profil risiko'**, **'Sentimen BBCA'**, atau **'Kalkulator DCA'**."
    ),
    "bot_identity": (
        "Saya adalah **InvestBot**, modul kecerdasan buatan dari aplikasi web **InvestBuddy**.\n\n"
        "Tujuan saya adalah mendampingi mahasiswa dan pekerja muda dalam mempelajari literasi finansial "
        "menggunakan data nyata pasar modal Indonesia secara deterministik dan terukur.\n\n"
        "*Disclaimer: Seluruh informasi dan simulasi adalah untuk edukasi, bukan nasihat keuangan resmi berlisensi.*"
    ),
    "help": (
        "Berikut beberapa hal yang bisa Anda tanyakan kepada saya:\n\n"
        "1. 📊 **Profil Risiko & Rekomendasi:** Ketik *'Mulai tes profil risiko'* atau *'Aset apa untuk profil Moderat?'*\n"
        "2. 📈 **Analisis Tren Regresi:** Ketik *'Tren IHSG bagaimana?'* atau *'Tren BBCA 3 tahun'*\n"
        "3. 📰 **Sentimen Berita Pasar:** Ketik *'Sentimen BBCA?'* atau *'Berita apa saja?'*\n"
        "4. 🧮 **Kalkulator Investasi:** Ketik *'Kalkulator DCA'* atau *'Kalkulator dana pensiun'*\n"
        "5. 🏷️ **Klaster Aset (K-Means):** Ketik *'BBCA masuk klaster apa?'* atau *'Apa itu clustering?'*\n"
        "6. 📚 **Edukasi & Sumber Data:** Ketik *'Apa itu regresi linear?'*, *'Apa itu R²?'*, atau *'Data dari mana?'*"
    ),
    "faq_data_source": (
        "Data pada InvestBuddy diperoleh dari sumber legal dan terpercaya:\n\n"
        "1. **Yahoo Finance (`yfinance`):** Harga historis harian saham LQ45, ETF, Indeks IHSG, dan aset kripto.\n"
        "2. **Google News RSS (`feedparser`):** Ringkasan berita pasar modal terkini per emiten.\n"
        "3. **Bank Indonesia (BI) & BPS:** Dataset inflasi tahunan historis Indonesia (10–15 tahun terakhir).\n\n"
        "Pembaruan data dilakukan secara batch harian setiap pukul 17.00 WIB pasca penutupan bursa IDX."
    ),
    "data_last_update": (
        "Pembaruan data pasar terakhir dicatat pada:\n"
        f"📅 **{get_system_metadata('data_last_update') or 'Hari ini, 17:00 WIB'}**\n\n"
        "Sistem kami menyinkronkan data harga dan berita secara otomatis pasca penutupan bursa."
    ),
    "explain_regression": (
        "**Apa itu Regresi Log-Linear dalam Investasi?**\n\n"
        "Regresi log-linear memodelkan pergerakan harga historis terhadap waktu dengan persamaan: `ln(Harga) = α + β × t`.\n\n"
        "• **Slope (β):** Menunjukkan laju pertumbuhan rata-rata harian yang dikonversi ke return tahunan berbasis 252 hari bursa (`exp(β × 252) - 1`).\n"
        "• **Kelebihan:** Mengurangi asumsi subjektif dan memberikan estimasi pertumbuhan historis berbasis data nyata.\n"
        "• **Batas Penggunaan:** Regresi linear tidak menangkap fluktuasi jangka pendek ekstrem. Oleh karena itu selalu disajikan bersama nilai R²."
    ),
    "explain_r2": (
        "**Apa itu Koefisien Determinasi (R²)?**\n\n"
        "R² (skala 0 hingga 1.0) mengukur seberapa baik garis tren regresi menggambarkan pergerakan harga sesungguhnya:\n\n"
        "• **R² > 0.70:** Tren harga historis sangat konsisten dan stabil mengikuti arah tren.\n"
        "• **R² 0.40 - 0.70:** Tren cukup konsisten dengan fluktuasi pasar wajar.\n"
        "• **R² < 0.40:** Harga memiliki volatilitas atau sideways tinggi, sehingga garis tren kurang representatif.\n\n"
        "*Catatan: R² tinggi pun tetap bukan jaminan keuntungan masa depan.*"
    ),
    "explain_sentiment": (
        "**Apa itu Analisis Sentimen Finansial?**\n\n"
        "Analisis sentimen mengevaluasi nada emosi dari judul dan ringkasan berita pasar modal menggunakan kamus istilah finansial "
        "(seperti laba, dividen, ARA, anjlok, rugi bersih, ARB).\n\n"
        "Hasil dikelompokkan ke dalam persentase **Positif**, **Netral**, dan **Negatif** selama 7 hari terakhir. "
        "Informasi ini membantu investor memahami psikologi pasar terkini sebelum mengambil keputusan."
    ),
    "explain_cluster": (
        "**Apa itu K-Means Clustering pada InvestBuddy?**\n\n"
        "Clustering adalah metode *unsupervised machine learning* yang mengelompokkan 25–30 aset investasi ke dalam 3 kelompok "
        "berdasarkan fitur **Return Tahunan** dan **Volatilitas Tahunan** (setelah distandarisasi):\n\n"
        "1. **Klaster Konservatif:** Volatilitas terendah (Pasar Uang, SBN/ORI).\n"
        "2. **Klaster Moderat:** Volatilitas dan return seimbang (Saham Bluechip defensif, ETF).\n"
        "3. **Klaster Agresif:** Volatilitas dan potensi return tertinggi (Kripto, saham komoditas/pertumbuhan)."
    ),
    "explain_volatility": (
        "**Apa itu Volatilitas?**\n\n"
        "Volatilitas mengukur seberapa liar fluktuasi naik-turun harga suatu aset dalam periode tertentu. "
        "Dihitung dari deviasi standar return harian yang disetahunkan (`std × √252`).\n\n"
        "• **Volatilitas Rendah (< 5%):** Harga stabil, risiko penurunan drastis kecil (contoh: Deposito, SBN).\n"
        "• **Volatilitas Tinggi (> 25%):** Harga sering melonjak atau anjlok dalam waktu singkat (contoh: Kripto, saham cyclical)."
    ),
    "faq_ojk": (
        "**Otoritas Jasa Keuangan (OJK)** adalah lembaga independen yang mengatur, mengawasi, dan melindungi konsumen industri jasa keuangan Indonesia.\n\n"
        "Selalu pastikan platform investasi, manajer investasi, dan sekuritas yang Anda gunakan telah memiliki izin resmi dari OJK untuk menghindari investasi bodong."
    ),
    "faq_sbn": (
        "**Surat Berharga Negara (SBN / ORI / Sukuk):**\n\n"
        "Obligasi yang diterbitkan oleh Pemerintah Republik Indonesia untuk membiayai APBN. "
        "Investasi ini dijamin 100% oleh undang-undang (bebas risiko gagal bayar), memberikan kupon bulanan tetap, "
        "dan sangat cocok untuk profil risiko Konservatif."
    ),
    "faq_reksadana": (
        "**Reksa Dana** adalah wadah penghimpun dana masyarakat pemodal untuk diinvestasikan ke dalam portofolio efek oleh Manajer Investasi (MI) profesional.\n\n"
        "Jenis-jenis utamanya:\n"
        "1. **Pasar Uang:** Risiko paling rendah, imbal hasil di atas tabungan bank biasa.\n"
        "2. **Pendapatan Tetap:** Mayoritas obligasi/SBN, imbal hasil terukur.\n"
        "3. **Campuran:** Kombinasi obligasi dan saham.\n"
        "4. **Saham:** Potensi pertumbuhan tinggi dengan risiko volatilitas pasar saham."
    ),
    "faq_diversification": (
        "**Prinsip Diversifikasi (*Don't put all your eggs in one basket*):**\n\n"
        "Menyebarkan investasi ke berbagai kelas aset (misal: membagi dana ke Pasar Uang, Obligasi, dan Saham LQ45). "
        "Tujuannya adalah mengurangi risiko total kerugian: jika salah satu sektor turun, aset lain yang stabil dapat menopang nilai portofolio Anda."
    )
}

def format_trend_response(data: dict) -> str:
    if not data.get("success"):
        return f"⚠️ {data.get('message', 'Gagal menghitung tren aset.')}"

    ticker = data['ticker']
    ret_pct = data['annual_return_pct']
    r2 = data['r_squared']
    direction = data['trend_direction']
    warning = f"\n⚠️ {data['warning']}" if data.get("warning") else ""

    return (
        f"📊 **Hasil Analisis Tren Regresi Log-Linear ({ticker})**\n\n"
        f"• **Arah Tren:** {direction}\n"
        f"• **Estimasi Return Tahunan:** **{ret_pct:+.2f}% per tahun**\n"
        f"• **Koefisien Determinasi (R²):** **{r2}** (Kecocokan Model: {'Tinggi' if r2 >= 0.7 else 'Sedang' if r2 >= 0.4 else 'Rendah'})\n"
        f"• **Titik Data Historis:** {data['data_points']} hari perdagangan ({data['period_years']} tahun){warning}\n\n"
        f"*{data.get('disclaimer')}*\n\n"
        f"💡 Ingin menggunakan estimasi return **{ret_pct:+.2f}%** ini untuk simulasi menabung rutin? "
        f"Ketik: **'Hitung DCA pakai hasil itu'**."
    )

def format_sentiment_response(data: dict) -> str:
    ticker = data['ticker']
    return (
        f"📰 **Sentimen Berita Pasar ({ticker} - 7 Hari Terakhir)**\n\n"
        f"• 🟢 **Positif:** {data['positive_pct']}%\n"
        f"• ⚪ **Netral:** {data['neutral_pct']}%\n"
        f"• 🔴 **Negatif:** {data['negative_pct']}%\n"
        f"• **Kesimpulan:** **{data['dominant_sentiment']}**\n\n"
        f"Ketik **'Berita apa saja?'** untuk membaca 3 judul berita teratas, "
        f"atau ketik **'Tren harganya?'** untuk melihat proyeksi tren regresi historisnya."
    )

def format_sentiment_news_response(data: dict) -> str:
    ticker = data['ticker']
    news_items = data.get("recent_news", [])
    if not news_items:
        return f"Belum ada berita spesifik terbaru untuk {ticker} dalam 7 hari terakhir."

    news_text = "\n".join([f"{i+1}. **{n['title']}** *(Sumber: {n['source']})*" for i, n in enumerate(news_items)])
    return (
        f"📰 **3 Berita Finansial Terbaru ({ticker}):**\n\n"
        f"{news_text}\n\n"
        f"Sentimen dominan: **{data.get('dominant_sentiment', 'Netral')}**."
    )

def format_cluster_single_response(data: dict) -> str:
    if not data.get("found"):
        return data.get("message")

    return (
        f"🏷️ **Informasi Klaster Aset: {data['ticker']}**\n\n"
        f"• **Nama Aset:** {data['asset_name']} ({data['asset_type']})\n"
        f"• **Klaster Risiko:** **{data['cluster_label']}**\n"
        f"• **Return Tahunan Rata-Rata:** {data['annual_return_pct']:+.2f}%\n"
        f"• **Volatilitas Tahunan:** {data['annual_volatility_pct']:.2f}%\n"
        f"• **Arah Tren:** {data['trend_direction']} (R² = {data['r_squared']})\n\n"
        f"Aset ini sangat cocok untuk investor dengan profil risiko **{data['cluster_label']}**."
    )

def format_profile_recommendation_response(profile: str, assets: list[dict]) -> str:
    if not assets:
        return f"Belum ada daftar aset terdaftar untuk profil {profile}."

    items = []
    for a in assets:
        ret = f"{a['annual_return']*100:+.1f}%"
        vol = f"{a['annual_volatility']*100:.1f}%"
        items.append(f"• **{a['ticker']}** - {a['asset_name']} ({a['asset_type']}) | Return: {ret}, Vol: {vol}")

    return (
        f"🎯 **Rekomendasi Klaster Aset untuk Profil {profile}:**\n\n" +
        "\n".join(items) +
        f"\n\nIngin melihat analisis tren atau sentimen salah satu aset di atas? Ketik misal: **'Tren {assets[0]['ticker'].split('.')[0]}'**."
    )

def format_risk_result_response(data: dict) -> str:
    profile = data['profile']
    score = data['total_score']
    desc = data['description']

    overrides_text = ""
    if data.get("overrides"):
        overrides_text = "\n\n⚠️ **Catatan Penyesuaian Aturan:**\n" + "\n".join([f"• {ov}" for ov in data["overrides"]])

    sentiment_text = ""
    if data.get("sentiment_warning"):
        sentiment_text = f"\n\n📢 **Peringatan Pasar Terkini:**\n{data['sentiment_warning']}"

    assets_text = ""
    if data.get("recommended_assets"):
        assets_text = "\n\n📋 **Pilihan Klaster Aset yang Sesuai:**\n" + "\n".join([
            f"• **{a['ticker']}** ({a['asset_name']}) - Volatilitas: {a['annual_volatility']*100:.1f}%"
            for a in data["recommended_assets"]
        ])

    return (
        f"🎉 **Hasil Evaluasi Profil Risiko Anda**\n\n"
        f"• **Total Skor Kuesioner:** {score} / 24\n"
        f"• **Kategori Profil:** **{profile}**\n"
        f"• **Karakteristik:** {desc}"
        f"{overrides_text}"
        f"{sentiment_text}"
        f"{assets_text}\n\n"
        f"Langkah selanjutnya: Anda dapat mencoba simulasi pertumbuhan aset menggunakan **'Kalkulator DCA'** "
        f"atau merencanakan masa depan dengan **'Kalkulator Dana Pensiun'**."
    )

def format_dca_response(data: dict) -> str:
    if not data.get("success"):
        return f"⚠️ {data.get('message')}"

    p = format_currency(data['monthly_amount'])
    tot_pokok = format_currency(data['total_principal'])
    tot_fv = format_currency(data['future_value'])
    tot_cuan = format_currency(data['interest_earned'])
    ret_pct = data['annual_return_pct']
    cuan_pct = data['profit_percentage']
    dur = data['duration_years']

    return (
        f"🧮 **Hasil Simulasi DCA (Dollar Cost Averaging)**\n\n"
        f"• **Investasi Rutin Bulanan:** {p}\n"
        f"• **Jangka Waktu:** {dur} tahun ({data['total_months']} bulan)\n"
        f"• **Estimasi Imbal Hasil:** {ret_pct}% per tahun\n\n"
        f"─────────────────────────────\n"
        f"💰 **Total Modal Disetor:** **{tot_pokok}**\n"
        f"📈 **Total Akumulasi Imbal Hasil:** **{tot_cuan}** (+{cuan_pct}%)\n"
        f"🏆 **Estimasi Nilai Akhir Portofolio:** **{tot_fv}**\n"
        f"─────────────────────────────\n\n"
        f"*{data.get('note')} Nilai di atas merupakan simulasi matematis deterministik.*"
    )

def format_pension_response(data: dict, inf_meta: dict = None) -> str:
    if not data.get("success"):
        return f"⚠️ {data.get('message')}"

    now_exp = format_currency(data['monthly_expense_now'])
    ret_exp = format_currency(data['monthly_expense_retirement'])
    tot_need = format_currency(data['total_pension_fund_needed'])
    mon_save = format_currency(data['monthly_saving_required'])

    warning_text = ""
    if data.get("real_return_warning"):
        warning_text = f"\n\n⚠️ {data['real_return_warning']}"

    inf_info = ""
    if inf_meta and inf_meta.get("status") == "calculated":
        inf_info = f" *(Proyeksi Regresi Inflasi BI/BPS: {inf_meta['projected_inflation']}%)*"

    return (
        f"🏖️ **Hasil Simulasi Perencanaan Dana Pensiun**\n\n"
        f"• **Usia Sekarang:** {data['current_age']} tahun | **Rencana Pensiun:** {data['retirement_age']} tahun\n"
        f"• **Masa Menabung:** {data['years_to_save']} tahun | **Masa Pensiun:** {data['years_in_retirement']} tahun\n"
        f"• **Pengeluaran Bulanan Saat Ini:** {now_exp}\n"
        f"• **Asumsi Laju Inflasi:** {data['annual_inflation_pct']}% per tahun{inf_info}\n"
        f"• **Asumsi Return Investasi:** {data['annual_return_pct']}% per tahun\n\n"
        f"─────────────────────────────\n"
        f"🛒 **Estimasi Pengeluaran Bulanan di Usia {data['retirement_age']}:** **{ret_exp}**\n"
        f"🎯 **Total Dana Pensiun yang Harus Terkumpul:** **{tot_need}**\n"
        f"💵 **Tabungan Bulanan yang Perlu Disisihkan Mulai Sekarang:** **{mon_save} / bulan**\n"
        f"─────────────────────────────"
        f"{warning_text}\n\n"
        f"💡 Tips: Semakin dini Anda memulai, efek bunga majemuk (*compound interest*) akan meringankan nominal tabungan bulanan yang dibutuhkan."
    )
