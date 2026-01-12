# main.py
# V26: THE INVINCIBLE BOT (Multi-Pair + ADX Shield) 🦅
# -------------------------------------
import ccxt
import pandas as pd
import pandas_ta as ta  # تأكد من وجود هذه المكتبة في requirements.txt
import time
import requests
import sys
import gc
import os
from datetime import datetime
import config
from telegram_bot import TelegramBot
from ai_brain import QuantModel
from vision import ChartPainter
from keep_alive import keep_alive 

keep_alive()

class MarketFeed:
    def __init__(self):
        self.exchange = ccxt.kucoin() # نستخدم KuCoin للبيانات لأنه سريع ومجاني
        
    def get_data(self, symbol):
        try:
            # جلب الشموع
            bars = self.exchange.fetch_ohlcv(symbol, config.TIMEFRAME, limit=100)
            df = pd.DataFrame(bars, columns=['t', 'open', 'high', 'low', 'close', 'volume'])
            df['t'] = pd.to_datetime(df['t'], unit='ms')
            
            # حساب المؤشرات الفنية (ADX + RSI)
            df.ta.adx(length=14, append=True) # يضيف ADX_14
            df.ta.rsi(length=14, append=True) # يضيف RSI_14
            
            return df
        except: return None

    def get_price(self, symbol):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except: return 0.0

class TradingEngine:
    def __init__(self):
        self.balance = config.INITIAL_CAPITAL
        self.positions = {} # قاموس لتخزين الصفقات لكل عملة
        self.history = []

    def calculate_position_size(self, confidence):
        # المحفظة الذكية: تزيد المخاطرة إذا كانت الثقة عالية
        risk_pct = config.HIGH_RISK if confidence > 0.90 else config.NORMAL_RISK
        amount = self.balance * risk_pct
        return amount

    def open_position(self, symbol, type, price, atr, confidence):
        if symbol in self.positions: return None # لا نفتح صفقتين لنفس العملة
        
        sl_dist = atr * 2.0
        tp_dist = atr * 4.0 # العائد ضعف المخاطرة (2:1)
        
        if type == 'LONG':
            sl = price - sl_dist
            tp = price + tp_dist
        else:
            sl = price + sl_dist
            tp = price - tp_dist
            
        qty = self.calculate_position_size(confidence) / price
        
        pos = {
            'symbol': symbol, 'type': type, 'entry': price, 
            'qty': qty, 'sl': sl, 'tp': tp, 
            'highest_price': price, # للوقف المتحرك
            'start_time': datetime.now()
        }
        self.positions[symbol] = pos
        return pos

    def manage_positions(self, current_prices):
        # مراقبة جميع الصفقات المفتوحة
        closed_trades = []
        active_symbols = list(self.positions.keys())
        
        for sym in active_symbols:
            pos = self.positions[sym]
            curr = current_prices.get(sym, 0)
            if curr == 0: continue
            
            pnl = 0
            closed = False
            reason = ""
            
            # 1. تحديث الوقف المتحرك (Trailing Stop) - الدرع النووي
            if pos['type'] == 'LONG':
                if curr > pos['highest_price']: pos['highest_price'] = curr
                # إذا تحرك السعر 1% لصالحنا، نحرك الوقف للدخول
                if (pos['highest_price'] - pos['entry']) / pos['entry'] > 0.01:
                    new_sl = pos['entry'] * 1.001 # فوق الدخول بقليل
                    if new_sl > pos['sl']: pos['sl'] = new_sl
            
                # فحص الخروج
                if curr >= pos['tp']:
                    pnl = (pos['tp'] - pos['entry']) * pos['qty']
                    closed = True; reason = "Take Profit ✅"
                elif curr <= pos['sl']:
                    pnl = (pos['sl'] - pos['entry']) * pos['qty']
                    closed = True; reason = "Stop Loss 🛑"
                    
            else: # SHORT
                if curr < pos['highest_price']: pos['highest_price'] = curr
                if (pos['entry'] - pos['highest_price']) / pos['entry'] > 0.01:
                    new_sl = pos['entry'] * 0.999
                    if new_sl < pos['sl']: pos['sl'] = new_sl
                    
                if curr <= pos['tp']:
                    pnl = (pos['entry'] - pos['tp']) * pos['qty']
                    closed = True; reason = "Take Profit ✅"
                elif curr >= pos['sl']:
                    pnl = (pos['entry'] - pos['sl']) * pos['qty']
                    closed = True; reason = "Stop Loss 🛑"
            
            if closed:
                self.balance += pnl
                self.history.append(pnl)
                closed_trades.append((pos, pnl, reason))
                del self.positions[sym]
                
        return closed_trades

