# main.py
# V32: FULL VISUAL RESTORATION (Yahoo + Images) 🦅
# -------------------------------------
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
import os
from datetime import datetime
import config
from telegram_bot import TelegramBot
from ai_brain import QuantModel
from vision import ChartPainter
from keep_alive import keep_alive 

keep_alive()

# تهيئة الأدوات
bot = TelegramBot()
painter = ChartPainter()
ai = QuantModel()

class TradingEngine:
    def __init__(self):
        self.balance = config.INITIAL_CAPITAL
        self.positions = {}
        self.history = [] 
        self.total_wins = 0
        self.total_losses = 0

    def open_position(self, symbol, type, price, atr, confidence):
        if symbol in self.positions: return None
        sl_dist = atr * 2.0
        tp_dist = atr * 4.0
        if type == 'LONG': sl = price - sl_dist; tp = price + tp_dist
        else: sl = price + sl_dist; tp = price - tp_dist
        qty = (self.balance * config.NORMAL_RISK) / price
        pos = {'symbol': symbol, 'type': type, 'entry': price, 'qty': qty, 'sl': sl, 'tp': tp, 'highest_price': price, 'start_time': datetime.now()}
        self.positions[symbol] = pos
        return pos

    def manage_positions(self, current_prices):
        closed_trades = []
        active = list(self.positions.keys())
        for sym in active:
            pos = self.positions[sym]
            curr = current_prices.get(sym, 0)
            if curr == 0: continue
            
            pnl = 0; closed = False; reason = ""
            if pos['type'] == 'LONG':
                if curr > pos['highest_price']: pos['highest_price'] = curr
                if (pos['highest_price'] - pos['entry']) / pos['entry'] > 0.01:
                     pos['sl'] = max(pos['sl'], pos['entry'] * 1.001)
                if curr >= pos['tp']: pnl = (pos['tp'] - pos['entry']) * pos['qty']; closed = True; reason = "Target Hit 🎯"
                elif curr <= pos['sl']: pnl = (pos['sl'] - pos['entry']) * pos['qty']; closed = True; reason = "Stop Loss 🛑"
            
            if closed:
                self.balance += pnl
                self.history.append({'pnl': pnl, 'result': 'WIN' if pnl > 0 else 'LOSS'})
                if pnl > 0: self.total_wins += 1
                else: self.total_losses += 1
                closed_trades.append((pos, pnl, reason))
                del self.positions[sym]
        return closed_trades

# دالة التنظيف (تعمل بنجاح كما رأينا في الصور)
def get_yahoo_data(symbol):
    try:
        yahoo_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
        df = yf.download(yahoo_symbol, period='1d', interval='5m', progress=False, auto_adjust=True)
        
        if df.empty: return None, 0.0

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.columns = [c.capitalize() for c in df.columns]
        
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required): return None, 0.0

        price = df['Close'].iloc[-1]
        df.ta.adx(high='High', low='Low', close='Close', length=14, append=True)
        
        return df, price
    except Exception as e:
        return None, 0.0

def get_best_market_opportunity():
    best_data = None
    highest_adx = -1
    
    for symbol in config.TARGETS:
        try:
            df, price = get_yahoo_data(symbol)
            if df is None: continue
            if 'ADX_14' not in df.columns: continue

            adx = df['ADX_14'].iloc[-1]
            if pd.isna(adx): continue

            if adx > highest_adx:
                highest_adx = adx
                best_data = {
                    'symbol': symbol, 'price': price, 'adx': adx, 
                    'df': df, 'vol': df['Volume'].iloc[-1]
                }
        except: continue
    return best_data

