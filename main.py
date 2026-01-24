# main.py
# V38: ARTIFICIAL INTELLIGENCE TRADING (Dynamic Trailing Stop) 🦅
# -------------------------------------------------------------
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
import os
import gc
from datetime import datetime
import config
from telegram_bot import TelegramBot
from vision import ChartPainter

# محاولة لإبقاء الاتصال حياً
try:
    from keep_alive import keep_alive
    keep_alive()
except: pass

bot = TelegramBot()
painter = ChartPainter()

class TradingEngine:
    def __init__(self):
        self.balance = config.INITIAL_CAPITAL
        self.positions = {}
        self.history = [] 
        self.total_wins = 0
        self.total_losses = 0

    def open_position(self, symbol, type, price, atr):
        if symbol in self.positions: return None
        
        # 🧠 الذكاء الاصطناعي هنا: تحديد المجال الحيوي بناء على تذبذب السوق
        # نستخدم ATR لتحديد مساحة التنفس للصفقة
        stop_distance = atr * 2.0  # مساحة كافية لعدم الخروج المبكر
        
        if type == 'LONG': 
            sl = price - stop_distance
            # ⚠️ لاحظ: لا يوجد هدف ثابت (TP = None). السماء هي الحدود!
            tp = None 
        
        # حساب الكمية بناء على المخاطرة
        qty = (self.balance * config.NORMAL_RISK) / price
        
        pos = {
            'symbol': symbol, 
            'type': type, 
            'entry': price, 
            'qty': qty, 
            'sl': sl,     # الوقف المبدئي
            'tp': None,   # مفتوح
            'highest_price': price, # لتتبع القمة
            'atr': atr,   # نحتفظ بقيمة التذبذب لاستخدامها في التحريك
            'start_time': datetime.now()
        }
        self.positions[symbol] = pos
        return pos

    def manage_positions(self, current_prices, current_rsi):
        closed_trades = []
        active = list(self.positions.keys())
        
        for sym in active:
            pos = self.positions[sym]
            curr_price = current_prices.get(sym, 0)
            rsi = current_rsi.get(sym, 50)
            
            if curr_price == 0: continue
            
            pnl = 0; closed = False; reason = ""
            
            if pos['type'] == 'LONG':
                # 1️⃣ الذكاء في ملاحقة الربح (Trailing Stop)
                if curr_price > pos['highest_price']:
                    pos['highest_price'] = curr_price
                    # معادلة ذكية: كلما صعد السعر، ارفع الوقف ليكون تحت القمة بمسافة ATR
                    # هذا يضمن حجز الربح أولاً بأول
                    new_sl = pos['highest_price'] - (pos['atr'] * 1.5)
                    if new_sl > pos['sl']:
                        pos['sl'] = new_sl
                
                # 2️⃣ الذكاء في الخروج (RSI Exhaustion)
                # إذا وصل RSI لـ 75 (تشبع) وبدأ السعر ينزل، اخرج فوراً لا تنتظر الوقف
                rsi_exit = (rsi > 75 and curr_price < pos['highest_price'] * 0.995)

                # 3️⃣ تنفيذ الخروج
                if curr_price <= pos['sl']: 
                    pnl = (pos['sl'] - pos['entry']) * pos['qty']
                    closed = True
                    reason = "Trailing Stop (Profit Locked) 🛡️" if pnl > 0 else "Stop Loss 🛑"
                
                elif rsi_exit and (curr_price > pos['entry']): # نخرج بـ RSI فقط إذا كنا رابحين
                    pnl = (curr_price - pos['entry']) * pos['qty']
                    closed = True
                    reason = "AI Exit (RSI Overbought) 🧠"

            if closed:
                self.balance += pnl
                self.history.append({'pnl': pnl})
                if pnl > 0: self.total_wins += 1
                else: self.total_losses += 1
                closed_trades.append((pos, pnl, reason))
                del self.positions[sym]
                
        return closed_trades

def get_yahoo_data(symbol):
    try:
        yahoo_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
        df = yf.download(yahoo_symbol, period='2d', interval='5m', progress=False, auto_adjust=True)
        
        if df.empty: return None, 0.0
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.capitalize() for c in df.columns]
        
        required = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required): return None, 0.0

        price = df['Close'].iloc[-1]
        
        # حساب المؤشرات الذكية
        df.ta.adx(high='High', low='Low', close='Close', length=14, append=True)
        df.ta.rsi(close='Close', length=14, append=True)
        df.ta.atr(high='High', low='Low', close='Close', length=14, append=True)
        
        return df, price
    except:
        return None, 0.0

def run_bot():
    engine = TradingEngine()
    bot.send_admin("🦅 <b>V38: AI INTELLIGENCE ACTIVE</b>\n- Logic: Dynamic Trailing Stop 🏃\n- Target: Unlimited 🚀\n- Exit: Smart Volatility Based")
    
    last_msg_time = time.time()
    
    while True:
        try:
            cmd = bot.get_updates()
            if cmd == "💰 الرصيد":
                bot.send_admin(f"💰 Balance: {engine.balance:.2f}$")
            
            # تجميع بيانات السوق الحالية
            current_prices = {}
            current_rsi = {}
            
            # مرحلة المسح (Scanning)
            for symbol in config.TARGETS:
                try:
                    df, price = get_yahoo_data(symbol)
                    if df is None: continue
                    
                    # حفظ البيانات للإدارة
                    current_prices[symbol] = price
                    if 'RSI_14' in df.columns:
                        current_rsi[symbol] = df['RSI_14'].iloc[-1]
                    else:
                        current_rsi[symbol] = 50

                    adx = df['ADX_14'].iloc[-1]
                    
                    # شروط الدخول (Entry Logic)
                    if symbol not in engine.positions and adx > 20: # تريند بدأ يقوى
                        atr = df['ATRr_14'].iloc[-1] if 'ATRr_14' in df.columns else (price*0.01)
                        pos = engine.open_position(symbol, 'LONG', price, atr)
                        
                        if pos:
                            msg = (
                                f"🚀 <b>SMART ENTRY: {symbol}</b>\n"
                                f"💵 Price: {price:.4f}\n"
                                f"🛡️ Initial Stop: {pos['sl']:.4f}\n"
                                f"🌊 Volatility (ATR): {atr:.4f}\n"
                                f"<i>Target is OPEN. Trailing active.</i>"
                            )
                            # رسم توضيحي
                            chart_slice = df.tail(40)
                            img = painter.draw_entry_chart(chart_slice, price, pos['sl'], price*1.05, symbol, mode="ENTRY")
                            if img:
                                bot.send_photo(img, msg, bot_type='news')
                                img.close(); del img
                            else:
                                bot.send_news(msg)
                except Exception as e:
                    print(f"Scan Error {symbol}: {e}")
                    continue
                gc.collect()

            # مرحلة الإدارة الذكية (AI Management)
            closed = engine.manage_positions(current_prices, current_rsi)
            
            for pos, pnl, reason in closed:
                icon = "🤑" if pnl > 0 else "🔻"
                bot.send_news(f"{icon} <b>AI CLOSED {pos['symbol']}</b>\n💵 PnL: {pnl:.2f}$\n🧠 Logic: {reason}")
            
            # رسالة نبض كل 15 دقيقة
            if time.time() - last_msg_time > 900:
                print("🦅 AI Brain is calculating...")
                last_msg_time = time.time()

            time.sleep(3)

        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
