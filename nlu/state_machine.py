import json
from database.connection import save_session_state, get_session_state, clear_session_state
from nlu.extractor import (
    extract_ticker, extract_nominal, extract_duration_years,
    extract_percentage, extract_option_number
)
from modules.regression import calculate_log_linear_trend, project_inflation_rate
from modules.sentiment import get_asset_sentiment_summary
from modules.clustering import get_single_asset_cluster, get_assets_by_profile
from modules.risk_profile import RISK_QUESTIONS, evaluate_risk_profile
from modules.calculator import calculate_dca, calculate_pension

class StateMachine:
    def __init__(self, session_id: str):
        self.session_id = session_id
        session = get_session_state(session_id)
        self.current_intent = session.get("current_intent")
        self.state_data = session.get("state_data", {})
        self.last_ticker = session.get("last_ticker")

    def save(self):
        save_session_state(
            self.session_id,
            self.current_intent,
            self.state_data,
            self.last_ticker
        )

    def reset(self):
        self.current_intent = None
        self.state_data = {}
        clear_session_state(self.session_id)

    def process_message(self, text: str, predicted_intent: str) -> dict:
        """
        Memproses teks pengguna berdasarkan state aktif saat ini dan intent hasil NLU.
        """
        # Ekstrak ticker jika ada di teks untuk memperbarui konteks aktif
        found_ticker = extract_ticker(text)
        if found_ticker:
            self.last_ticker = found_ticker

        # Prioritas Interupsi: Jika pengguna mengetik perintah/topik baru secara eksplisit, reset wizard lama
        interrupt_intents = [
            "start_risk_profile", "start_trend", "start_sentiment",
            "start_dca_calculator", "start_pension_calculator", "greeting",
            "help", "faq_data_source", "data_last_update", "show_asset_cluster",
            "recommend_by_profile", "explain_regression", "explain_r2",
            "explain_sentiment", "explain_cluster", "explain_volatility"
        ]
        if predicted_intent in interrupt_intents and not (self.current_intent == "risk_profile_in_progress" and extract_option_number(text)):
            if self.current_intent not in [None, "awaiting_trend_ticker", "awaiting_trend_period"]:
                self.current_intent = None
                self.state_data = {}

        # ----------------------------------------------------
        # 1. Alur Kuesioner Profil Risiko (Q1 - Q6)
        # ----------------------------------------------------
        if self.current_intent == "risk_profile_in_progress":
            step = self.state_data.get("step", 1)
            opt_score = extract_option_number(text)
            if not opt_score:
                return {
                    "type": "quick_reply",
                    "text": f"Mohon pilih nomor jawaban yang sesuai (1, 2, 3, atau 4) untuk pertanyaan {step}:\n\n"
                            f"**{RISK_QUESTIONS[step-1]['question']}**\n" +
                            "\n".join([f"{idx+1}. {opt['text']}" for idx, opt in enumerate(RISK_QUESTIONS[step-1]['options'])])
                }

            self.state_data[f"q{step}"] = opt_score
            step += 1
            self.state_data["step"] = step

            if step <= 6:
                self.save()
                next_q = RISK_QUESTIONS[step-1]
                options_text = "\n".join([f"{idx+1}. {opt['text']}" for idx, opt in enumerate(next_q['options'])])
                return {
                    "type": "quick_reply",
                    "text": f"**Pertanyaan {step}/6:**\n{next_q['question']}\n\n{options_text}"
                }
            else:
                # Selesai kuesioner Q1-Q6
                eval_result = evaluate_risk_profile(self.state_data)
                self.reset()
                return {
                    "type": "risk_result",
                    "data": eval_result
                }

        # ----------------------------------------------------
        # 2. Alur Kalkulator DCA Wizard
        # ----------------------------------------------------
        if self.current_intent == "dca_wizard":
            step = self.state_data.get("step", "amount")
            if step == "amount":
                nom = extract_nominal(text)
                if not nom:
                    return {"type": "text", "text": "Mohon masukkan nominal investasi bulanan yang valid (misal: Rp 1.000.000 atau 500rb)."}
                self.state_data["monthly_amount"] = nom
                
                # Cek apakah return sudah ada dari tren
                if "annual_return" not in self.state_data:
                    self.state_data["step"] = "return"
                    self.save()
                    return {"type": "text", "text": f"Nominal bulanan Rp {nom:,.0f} tersimpan.\nBerapa estimasi imbal hasil (return) tahunan yang diinginkan? (Contoh: 9% atau 12%)."}
                else:
                    self.state_data["step"] = "duration"
                    self.save()
                    return {"type": "text", "text": f"Nominal bulanan Rp {nom:,.0f} tersimpan.\nBerapa lama durasi investasi Anda dalam tahun? (Contoh: 3 tahun atau 5 tahun)."}

            elif step == "return":
                ret = extract_percentage(text)
                if ret is None:
                    return {"type": "text", "text": "Mohon masukkan angka persentase return yang valid (misal: 8% atau 10 persen)."}
                self.state_data["annual_return"] = ret
                self.state_data["step"] = "duration"
                self.save()
                return {"type": "text", "text": f"Estimasi return {ret*100:.1f}% per tahun tersimpan.\nBerapa lama durasi investasi Anda dalam tahun? (Contoh: 3 tahun atau 5 tahun)."}

            elif step == "duration":
                dur = extract_duration_years(text)
                if not dur:
                    return {"type": "text", "text": "Mohon masukkan durasi investasi yang valid dalam satuan tahun (misal: 3 tahun atau 5 tahun)."}
                self.state_data["duration_years"] = dur
                
                # Hitung hasil DCA
                calc_result = calculate_dca(
                    monthly_amount=self.state_data["monthly_amount"],
                    annual_return_rate=self.state_data["annual_return"],
                    duration_years=dur
                )
                self.reset()
                return {
                    "type": "dca_result",
                    "data": calc_result
                }

        # ----------------------------------------------------
        # 3. Alur Kalkulator Dana Pensiun Wizard
        # ----------------------------------------------------
        if self.current_intent == "pension_wizard":
            step = self.state_data.get("step", "current_age")
            if step == "current_age":
                age = extract_option_number(text) or extract_duration_years(text)
                if not age or age < 15 or age > 70:
                    return {"type": "text", "text": "Mohon masukkan usia Anda saat ini yang realistis (antara 17 hingga 70 tahun)."}
                self.state_data["current_age"] = int(age)
                self.state_data["step"] = "retirement_age"
                self.save()
                return {"type": "text", "text": f"Usia saat ini: {int(age)} tahun.\nDi usia berapa Anda merencanakan untuk pensiun? (Contoh: 55 tahun atau 60 tahun)."}

            elif step == "retirement_age":
                ret_age = extract_option_number(text) or extract_duration_years(text)
                current_age = self.state_data["current_age"]
                if not ret_age or ret_age <= current_age:
                    return {"type": "text", "text": f"Usia pensiun harus lebih besar dari usia saat ini ({current_age} tahun). Mohon masukkan kembali usia pensiun Anda."}
                self.state_data["retirement_age"] = int(ret_age)
                self.state_data["step"] = "monthly_expense"
                self.save()
                return {"type": "text", "text": f"Usia pensiun: {int(ret_age)} tahun.\nBerapa perkiraan pengeluaran biaya hidup bulanan Anda saat ini dalam Rupiah? (Contoh: Rp 5.000.000 atau 7jt)."}

            elif step == "monthly_expense":
                expense = extract_nominal(text)
                if not expense or expense < 500_000:
                    return {"type": "text", "text": "Mohon masukkan nominal pengeluaran bulanan yang valid (minimal Rp 500.000)."}
                self.state_data["monthly_expense"] = expense
                
                # Dapatkan proyeksi inflasi dinamis dari regresi BI/BPS
                proj_inf = project_inflation_rate()
                default_inf = proj_inf.get("projected_inflation", 3.5) / 100.0
                self.state_data["annual_inflation"] = default_inf

                # Hitung hasil Pensiun
                pension_res = calculate_pension(
                    current_age=self.state_data["current_age"],
                    retirement_age=self.state_data["retirement_age"],
                    monthly_expense_now=expense,
                    annual_inflation_rate=default_inf,
                    annual_return_rate=0.08  # Default return konservatif-moderat
                )
                self.reset()
                return {
                    "type": "pension_result",
                    "data": pension_res,
                    "inflation_metadata": proj_inf
                }

        # ----------------------------------------------------
        # 4. Input Pending untuk Tren Aset
        # ----------------------------------------------------
        if self.current_intent == "awaiting_trend_period":
            dur = extract_duration_years(text) or 1.0
            ticker = self.state_data.get("ticker") or self.last_ticker or "^JKSE"
            trend_res = calculate_log_linear_trend(ticker, period_years=dur)
            self.reset()
            self.last_ticker = ticker
            self.save()
            return {
                "type": "trend_result",
                "data": trend_res
            }

        # ----------------------------------------------------
        # 5. Intent Handling Bebas (Fresh Intents)
        # ----------------------------------------------------
        if predicted_intent == "start_risk_profile":
            self.current_intent = "risk_profile_in_progress"
            self.state_data = {"step": 1}
            self.save()
            first_q = RISK_QUESTIONS[0]
            options_text = "\n".join([f"{idx+1}. {opt['text']}" for idx, opt in enumerate(first_q['options'])])
            return {
                "type": "quick_reply",
                "text": f"Mari kita mulai Kuesioner Profil Risiko untuk menentukan strategi investasi yang tepat bagi Anda.\n\n"
                        f"**Pertanyaan 1/6:**\n{first_q['question']}\n\n{options_text}"
            }

        elif predicted_intent == "start_trend":
            ticker = found_ticker or self.last_ticker
            dur = extract_duration_years(text)
            if not ticker:
                self.current_intent = "awaiting_trend_ticker"
                self.save()
                return {"type": "text", "text": "Aset apa yang ingin Anda lihat trennya? (Contoh: BBCA, BBRI, IHSG, atau Bitcoin)."}
            
            if not dur:
                self.current_intent = "awaiting_trend_period"
                self.state_data = {"ticker": ticker}
                self.save()
                return {"type": "text", "text": f"Untuk aset {ticker}, berapa periode tahun yang ingin dianalisis? (Contoh: 1 tahun, 2 tahun, atau 3 tahun)."}

            trend_res = calculate_log_linear_trend(ticker, period_years=dur)
            return {"type": "trend_result", "data": trend_res}

        elif self.current_intent == "awaiting_trend_ticker":
            ticker = found_ticker or extract_ticker(text) or "BBCA.JK"
            self.last_ticker = ticker
            self.current_intent = "awaiting_trend_period"
            self.state_data = {"ticker": ticker}
            self.save()
            return {"type": "text", "text": f"Ticker {ticker} dipilih. Berapa periode tahun yang ingin dianalisis? (Contoh: 1 tahun, 2 tahun, atau 3 tahun)."}

        elif predicted_intent == "use_trend_for_dca":
            # Ambil return dari analisis tren terakhir
            ticker = self.last_ticker or "^JKSE"
            trend_res = calculate_log_linear_trend(ticker, period_years=1.0)
            ann_ret = trend_res.get("annual_return", 0.08)

            self.current_intent = "dca_wizard"
            self.state_data = {
                "step": "amount",
                "annual_return": ann_ret,
                "ticker_source": ticker
            }
            self.save()

            warning_note = ""
            if ann_ret <= 0.0:
                warning_note = f"\n⚠️ Catatan: Estimasi return tren {ticker} ({ann_ret*100:.2f}%) sedang negatif/rendah."

            return {
                "type": "text",
                "text": f"Baik! Kita akan simulasikan DCA menggunakan estimasi return tren {ticker} sebesar **{ann_ret*100:.2f}% per tahun**.{warning_note}\n\n"
                        f"Berapa nominal investasi rutin yang ingin Anda sisihkan setiap bulan? (Contoh: Rp 1.000.000 atau 500rb)."
            }

        elif predicted_intent == "start_dca_calculator":
            self.current_intent = "dca_wizard"
            self.state_data = {"step": "amount"}
            self.save()
            return {
                "type": "text",
                "text": "Selamat datang di Kalkulator DCA (Dollar Cost Averaging).\nBerapa nominal investasi rutin yang ingin Anda sisihkan setiap bulan? (Contoh: Rp 1.000.000 atau 500rb)."
            }

        elif predicted_intent == "start_pension_calculator":
            self.current_intent = "pension_wizard"
            self.state_data = {"step": "current_age"}
            self.save()
            return {
                "type": "text",
                "text": "Selamat datang di Kalkulator Dana Pensiun InvestBuddy.\nBerapa usia Anda saat ini? (Contoh: 23 tahun)."
            }

        elif predicted_intent == "start_sentiment":
            ticker = found_ticker or self.last_ticker or "BBCA.JK"
            self.last_ticker = ticker
            self.save()
            sentiment_summary = get_asset_sentiment_summary(ticker)
            return {
                "type": "sentiment_result",
                "data": sentiment_summary
            }

        elif predicted_intent == "sentiment_news_list":
            ticker = found_ticker or self.last_ticker or "BBCA.JK"
            sentiment_summary = get_asset_sentiment_summary(ticker)
            return {
                "type": "sentiment_news_result",
                "data": sentiment_summary
            }

        elif predicted_intent == "show_asset_cluster":
            ticker = found_ticker or self.last_ticker or "BBCA.JK"
            cluster_info = get_single_asset_cluster(ticker)
            return {
                "type": "cluster_single_result",
                "data": cluster_info
            }

        elif predicted_intent == "recommend_by_profile":
            # Deteksi apakah profil disebut di teks
            text_lower = text.lower()
            if "konservatif" in text_lower:
                profile = "Konservatif"
            elif "agresif" in text_lower:
                profile = "Agresif"
            else:
                profile = "Moderat"

            assets = get_assets_by_profile(profile)
            return {
                "type": "profile_recommendation_result",
                "profile": profile,
                "assets": assets[:5]
            }

        return {"type": "direct_intent", "intent": predicted_intent}