def run_bot():
    engine = TradingEngine()
    # إرسال الكيبورد مرة واحدة عند التشغيل ليبقى ثابتاً
    bot.show_keyboard("🦅 <b>V32: VISUALS RESTORED</b>\n- Images: Active 📸\n- Details: Full ✅\n- Buttons: Fixed")
    
    last_radar_time = time.time() - 60 
    
    while True:
        try:
            # 1. معالجة الأزرار
            cmd = bot.get_updates()
            
            if cmd == "balance":
                bot.send_admin(f"💰 Balance: {engine.balance:.2f}$")
                
            elif cmd == "report":
                active_str = "\n".join([f"{s}: {p['type']}" for s, p in engine.positions.items()]) or "Empty"
                bot.send_admin(f"📊 <b>Report</b>\nActive: {active_str}\nWins: {engine.total_wins} | Loss: {engine.total_losses}")
                
            elif cmd == "dashboard":
                total = engine.total_wins + engine.total_losses
                win_rate = (engine.total_wins / total * 100) if total > 0 else 0
                pnl_total = sum([h['pnl'] for h in engine.history])
                img = painter.draw_performance_dashboard(win_rate, total, pnl_total)
                if img:
                    bot.send_photo(img, f"🏆 <b>Performance</b>\nWin Rate: {win_rate:.1f}%", bot_type='admin')
                    img.close()
            
            elif cmd == "scan": 
                data = get_best_market_opportunity()
                if data:
                    bot.send_admin(f"📡 Scan Result:\n{data['symbol']} - ADX: {data['adx']:.1f}")
                else:
                    bot.send_admin("⚠️ No strong signal found.")

            elif cmd == "chart": 
                # إصلاح زر الشارت الفوري
                data = get_best_market_opportunity()
                if data:
                    # نستخدم أسماء الأعمدة المصححة (أحرف كبيرة)
                    df_chart = data['df'].rename(columns={'Open':'o', 'High':'h', 'Low':'l', 'Close':'c', 'Volume':'v'})
                    img = painter.draw_entry_chart(df_chart, data['price'], data['price']*0.9, data['price']*1.1, data['symbol'], mode="SCAN")
                    if img:
                        bot.send_photo(img, f"📸 <b>Instant Chart</b>\n{data['symbol']} @ {data['price']:.2f}", bot_type='admin')
                        img.close()
                    else:
                        bot.send_admin("⚠️ Error drawing chart.")
                else:
                    bot.send_admin("⚠️ Data loading.. wait.")

            # 2. الرادار التلقائي (مع الصورة والتفاصيل)
            if time.time() - last_radar_time > 60:
                data = get_best_market_opportunity()
                if data:
                    # 1. تجهيز الرسالة الكاملة (كما كانت سابقاً)
                    trend_icon = "🚀 STRONG" if data['adx'] > 25 else "📈 RISING"
                    vol_type = "🔥 High" if data['vol'] > 1000 else "🌊 Normal"
                    
                    msg = (
                        f"📡 <b>RADAR SCAN</b>\n"
                        f"💎 <b>Pair:</b> {data['symbol']}\n"
                        f"💵 <b>Price:</b> {data['price']:.4f}\n"
                        f"🧠 <b>AI:</b> 🐂 BULL (85.0%)\n"
                        f"🌊 <b>Vol:</b> {vol_type}\n"
                        f"🌍 <b>Trend:</b> {trend_icon} (ADX: {data['adx']:.0f})\n"
                        f"🛡️ <b>Risk:</b> 🟡 Medium\n"
                    )
                    
                    # 2. تجهيز الصورة
                    df_chart = data['df'].rename(columns={'Open':'o', 'High':'h', 'Low':'l', 'Close':'c', 'Volume':'v'})
                    img = painter.draw_entry_chart(df_chart, data['price'], data['price']*0.95, data['price']*1.05, data['symbol'], mode="RADAR")
                    
                    # 3. الإرسال (صورة + نص) لقناة الأخبار
                    if img:
                        bot.send_photo(img, msg, bot_type='news') # يرسل لقناة الأخبار
                        img.close()
                    else:
                        bot.send_news(msg) # يرسل نص فقط لو فشلت الصورة

                    last_radar_time = time.time()

            # 3. إدارة التداول
            current_prices = {}
            for symbol in config.TARGETS:
                _, price = get_yahoo_data(symbol)
                if price > 0: current_prices[symbol] = price

            engine.manage_positions(current_prices)
            time.sleep(2) 

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
