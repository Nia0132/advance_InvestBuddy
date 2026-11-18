import math

def calculate_dca(monthly_amount: float, annual_return_rate: float, duration_years: float) -> dict:
    """
    Menghitung simulasi Dollar Cost Averaging (DCA) bulanan secara deterministik.
    monthly_amount: Nominal investasi bulanan (Rp)
    annual_return_rate: Estimasi return tahunan (desimal, misal 0.08 untuk 8%)
    duration_years: Durasi investasi (tahun)
    """
    total_months = int(round(duration_years * 12))
    if total_months <= 0 or monthly_amount <= 0:
        return {
            "success": False,
            "message": "Nominal bulanan dan durasi harus lebih besar dari 0."
        }

    total_principal = monthly_amount * total_months

    # PENGAMANAN 1: Penanganan return = 0% untuk mencegah ZeroDivisionError
    if abs(annual_return_rate) < 1e-9:
        future_value = total_principal
        interest_earned = 0.0
        monthly_rate = 0.0
    else:
        # Suku bunga bulanan ekuivalen majemuk
        monthly_rate = math.pow(1.0 + annual_return_rate, 1.0 / 12.0) - 1.0
        # Formula Anuitas Due (investasi dilakukan di awal setiap bulan)
        growth_factor = math.pow(1.0 + monthly_rate, total_months)
        future_value = monthly_amount * ((growth_factor - 1.0) / monthly_rate) * (1.0 + monthly_rate)
        interest_earned = future_value - total_principal

    return {
        "success": True,
        "monthly_amount": monthly_amount,
        "annual_return_rate": annual_return_rate,
        "annual_return_pct": round(annual_return_rate * 100, 2),
        "duration_years": duration_years,
        "total_months": total_months,
        "total_principal": round(total_principal),
        "future_value": round(future_value),
        "interest_earned": round(interest_earned),
        "profit_percentage": round((interest_earned / total_principal) * 100, 2) if total_principal > 0 else 0.0,
        "note": "Perhitungan menggunakan bunga majemuk bulanan anuitas di awal periode."
    }

def calculate_pension(
    current_age: int,
    retirement_age: int,
    monthly_expense_now: float,
    annual_inflation_rate: float = 0.035,
    annual_return_rate: float = 0.07,
    life_expectancy: int = 75
) -> dict:
    """
    Menghitung kebutuhan dana pensiun dan tabungan bulanan yang dibutuhkan.
    Dilengkapi pengamanan return = 0% dan deteksi real return negatif.
    """
    years_to_save = retirement_age - current_age
    years_in_retirement = life_expectancy - retirement_age

    if years_to_save <= 0 or years_in_retirement <= 0:
        return {
            "success": False,
            "message": "Usia pensiun harus lebih besar dari usia saat ini dan lebih kecil dari harapan hidup."
        }

    # PENGAMANAN 2: Peringatan Real Return Negatif / Rendah
    real_return_warning = None
    if annual_return_rate <= annual_inflation_rate:
        real_return_warning = (
            f"Perhatian: Asumsi return investasi ({annual_return_rate*100:.1f}%) lebih kecil atau sama dengan "
            f"tingkat inflasi ({annual_inflation_rate*100:.1f}%). Secara riil, daya beli dana Anda berpotensi tergerus inflasi."
        )

    # 1. Biaya hidup bulanan saat mulai pensiun (disesuaikan inflasi)
    monthly_expense_retirement = monthly_expense_now * math.pow(1.0 + annual_inflation_rate, years_to_save)
    annual_expense_retirement = monthly_expense_retirement * 12.0

    # 2. Tingkat return riil pasca-pensiun
    real_rate = (1.0 + annual_return_rate) / (1.0 + annual_inflation_rate) - 1.0

    # Total dana pensiun yang dibutuhkan saat mencapai usia pensiun
    if abs(real_rate) < 1e-9:
        total_pension_fund = annual_expense_retirement * years_in_retirement
    else:
        pv_factor = (1.0 - math.pow(1.0 + real_rate, -years_in_retirement)) / real_rate
        total_pension_fund = annual_expense_retirement * pv_factor

    # 3. Tabungan bulanan yang perlu disisihkan mulai sekarang
    months_to_save = years_to_save * 12
    # PENGAMANAN 1: Return = 0%
    if abs(annual_return_rate) < 1e-9:
        monthly_saving_required = total_pension_fund / months_to_save
    else:
        monthly_i = math.pow(1.0 + annual_return_rate, 1.0 / 12.0) - 1.0
        fv_factor = ((math.pow(1.0 + monthly_i, months_to_save) - 1.0) / monthly_i) * (1.0 + monthly_i)
        monthly_saving_required = total_pension_fund / fv_factor

    return {
        "success": True,
        "current_age": current_age,
        "retirement_age": retirement_age,
        "life_expectancy": life_expectancy,
        "years_to_save": years_to_save,
        "years_in_retirement": years_in_retirement,
        "monthly_expense_now": round(monthly_expense_now),
        "monthly_expense_retirement": round(monthly_expense_retirement),
        "annual_inflation_pct": round(annual_inflation_rate * 100, 2),
        "annual_return_pct": round(annual_return_rate * 100, 2),
        "total_pension_fund_needed": round(total_pension_fund),
        "monthly_saving_required": round(monthly_saving_required),
        "real_return_warning": real_return_warning
    }
