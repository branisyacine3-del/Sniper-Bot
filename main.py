# main.py
# V42: HALAL SPOT TRADER (Light & Fast) 🦅
# -------------------------------------------------------------
import ccxt
import pandas as pd
import time
import os
from datetime import datetime
import config
from telegram_bot import TelegramBot
from ai_brain import QuantModel

# تهيئة الأدوات
bot = TelegramBot()
brain = QuantModel()
# تم حذف الرسام painter لتخفيف الحمل وضمان العمل

# الاتصال بالمنصة (بايننس سبوت)
exchange = ccxt.binance({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

class HalalEngine:
    def __init__(self):
        self.usdt_balance = config.INITIAL_CAPITAL
        self.portfolio = {} 

    def fetch_data(self, symbol):
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=config.TIMEFRAME, limit=100)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except Exception as e:
            print(f"Data Error {symbol}: {e}")
            return None

    def execute_trade(self, symbol, signal, price, rsi):
        # 🟢 منطق الشراء
        if signal == "BUY":
            # هنا يجب إضافة منطق التحقق من الرصيد الحقيقي لاحقاً
            msg = (f"🟢 <b>HALAL BUY SIGNAL: {symbol}</b>\n"
                   f"💵 Price: {price:.4f}\n"
                   f"📉 RSI: {rsi:.2f}\n"
                   f"🦅 Action: Spot Buy Opportunity")
            bot.send_news(msg)
            print(msg)

        # 🔴 منطق البيع
        elif signal == "SELL":
            msg = (f"💰 <b>HALAL SELL SIGNAL: {symbol}</b>\n"
                   f"💵 Price: {price:.4f}\n"
                   f"📈 RSI: {rsi:.2f}\n"
                   f"🦅 Action: Take Profit")
            bot.send_news(msg)
            print(msg)

    def scan_market(self):
        print(f"🦅 Scanning Market...")
        bot.send_admin("🦅 <b>Routine Check Started...</b>")
        
        for symbol in config.TARGETS:
            df = self.fetch_data(symbol)
            if df is None: continue
            
            signal, rsi = brain.analyze_market(df)
            current_price = df['close'].iloc[-1]
            
            self.execute_trade(symbol, signal, current_price, rsi)

def run_bot():
    # تشغيل الفحص مرة واحدة (GitHub سيقوم بتكراره كل 15 دقيقة)
    engine = HalalEngine()
    engine.scan_market()
    print("✅ Check Complete. Closing session.")

if __name__ == "__main__":
    run_bot()
 