def prepare_chart_data(df):
    df_out = df.copy()
    df_out.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
    df_out.index = df_out['t']
    return df_out

def run_bot():
    bot = TelegramBot()
    market = MarketFeed()
    engine = TradingEngine()
    ai = QuantModel()
    painter = ChartPainter()
    
    bot.show_keyboard("🦅 <b>V26: INVINCIBLE ONLINE</b>\n- Multi-Pair Active\n- ADX Shield Active\n- Smart Wallet Ready")
    print("🦅 V26 Scanning Targets...")
    
    while True:
        try:
            current_prices = {}
            
            # 1. الدورة على جميع العملات (المسح الراداري)
            for symbol in config.TARGETS:
                df = market.get_data(symbol)
                price = market.get_price(symbol)
                current_prices[symbol] = price
                
                if df is None or len(df) < 50: continue
                
                # --- الفلتر الدفاعي (ADX) ---
                adx_val = df['ADX_14'].iloc[-1]
                if adx_val < config.ADX_THRESHOLD:
                    # السوق ميت، تجاوز هذه العملة
                    continue
                
                # --- الذكاء الاصطناعي ---
                pred, conf = ai.predict(df)
                
                # شروط الدخول الصارمة
                if symbol not in engine.positions and conf > config.CONFIDENCE_THRESHOLD * 100:
                    signal = "LONG" if pred == 1 else "SHORT"
                    
                    # حساب الـ ATR لتحديد الأهداف
                    atr = (df['high'] - df['low']).mean()
                    
                    # فتح الصفقة
                    pos = engine.open_position(symbol, signal, price, atr, conf/100)
                    
                    if pos:
                        # --- 1. رسالة الرادار (احترافية كما طلبت) ---
                        sentiment = "🐂 BULL" if signal == "LONG" else "🐻 BEAR"
                        vol_type = "🔥 High Vol" if df['volume'].iloc[-1] > df['volume'].mean() else "🌊 Normal"
                        trend_str = "🚀 STRONG" if adx_val > 30 else "📈 RISING"
                        risk_lvl = "🟢 Low Risk" if conf > 90 else "🟡 Medium"
                        
                        radar_msg = (
                            f"📡 <b>RADAR SCAN</b>\n"
                            f"💎 <b>Pair:</b> {symbol}\n"
                            f"💵 <b>Price:</b> {price}\n"
                            f"🧠 <b>AI:</b> {sentiment} ({conf:.1f}%)\n"
                            f"🌊 <b>Vol:</b> {vol_type}\n"
                            f"🌍 <b>Trend:</b> {trend_str} (ADX: {adx_val:.0f})\n"
                            f"🛡️ <b>Risk:</b> {risk_lvl}\n"
                            f"🎯 <b>Target:</b> {pos['tp']:.2f}"
                        )
                        
                        # رسم الشارت وإرساله
                        chart_data = prepare_chart_data(df.tail(60))
                        img = painter.draw_entry_chart(chart_data, price, pos['sl'], pos['tp'], symbol, "ENTRY")
                        if img:
                            bot.send_photo(img, radar_msg, bot_type='news')
                            # إرسال نسخة لبوت التحكم مع السبب
                            entry_reason = f"Breakout + High ADX ({adx_val:.1f})"
                            control_msg = f"🚀 <b>New Execution</b>\n{symbol} {signal}\nReason: {entry_reason}"
                            bot.send_photo(img, control_msg, bot_type='admin')
                            img.close()

            # 2. إدارة الصفقات المفتوحة (الربح/الخسارة)
            closed = engine.manage_positions(current_prices)
            for pos, pnl, reason in closed:
                icon = "💰" if pnl > 0 else "🛑"
                msg = (
                    f"{icon} <b>Trade Closed: {pos['symbol']}</b>\n"
                    f"Result: {reason}\n"
                    f"PnL: {pnl:.2f}$\n"
                    f"New Balance: {engine.balance:.2f}$"
                )
                bot.send_admin(msg)
            
            # أوامر المستخدم (تقرير/رصيد)
            cmd = bot.check_updates()
            if cmd and "تقرير" in cmd:
                open_pos_str = "\n".join([f"- {s}: {p['type']}" for s, p in engine.positions.items()]) or "No Active Trades"
                bot.send_admin(f"📊 <b>System Report</b>\nScanning: {len(config.TARGETS)} Pairs\nActive: {open_pos_str}\nBalance: {engine.balance:.2f}$")
            
            time.sleep(10) # راحة 10 ثواني بين كل دورة مسح كاملة
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
