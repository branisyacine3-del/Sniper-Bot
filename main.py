# main.py
# V27: THE COMMANDER (Non-Stop Radar + Dashboard) 🦅
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

# تهيئة المتغيرات العالمية
bot = TelegramBot()
painter = ChartPainter()
engine = None # سيتم تعريفه لاحقاً

class TradingEngine:
    def __init__(self):
        self.balance = config.INITIAL_CAPITAL
        self.positions = {}
        self.history = [] # سجل الصفقات المغلقة (للإحصائيات)
        self.total_wins = 0
        self.total_losses = 0

    def open_position(self, symbol, type, price, atr, confidence):
        if symbol in self.positions: return None
        
        sl_dist = atr * 2.0
        tp_dist = atr * 4.0
        
        if type == 'LONG':
            sl = price - sl_dist; tp = price + tp_dist
        else:
            sl = price + sl_dist; tp = price - tp_dist
            
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
            
            # الوقف المتحرك
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

def run_bot():
    market = ccxt.kucoin()
    engine = TradingEngine()
    ai = QuantModel()
    
    bot.show_keyboard("🦅 <b>V27: COMMANDER ONLINE</b>\n- Radar: Non-Stop Scan\n- Dashboard: Active\n- Buttons: Fixed")
    
    last_radar_time = 0 # توقيت آخر رسالة للرادار
    
    while True:
        try:
            # 1. التحقق من الأزرار (أولوية قصوى)
            cmd = bot.get_updates()
            if cmd:
                if cmd == "balance":
                    bot.send_admin(f"💰 Balance: {engine.balance:.2f}$")
                elif cmd == "report":
                    active_str = "\n".join([f"{s}: {p['type']}" for s, p in engine.positions.items()]) or "Empty"
                    bot.send_admin(f"📊 <b>Report</b>\nActive: {active_str}\nPNL: {sum([h['pnl'] for h in engine.history]):.2f}$")
                elif cmd == "dashboard":
                    # كود الزر السابع (رسم العداد)
                    total = engine.total_wins + engine.total_losses
                    win_rate = (engine.total_wins / total * 100) if total > 0 else 0
                    pnl_total = sum([h['pnl'] for h in engine.history])
                    img = painter.draw_performance_dashboard(win_rate, total, pnl_total)
                    if img:
                        bot.send_photo(img, f"🏆 <b>Performance</b>\nWin Rate: {win_rate:.1f}%", bot_type='admin')
                        img.close()
            
            # 2. مسح السوق
            current_prices = {}
            best_scan = None
            highest_adx = 0

            for symbol in config.TARGETS:
                try:
                    bars = market.fetch_ohlcv(symbol, config.TIMEFRAME, limit=100)
                    df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    df.ta.adx(length=14, append=True)
                    price = float(bars[-1][4])
                    current_prices[symbol] = price
                    
                    adx = df['ADX_14'].iloc[-1]
                    
                    # حفظ أقوى عملة لإرسالها للرادار لاحقاً
                    if adx > highest_adx:
                        highest_adx = adx
                        best_scan = {'symbol': symbol, 'price': price, 'adx': adx, 'vol': df['v'].iloc[-1]}

                    # منطق الدخول في الصفقة (كما هو)
                    if symbol not in engine.positions and adx > config.ADX_THRESHOLD:
                        pred, conf = ai.predict(df)
                        if conf > config.CONFIDENCE_THRESHOLD * 100:
                            atr = (df['h'] - df['l']).mean()
                            signal = "LONG" if pred == 1 else "SHORT"
                            pos = engine.open_position(symbol, signal, price, atr, conf/100)
                            if pos:
                                img = painter.draw_entry_chart(df, price, pos['sl'], pos['tp'], symbol)
                                bot.send_photo(img, f"🚀 <b>EXECUTION</b>\n{symbol} {signal}\nReason: ADX {adx:.1f}", 'admin')

                except: continue

            # 3. إرسال الرادار (كل دقيقة) - حتى لو لم ندخل صفقة
            if time.time() - last_radar_time > 60: # كل 60 ثانية
                if best_scan:
                    trend_icon = "🔥" if best_scan['adx'] > 30 else "💤"
                    msg = (
                        f"📡 <b>RADAR PULSE</b>\n"
                        f"👁️ Scanned: {len(config.TARGETS)} Pairs\n"
                        f"⭐ Top Mover: <b>{best_scan['symbol']}</b>\n"
                        f"📈 ADX: {best_scan['adx']:.1f} {trend_icon}\n"
                        f"💵 Price: {best_scan['price']}"
                    )
                    bot.send_news(msg)
                    last_radar_time = time.time()

            # 4. إدارة الصفقات
            closed = engine.manage_positions(current_prices)
            for pos, pnl, reason in closed:
                bot.send_admin(f"💰 Closed {pos['symbol']}: {pnl:.2f}$ ({reason})")

            time.sleep(2) # تقليل وقت الانتظار لتسريع الأزرار

        except Exception as e:
            print(e)
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
