import re

KNOWN_TICKERS = {
    "BBCA": "BBCA.JK", "BBRI": "BBRI.JK", "BMRI": "BMRI.JK", "BBNI": "BBNI.JK",
    "ASII": "ASII.JK", "TLKM": "TLKM.JK", "ICBP": "ICBP.JK", "INDF": "INDF.JK",
    "UNVR": "UNVR.JK", "KLBF": "KLBF.JK", "ADRO": "ADRO.JK", "PTBA": "PTBA.JK",
    "ANTM": "ANTM.JK", "CPIN": "CPIN.JK", "PGAS": "PGAS.JK",
    "IHSG": "^JKSE", "^JKSE": "^JKSE", "EIDO": "EIDO", "BTC": "BTC-USD",
    "BITCOIN": "BTC-USD", "ETH": "ETH-USD", "ETHEREUM": "ETH-USD", "SOL": "SOL-USD"
}

def extract_ticker(text: str) -> str | None:
    """
    Mengekstrak ticker saham atau aset dari teks.
    """
    text_upper = text.upper()
    # 1. Cek kata kunci spesifik
    for key, val in KNOWN_TICKERS.items():
        if re.search(r'\b' + re.escape(key) + r'\b', text_upper):
            return val

    # 2. Cek pola ticker IDX standar (4 huruf kapital, e.g., BBCA, GOTO)
    match = re.search(r'\b([A-Z]{4})\b', text_upper)
    if match:
        candidate = match.group(1)
        if candidate not in ["DANA", "TAHUN", "BULAN", "MENU", "HALO", "INFO", "OJK", "RIIL"]:
            return f"{candidate}.JK"

    return None

def extract_nominal(text: str) -> float | None:
    """
    Mengekstrak nilai nominal rupiah dari teks (misal: 1000000, 1.5jt, 500rb, Rp 2.000.000).
    """
    text_lower = text.lower()
    
    # Cek format "juta" atau "jt" (misal: 1,5 juta atau 2jt)
    jt_match = re.search(r'([0-9]+(?:[.,][0-9]+)?)\s*(?:jt|juta)', text_lower)
    if jt_match:
        val = float(jt_match.group(1).replace(",", "."))
        return val * 1_000_000

    # Cek format "ribu" atau "rb" atau "k" (misal: 500rb)
    rb_match = re.search(r'([0-9]+(?:[.,][0-9]+)?)\s*(?:rb|ribu|k)', text_lower)
    if rb_match:
        val = float(rb_match.group(1).replace(",", "."))
        return val * 1_000

    # Cek format angka dengan titik pemisah ribuan (misal: 1.000.000 atau Rp 2.500.000)
    thousands_match = re.search(r'(?:rp\s*)?([0-9]{1,3}(?:\.[0-9]{3})+)', text_lower)
    if thousands_match:
        val_str = thousands_match.group(1).replace(".", "")
        return float(val_str)

    # Cek angka mentah minimal 4 digit (misal: 1000000)
    raw_digits_match = re.search(r'\b([0-9]{4,12})\b', text_lower)
    if raw_digits_match:
        return float(raw_digits_match.group(1))

    # Cek angka berurutan di dalam teks
    any_digits_match = re.search(r'([0-9]{4,12})', text_lower)
    if any_digits_match:
        return float(any_digits_match.group(1))

    return None

def extract_duration_years(text: str) -> float | None:
    """
    Mengekstrak durasi investasi dalam satuan tahun.
    """
    text_lower = text.lower()
    
    # Format tahun (misal: 3 tahun, 5 thn, 2y)
    yr_match = re.search(r'([0-9]+(?:[.,][0-9]+)?)\s*(?:tahun|thn|th|y|yr)', text_lower)
    if yr_match:
        return float(yr_match.group(1).replace(",", "."))

    # Format bulan (misal: 36 bulan) -> dikonversi ke tahun
    bln_match = re.search(r'([0-9]+)\s*(?:bulan|bln|m|mo)', text_lower)
    if bln_match:
        return float(bln_match.group(1)) / 12.0

    # Angka tunggal jika konteksnya adalah periode (misal: "3")
    single_digit = re.search(r'\b([1-9]|[1-4][0-9])\b', text_lower)
    if single_digit:
        return float(single_digit.group(1))

    return None

def extract_percentage(text: str) -> float | None:
    """
    Mengekstrak nilai persentase (misal: 8%, 9.5 persen, 0.08).
    Mengembalikan nilai desimal (misal 0.08 untuk 8%).
    """
    text_lower = text.lower()
    pct_match = re.search(r'([0-9]+(?:[.,][0-9]+)?)\s*(?:%|persen)', text_lower)
    if pct_match:
        val = float(pct_match.group(1).replace(",", "."))
        return val / 100.0

    dec_match = re.search(r'\b0\.[0-9]+\b', text_lower)
    if dec_match:
        return float(dec_match.group(0))

    return None

def extract_option_number(text: str) -> int | None:
    """
    Mengekstrak pilihan jawaban 1-4 atau A-D.
    """
    text_clean = text.strip().upper()
    mapping = {"A": 1, "B": 2, "C": 3, "D": 4}
    if text_clean in mapping:
        return mapping[text_clean]
    
    match = re.search(r'\b([1-4])\b', text_clean)
    if match:
        return int(match.group(1))
    return None
