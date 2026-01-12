# main.py
# V28: DATA STREAM FIXED (Binance Source) 🦅
# -------------------------------------
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import io
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

# التغيير الجوهري: استخدام Binance لجلب البيانات (أكثر استقراراً)
market = ccxt.binance({'options': {'adjustForTimeDifference': True}})
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

# دالة جلب البيانات (تم تحسينها لتجاوز الأخطاء)
def get_best_market_opportunity():
    best_data = None
    highest_adx = -1
    error_msg = ""
    
    for symbol in config.TARGETS:
        try:
            # جلب الشموع من بينانس
            bars = market.fetch_ohlcv(symbol, config.TIMEFRAME, limit=60)
            if not bars: continue
            
            df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
            
            # التأكد من وجود بيانات كافية للمؤشرات
            if len(df) < 20: continue

            df.ta.adx(length=14, append=True)
            
            # التعامل مع احتمال نقص البيانات
            if 'ADX_14' not in df.columns: continue
            
            adx = df['ADX_14'].iloc[-1]
            price = df['c'].iloc[-1]
            
            # تجاهل القيم غير الموجودة (NaN)
            if pd.isna(adx): continue

            if adx > highest_adx:
                highest_adx = adx
                best_data = {
                    'symbol': symbol, 'price': price, 'adx': adx, 
                    'df': df, 'vol': df['v'].iloc[-1]
                }
        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching {symbol}: {e}")
            continue
            
    return best_data, error_msg

def run_bot():
    engine = TradingEngine()
    bot.show_keyboard("🦅 <b>V28: CONNECTED TO BINANCE</b>\n- Data Stream: Stable 🟢\n- Auto Radar: Active")
    
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
                data, err = get_best_market_opportunity()
                if data:
                    msg = f"📡 <b>Manual Scan</b>\nTop: {data['symbol']}\nADX: {data['adx']:.1f}\nPrice: {data['price']}"
                    bot.send_admin(msg)
                else:
                    # الآن سيخبرك بالسبب الحقيقي للخطأ
                    bot.send_admin(f"⚠️ Data Error: {err if err else 'No strong targets'}")

            elif cmd == "chart": 
                data, _ = get_best_market_opportunity()
                if data:
                    img = painter.draw_entry_chart(data['df'], data['price'], data['price']*0.9, data['price']*1.1, data['symbol'], mode="SCAN")
                    if img:
                        bot.send_photo(img, f"📸 <b>Instant Chart</b>\n{data['symbol']} @ {data['price']}", bot_type='admin')
                        img.close()

            # 2. الرادار التلقائي
            if time.time() - last_radar_time > 60:
                data, _ = get_best_market_opportunity()
                if data:
                    trend_icon = "🔥" if data['adx'] > 25 else "💤"
                    msg = (
                        f"📡 <b>RADAR PULSE (1m)</b>\n"
                        f"💎 Pair: <b>{data['symbol']}</b>\n"
                        f"💵 Price: {data['price']}\n"
                        f"📈 Trend Strength: {data['adx']:.1f} {trend_icon}\n"
                        f"🌊 Vol: {'High' if data['vol'] > 1000 else 'Normal'}"
                    )
                    bot.send_news(msg) 
                    last_radar_time = time.time()

            # 3. إدارة التداول
            current_prices = {}
            # هنا نستخدم دورة سريعة لجلب الأسعار الحالية فقط
            for symbol in config.TARGETS:
                try:
                    ticker = market.fetch_ticker(symbol)
                    current_prices[symbol] = ticker['last']
                except: continue

            engine.manage_positions(current_prices)
            time.sleep(1) 

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
