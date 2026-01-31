# ai_brain.py
# العقل الإسلامي: معادلات يدوية (بدون مكتبات خارجية) 🦅📈
# -------------------------------------
import pandas as pd

class QuantModel:
    def __init__(self):
        pass

    def calculate_rsi(self, series, period=14):
        # معادلة RSI الرياضية يدوياً
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def analyze_market(self, df):
        try:
            # 1. حساب RSI يدوياً
            df['rsi'] = self.calculate_rsi(df['close'], period=14)
            
            # 2. حساب مؤشر بسيط للبولنجر باند يدوياً
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['lower_band'] = sma - (2 * std)
            df['upper_band'] = sma + (2 * std)

            last = df.iloc[-1]

            score = 0
            signal = "NEUTRAL"

            # 🟢 استراتيجية الشراء (Spot Buy):
            # السعر رخيص (تحت البولنجر) + RSI منخفض
            if last['close'] < last['lower_band'] or last['rsi'] < 30:
                score += 2
            
            # 🔴 استراتيجية البيع (Spot Sell):
            # السعر غالٍ (فوق البولنجر) + RSI مرتفع
            if last['rsi'] > 70 or last['close'] > last['upper_band']:
                score -= 2

            # القرار
            if score >= 2:
                signal = "BUY"
            elif score <= -2:
                signal = "SELL"
            
            return signal, last['rsi']

        except Exception as e:
            print(f"AI Error: {e}")
            return "NEUTRAL", 50
