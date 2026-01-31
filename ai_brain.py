# ai_brain.py
# عقل إسلامي: يقتنص فرص الشراء من القاع فقط 🦅📈
# -------------------------------------
import pandas_ta as ta

class QuantModel:
    def __init__(self):
        pass

    def analyze_market(self, df):
        try:
            # 1. حساب المؤشرات
            df['rsi'] = ta.rsi(df['close'], length=14)
            df['adx'] = ta.adx(df['high'], df['low'], df['close'], length=14)['ADX_14']
            
            # البولنجر باند (لقنص القيعان)
            bb = ta.bbands(df['close'], length=20, std=2)
            df['lower_band'] = bb['BBL_20_2.0']
            df['upper_band'] = bb['BBU_20_2.0']

            last = df.iloc[-1]
            prev = df.iloc[-2]

            score = 0
            signal = "NEUTRAL"

            # 🟢 استراتيجية الشراء (Spot Buy):
            # 1. السعر نزل تحت خط البولنجر السفلي (سعر رخيص جداً)
            # 2. RSI تحت 30 (تشبع بيعي)
            if last['close'] < last['lower_band'] or last['rsi'] < 30:
                score += 2
            
            # تأكيد قوة التريند الصاعد (ADX)
            if last['adx'] > 25:
                score += 1

            # 🔴 استراتيجية البيع (Spot Sell):
            # نبيع فقط لجني الربح عندما يتضخم السعر
            if last['rsi'] > 70 or last['close'] > last['upper_band']:
                score -= 2

            # القرار النهائي
            if score >= 2:
                signal = "BUY"
            elif score <= -2:
                signal = "SELL"
            
            return signal, last['rsi']

        except Exception as e:
            print(f"AI Error: {e}")
            return "NEUTRAL", 50
