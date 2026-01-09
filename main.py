# main.py
# V23: Institutional Sniper (Render Edition) 🦅
# -------------------------------------
import ccxt
import pandas as pd
import time
import requests
import sys
import gc
import os
from datetime import datetime, timedelta
import config
from telegram_bot import TelegramBot
from ai_brain import QuantModel
from vision import ChartPainter
from keep_alive import keep_alive 

# تشغيل القلب
keep_alive()

class MarketFeed:
    def __init__(self):
        # في Render نستخدم متغيرات البيئة
        # إذا لم نجدها، نستخدم القيم الموجودة في config (للاحتياط)
        api = os.environ.get('API_KEY', config.API_KEY)
        sec = os.environ.get('SECRET_KEY', config.SECRET_KEY)
        
        self.writer = ccxt.binance({'apiKey': api, 'secret': sec, 'options': {'defaultType': 'future'}})
        self.reader = ccxt.kucoin() 
        
    def get_price(self):
        try: 
            ticker = self.reader.fetch_ticker('SOL/USDT')
            return float(ticker['last'])
        except: return 0.0

    def get_candles(self, timeframe, limit=1000): # 1000 شمعة
        try:
            bars = self.reader.fetch_ohlcv('SOL/USDT', timeframe, limit=limit)
            if not bars: return None
            df = pd.DataFrame(bars, columns=['t', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except: return None

    def get_btc_sentiment(self):
        try:
            bars = self.reader.fetch_ohlcv('BTC/USDT', '1h', limit=24)
            if not bars: return "NEUTRAL"
            closes = [x[4] for x in bars]
            return "BULLISH 🟢" if closes[-1] > closes[0] else "BEARISH 🔴"
        except: return "NEUTRAL ⚪"

class TradingEngine:
    def __init__(self):
        self.balance = config.INITIAL_CAPITAL
        self.position = None
        self.pnl_history = []
    
    def check_institutional_volume(self, df):
        try:
            vol_ma = df['volume'].rolling(window=20).mean().iloc[-1]
            current_vol = df['volume'].iloc[-1]
            if current_vol > vol_ma * 1.2: return True, "🔥 High Vol"
            return False, "❄️ Normal"
        except: return False, "Unknown"

    def execute_trade(self, signal, price, atr):
        if self.position: return None
        sl_dist = atr * 2.0 
        tp_dist = atr * 4.0
        if signal == 'LONG':
            sl = price - sl_dist
            tp = price + tp_dist
        else:
            sl = price + sl_dist
            tp = price - tp_dist
        risk_amt = self.balance * config.RISK_PER_TRADE
        qty = risk_amt / sl_dist if sl_dist > 0 else 0
        self.position = {'type': signal, 'entry': price, 'qty': qty, 'sl': sl, 'tp': tp}
        return self.position

    def update_position(self, current_price):
        if not self.position: return 0.0
        pos = self.position
        pnl = 0.0
        closed = False
        if pos['type'] == 'LONG':
            if current_price >= pos['tp']:
                pnl = (pos['tp'] - pos['entry']) * pos['qty']
                closed = True
            elif current_price <= pos['sl']:
                pnl = (pos['sl'] - pos['entry']) * pos['qty']
                closed = True
        else:
            if current_price <= pos['tp']:
                pnl = (pos['entry'] - pos['tp']) * pos['qty']
                closed = True
            elif current_price >= pos['sl']:
                pnl = (pos['entry'] - pos['sl']) * pos['qty']
                closed = True
        if closed:
            self.balance += pnl
            self.pnl_history.append(pnl)
            self.position = None
            return pnl
        return 0.0

def prepare_for_painter(df_in):
    df_out = df_in.copy()
    df_out.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
    df_out.index = pd.to_datetime(df_out['t'], unit='ms')
    return df_out

def run_bot():
    # محاولة جلب التوكن من البيئة أولاً
    token = os.environ.get('BOT_TOKEN', config.BOT_TOKEN)
    chat_id = os.environ.get('CHAT_ID', config.CHAT_ID)
    
    # تحديث Config مؤقتاً ليعمل البوت
    config.BOT_TOKEN = token
    config.CHAT_ID = chat_id
    
    bot = TelegramBot()
    market = MarketFeed()
    engine = TradingEngine()
    ai = QuantModel()
    painter = ChartPainter()
    
    bot.show_keyboard("🦅 <b>V23: Render Edition</b>\nتم تفعيل النظام على السيرفر الجديد.")
    print("🦅 V23 Running on Render...")
    
    status = "RUNNING"
    last_radar_time = 0
    
    while True:
        try:
            current_time = time.time()
            price = market.get_price()
            
            # معالجة الأوامر
            cmd = bot.check_updates()
            if cmd:
                if "شارت" in cmd and price > 0:
                    bot.send("📸 جاري التحليل...")
                    df = market.get_candles(config.TIMEFRAME)
                    if df is not None:
                        img = painter.draw_entry_chart(prepare_for_painter(df.tail(80)), price, price, price, "MANUAL")
                        if img: bot.send_photo(img, f"Price: {price}")
                        try: img.close(); del img; del df; gc.collect()
                        except: pass
                
                elif "رادار" in cmd: 
                    bot.send("📡 جاري المسح...")
                    last_radar_time = 0 

                elif "الرصيد" in cmd:
                    pnl = sum(engine.pnl_history)
                    bot.send(f"💰 Balance: {engine.balance:.2f}$\nPnL: {pnl:.2f}$")

                elif "تقرير" in cmd:
                    dz_time = datetime.now() + timedelta(hours=1)
                    bot.send(f"📊 Status: {status}\n🚀 Server: Render\n⏳ Time: {dz_time.strftime('%H:%M:%S')}")

                elif "إيقاف" in cmd: status = "PAUSED"; bot.send("⏸️ Paused")
                elif "تشغيل" in cmd: status = "RUNNING"; bot.send("▶️ Running")

            # الرادار الآلي
            if status == "RUNNING" and price > 0:
                if engine.position:
                    pnl = engine.update_position(price)
                    if pnl != 0:
                        emoji = "✅ PROFIT" if pnl > 0 else "🛑 STOP"
                        bot.send(f"{emoji} <b>Trade Closed:</b> {pnl:.2f}$")
                
                # الفحص كل 60 ثانية
                if current_time - last_radar_time > 60: 
                    try:
                        df_1000 = market.get_candles(config.TIMEFRAME, limit=1000)
                        
                        if df_1000 is not None:
                            pred, conf = ai.predict(df_1000)
                            
                            btc_mood = market.get_btc_sentiment()
                            trend_long = "UP 🟢" if df_1000['close'].iloc[-1] > df_1000['close'].iloc[-20] else "DOWN 🔴"
                            is_whale, vol_msg = engine.check_institutional_volume(df_1000)
                            
                            if engine.position is None and conf > config.CONFIDENCE_THRESHOLD * 100:
                                signal = "LONG" if pred == 1 else "SHORT"
                                entry_valid = False
                                if signal == "LONG" and "UP" in trend_long and "BEARISH" not in btc_mood: entry_valid = True
                                if signal == "SHORT" and "DOWN" in trend_long and "BULLISH" not in btc_mood: entry_valid = True
                                
                                if entry_valid:
                                    atr = (df_1000['high'] - df_1000['low']).mean()
                                    pos = engine.execute_trade(signal, price, atr)
                                    if pos:
                                        bot.send(f"🐋 <b>ENTRY:</b> {signal} @ {price}\n{vol_msg}")
                                        try:
                                            img = painter.draw_entry_chart(prepare_for_painter(df_1000.tail(60)), price, price, price, "ENTRY")
                                            if img: bot.send_photo(img, "Sniper Entry")
                                            img.close(); del img
                                        except: pass

                            ai_icon = "🐂 BULL" if pred == 1 else "🐻 BEAR"
                            msg = (
                                f"📡 <b>RADAR SCAN</b>\n"
                                f"💎 Price: {price}\n"
                                f"🧠 AI: <b>{ai_icon}</b> ({conf:.1f}%)\n"
                                f"🌊 Vol: {vol_msg}\n"
                                f"🌍 BTC: {btc_mood}"
                            )
                            try:
                                img_radar = painter.draw_entry_chart(prepare_for_painter(df_1000.tail(60)), price, price, price, "RADAR")
                                if img_radar: bot.send_photo(img_radar, msg, 'news')
                                img_radar.close(); del img_radar
                            except: pass
                            
                            last_radar_time = current_time
                            del df_1000
                            gc.collect()
                            
                    except Exception as e:
                        print(f"Radar Error: {e}")
                        gc.collect()

            time.sleep(1)
            
        except Exception as e:
            print(f"Main Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
