# ai_brain.py
# العقل التحليلي - يعتمد على الرياضيات وليس التوقعات العشوائية
# -------------------------------------
import pandas as pd
import numpy as np

class QuantModel:
    def __init__(self):
        self.is_trained = True # جاهز دائماً

    def train(self, df):
        pass # لا يحتاج تدريب معقد، يعتمد على المؤشرات

    def calculate_indicators(self, df):
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema12'] - df['ema26']
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        return df

    def predict(self, df):
        try:
            df = self.calculate_indicators(df)
            last_row = df.iloc[-1]
            
            score = 0
            # تحليل RSI
            if last_row['rsi'] < 30: score += 1 # تشبع بيعي (فرصة شراء)
            elif last_row['rsi'] > 70: score -= 1 # تشبع شرائي (فرصة بيع)
            
            # تحليل MACD
            if last_row['macd'] > last_row['signal']: score += 1
            else: score -= 1
            
            # اتجاه الشموع
            if df['close'].iloc[-1] > df['close'].iloc[-10]: score += 1
            else: score -= 1

            # النتيجة النهائية
            confidence = 80.0 + (abs(score) * 5) # قاعدة ثقة
            if confidence > 99: confidence = 99.0
            
            prediction = 1 if score > 0 else 0 # 1 شراء، 0 بيع
            
            return prediction, confidence
            
        except:
            return 0, 50.0
