# 📈 InvestBuddy - Asisten Cerdas Investasi Berbasis Data Pasar Modal (InvestBot v2.0)

Aplikasi Web Chatbot Edukasi Finansial & Simulasi Investasi Berbasis Data Nyata (Bukan Nasihat Keuangan Resmi) yang dioptimalkan untuk perangkat laptop dengan spesifikasi **RAM 8GB DDR4** tanpa GPU diskret.

---

## 🏛️ 1. Arsitektur Sistem (Hybrid Deterministic + Grounded NLG)

```
[Crawling Harian 17.00 WIB]
Yahoo Finance (yfinance) + Google News RSS (feedparser) + Inflasi BI/BPS
                           │
                           ▼
                  [investbuddy.db] (SQLite WAL Mode)
                           │
                           ▼
[Batch ML Pipeline (daily_pipeline.py)]
• Regresi Log-Linear (Return Tahunan = exp(slope * 252) - 1, R², Arah Tren)
• Analisis Sentimen Terbobot Kata Kunci Pasar Modal
• K-Means Clustering Aset (k=3: Konservatif, Moderat, Agresif)
• Evaluasi Kuesioner Pengguna (Silhouette Score)
• Pembersihan Memori (gc.collect())
                           │
                           ▼
[Web Chat Real-Time (FastAPI + Web UI)]
User Input ──> NLU Engine (TF-IDF + LinearSVC, <5ms latency, <40MB RAM)
            ──> State Machine (Multi-Turn Context & Session Tracking)
            ──> Kalkulator Python 100% Deterministik (DCA, Pensiun, Risk Profile)
            ──> Grounded NLG (Qwen2.5-1.5B / Qwen3-1.7B via Ollama / Fallback Template)
            ──> Antarmuka Modern Web Chat (FastAPI + HTML5 + CSS3 + Marked.js)
```

---

## 🚀 2. Panduan Instalasi & Menjalankan Aplikasi

### A. Prasyarat Sistem
* Python 3.10+ (Direkomendasikan Python 3.12/3.14)
* RAM 8GB DDR4 (Aman berjalan bersamaan dengan OS & Browser)
* *(Opsional)* Ollama dengan model `qwen2.5:1.5b` jika ingin NLG LLM lokal aktif. Jika Ollama tidak diinstal, sistem otomatis berjalan 100% sempurna dengan **Deterministic Fallback Engine**.

### B. Lingkungan Virtual Environment (Virtualenv)
Virtual environment telah dibuat di folder `venv/` dan seluruh paket dependensi telah terinstal:

```powershell
# Aktivasi venv di Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Atau di Command Prompt:
.\venv\Scripts\activate.bat
```

### C. Menjalankan Daily Batch ML Pipeline (Crawling & Pelatihan Model)
Untuk memperbarui data pasar saham LQ45, berita sentimen RSS, inflasi, dan clustering aset:

```powershell
.\venv\Scripts\python.exe scripts/daily_pipeline.py
```
*Atau klik ganda `run_pipeline.bat` di Windows Explorer.*

### D. Menjalankan Web Server Chatbot (FastAPI)
Untuk menyalakan server chatbot interaktif:

```powershell
.\venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
*Atau klik ganda `run_app.bat` di Windows Explorer.*

Buka browser Anda dan akses:  
👉 **http://127.0.0.1:8000**

---

## 🧪 3. Menjalankan Pengujian Otomatis (Automated Tests)

Semua modul logika, NLU (<1 ms latency), regresi log-linear, integrasi tren ke DCA, penanganan `r=0%`, peringatan real return pensiun, dan kuesioner profil risiko Q1–Q6 telah diuji secara otomatis:

```powershell
.\venv\Scripts\python.exe tests/test_flow.py
```

---

## 📂 4. Struktur Direktori Proyek

```
Proyek Akhir/
├── venv/                       # Virtual Environment Python
├── requirements.txt            # Daftar pustaka & dependensi
├── app.py                      # Server FastAPI & API endpoints (/api/chat, /api/status, /api/reset)
├── run_app.bat                 # Shortcut satu klik menjalankan web server
├── run_pipeline.bat            # Shortcut satu klik menjalankan batch pipeline
├── investbuddy.db              # Database SQLite (WAL Mode, aman multi-read)
├── data/
│   ├── bi_bps_inflation.csv    # Dataset historis inflasi BI / BPS 2010–2024
│   └── seed_assets.json        # 25-30 aset target (LQ45, ETF, SBN/Pasar Uang, Kripto)
├── database/
│   ├── connection.py           # Helper koneksi & fungsi query SQLite
│   └── schema.sql              # Skema 6 tabel SQLite
├── modules/
│   ├── crawler.py              # Yahoo Finance batch download & Google News RSS parser
│   ├── regression.py           # Log-Linear Regression (kemiringan 252 hari, R², proyeksi inflasi)
│   ├── sentiment.py            # Analisis sentimen berita berbobot pasar modal (7 hari)
│   ├── clustering.py           # K-Means (k=3) aset & evaluasi Silhouette Score Q1-Q6
│   ├── calculator.py           # Kalkulator DCA & Dana Pensiun dengan pengamanan matematika
│   └── risk_profile.py         # Kuesioner Q1-Q6, aturan override dana darurat & horizon
├── nlu/
│   ├── intents.json            # Dataset 30+ intent percakapan finansial
│   ├── classifier.py           # Klasifikasi TF-IDF + LinearSVC (<5ms latency, <40MB RAM)
│   ├── extractor.py            # Ekstraksi entitas Regex (ticker, nominal rupiah, durasi, persentase)
│   └── state_machine.py        # Pelacak state percakapan multi-turn & retensi konteks
├── llm/
│   ├── client.py               # Klien Ollama Qwen dengan batas timeout 5 detik
│   └── fallback_templates.py   # Template deterministik lengkap jika LLM tidak aktif
├── web/
│   ├── templates/
│   │   └── index.html          # Antarmuka Web Dashboard Chatbot modern & responsif
│   └── static/
│       ├── css/style.css       # Desain antarmuka modern, dark theme, styling bubble chat
│       └── js/chat.js          # Logika frontend, Markdown parsing (marked.js), quick replies
├── scripts/
│   └── daily_pipeline.py       # Batch ML Pipeline harian pasca jam bursa tutup (17:00 WIB)
└── tests/
    └── test_flow.py            # Skrip pengujian otomatis 8 skenario utama
```

---

## 🛡️ 5. Pengamanan Teknis & Guardrails

1. **Anti-Halusinasi Angka:** Seluruh perhitungan bunga majemuk, regresi, dan kalkulator diselesaikan 100% oleh kode Python deterministik, bukan oleh LLM.
2. **Pengamanan `Return = 0%`:** Mencegah `ZeroDivisionError` pada rumus anuitas dengan percabangan `if r == 0: FV = P * n`.
3. **Peringatan Real Return Negatif:** Kalkulator dana pensiun otomatis menampilkan peringatan jika `asumsi return <= inflasi`.
4. **Override Profil Risiko:** Jika dana darurat < 3 bulan, profil otomatis diturunkan maksimal Moderat/Konservatif dengan edukasi prioritas dana darurat.
5. **Fallback Timeout 5 Detik:** Menjamin pengguna web tidak pernah mengalami error timeout atau antarmuka terhenti.
