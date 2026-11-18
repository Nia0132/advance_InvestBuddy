import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from nlu.classifier import get_intent
from nlu.state_machine import StateMachine
from llm.client import generate_grounded_response
from modules.calculator import calculate_dca, calculate_pension

def test_nlu_and_flow():
    print("=== PENGUJIAN OTOMATIS FITUR INVESTBUDDY ===")

    # 1. Test NLU Latency
    queries = [
        "Halo apa kabar?",
        "Data dari mana?",
        "Tren IHSG bagaimana?",
        "Sentimen BBCA?",
        "BBCA masuk klaster apa?",
        "Hitung DCA",
        "Kalkulator dana pensiun",
        "Apa itu regresi linear?",
        "Apa itu R²?",
        "Mulai tes profil risiko"
    ]
    print("\n--- 1. Uji Klasifikasi NLU ---")
    for q in queries:
        t0 = time.time()
        intent, conf = get_intent(q)
        lat_ms = (time.time() - t0) * 1000
        print(f"Query: '{q}' -> Intent: {intent} (Conf: {conf:.2f}, Latency: {lat_ms:.2f} ms)")
        assert lat_ms < 20, "NLU latency melebihi batas 20ms!"

    # 2. Test Trend Regression
    print("\n--- 2. Uji Analisis Tren Regresi (BBCA.JK) ---")
    sm = StateMachine("test_session_1")
    sm.reset()
    res = sm.process_message("Tren BBCA 2 tahun", "start_trend")
    reply = generate_grounded_response("start_trend", "Tren BBCA 2 tahun", res)
    print("Respons Tren:")
    print(reply[:300] + "...")
    assert "Hasil Analisis Tren Regresi" in reply

    # 3. Test Sentimen BBCA
    print("\n--- 3. Uji Sentimen Berita (BBCA) ---")
    res_sent = sm.process_message("Sentimen BBCA?", "start_sentiment")
    reply_sent = generate_grounded_response("start_sentiment", "Sentimen BBCA?", res_sent)
    print("Respons Sentimen:")
    print(reply_sent[:300] + "...")
    assert "Sentimen Berita Pasar" in reply_sent

    # 4. Test Use Trend for DCA
    print("\n--- 4. Uji Integrasi Tren ke DCA ---")
    res_dca_prep = sm.process_message("Hitung DCA pakai hasil itu", "use_trend_for_dca")
    reply_dca_prep = generate_grounded_response("use_trend_for_dca", "Hitung DCA pakai hasil itu", res_dca_prep)
    print(reply_dca_prep[:200] + "...")
    assert "DCA menggunakan estimasi return" in reply_dca_prep

    # 5. Test DCA Step: Nominal -> Durasi -> Hasil
    res_dca_amt = sm.process_message("1000000 per bulan", "dca_wizard")
    print("Step Nominal ->", res_dca_amt.get("text"))
    res_dca_final = sm.process_message("3 tahun", "dca_wizard")
    reply_dca_final = generate_grounded_response("dca_wizard", "3 tahun", res_dca_final)
    print("Hasil Final DCA:")
    print(reply_dca_final)
    assert "Hasil Simulasi DCA" in reply_dca_final

    # 6. Test Safeguard Return = 0% pada DCA
    print("\n--- 6. Uji Pengamanan Return = 0% DCA ---")
    zero_dca = calculate_dca(monthly_amount=1_000_000, annual_return_rate=0.0, duration_years=2)
    assert zero_dca["future_value"] == 24_000_000, "Nilai akhir return 0% salah!"
    assert zero_dca["interest_earned"] == 0.0
    print("Safeguard DCA r=0% lolos (FV = Rp 24.000.000, no ZeroDivisionError).")

    # 7. Test Safeguard Pension: Return <= Inflasi
    print("\n--- 7. Uji Pengamanan Kalkulator Pensiun ---")
    pension_res = calculate_pension(
        current_age=25, retirement_age=55, monthly_expense_now=5_000_000,
        annual_inflation_rate=0.04, annual_return_rate=0.03
    )
    assert pension_res["real_return_warning"] is not None
    print("Safeguard Pensiun lolos (Warning:", pension_res["real_return_warning"][:70], "...)")

    # 8. Test Kuesioner Profil Risiko Multi-Turn
    print("\n--- 8. Uji Multi-Turn Kuesioner Profil Risiko (Q1-Q6) ---")
    sm_risk = StateMachine("test_risk_session")
    step1 = sm_risk.process_message("Mulai tes profil risiko", "start_risk_profile")
    print("Pertanyaan 1 muncul:", "Pertanyaan 1/6" in step1["text"])
    
    # Jawab Q1=4, Q2=4, Q3=4, Q4=4, Q5=2 (dana darurat rendah -> override dari Agresif ke Moderat!), Q6=4
    sm_risk.process_message("4", "quick_reply")
    sm_risk.process_message("4", "quick_reply")
    sm_risk.process_message("4", "quick_reply")
    sm_risk.process_message("4", "quick_reply")
    sm_risk.process_message("2", "quick_reply") # Q5
    final_risk = sm_risk.process_message("4", "quick_reply") # Q6
    
    reply_risk = generate_grounded_response("risk_result", "3", final_risk)
    print("Hasil Kuesioner:")
    print(reply_risk[:400] + "...")
    assert "Hasil Evaluasi Profil Risiko Anda" in reply_risk
    assert "Penyesuaian Dana Darurat" in reply_risk

    print("\n=== SEMUA 8 PENGUJIAN OTOMATIS BERHASIL DENGAN SEMPURNA! ===")

if __name__ == "__main__":
    test_nlu_and_flow()
