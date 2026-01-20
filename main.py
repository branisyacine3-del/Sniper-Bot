# main.py
# V36: LIGHTWEIGHT & STABLE (Text Radar / Chart on Demand) 🦅
# --------------------------------------------------------
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
from ai_brain import QuantModel
from vision import ChartPainter
from keep_alive import keep_alive 

keep_alive()

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

    def open_position(self, symbol, type, price, atr):
        if symbol in self.positions: return None
        # إعدادات وقف الخسارة والهدف
        sl_dist = atr * 2.0
        tp_dist = atr * 4.0 # هدف طموح 1:2
        
        if type == 'LONG': 
            sl = price - sl_dist
            tp = price + tp_dist
        else: 
            sl = price + sl_dist
            tp = price - tp_dist
            
        qty = (self.balance * config.NORMAL_RISK) / price
        pos = {
            'symbol': symbol, 'type': type, 'entry': price, 
            'qty': qty, 'sl': sl, 'tp': tp, 
            'highest_price': price, 'start_time': datetime.now()
        }
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
            
            # إدارة صفقات الشراء (LONG Only for Spot/Simple Futures)
            if pos['type'] == 'LONG':
                # Trailing Stop (وقف متحرك)
                if curr > pos['highest_price']: pos['highest_price'] = curr
                if (pos['highest_price'] - pos['entry']) / pos['entry'] > 0.015: # بعد ربح 1.5%
                     pos['sl'] = max(pos['sl'], pos['entry'] * 1.005) # حجز ربح

                if curr >= pos['tp']: 
                    pnl = (pos['tp'] - pos['entry']) * pos['qty']
                    closed = True; reason = "Target Hit 🎯"
                elif curr <= pos['sl']: 
                    pnl = (pos['sl'] - pos['entry']) * pos['qty']
                    closed = True; reason = "Stop Loss 🛑"
            
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
        # 🔥 تخفيف الحمل: سحب يومين فقط بدلاً من 5
        df = yf.download(yahoo_symbol, period='2d', interval='5m', progress=False, auto_adjust=True)
        
        if df.empty: return None, 0.0

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df.columns = [c.capitalize() for c in df.columns]
        
        required = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required): return None, 0.0

        price = df['Close'].iloc[-1]
        
        # حساب المؤشرات
        df.ta.adx(high='High', low='Low', close='Close', length=14, append=True)
        df.ta.rsi(close='Close', length=14, append=True) # إضافة RSI للمساعدة في القرار
        
        return df, price
    except:
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
                    'df': df, 
                    'vol': df['Volume'].iloc[-1] if 'Volume' in df.columns else 0
                }
        except: continue
        gc.collect() # تنظيف سريع
        
    return best_data

def run_bot():
    engine = TradingEngine()
    bot.show_keyboard("🦅 <b>V36: STABLE MODE</b>\n- Auto Radar: Text Only 📝\n- Charts: On Demand/Entry 📸\n- Data: 2 Days (Fast)")
    
    last_radar_time = time.time() - 180 
    
    while True:
        try:
            # 1. الأوامر اليدوية (مسموح فيها بالصور)
            cmd = bot.get_updates()
            
            if cmd == "💰 الرصيد":
                bot.send_admin(f"💰 Balance: {engine.balance:.2f}$")
                
            elif cmd == "📊 تقرير شامل":
                active_str = "\n".join([f"{s}: {p['type']}" for s, p in engine.positions.items()]) or "Empty"
                bot.send_admin(f"📊 <b>Report</b>\nActive: {active_str}\nWins: {engine.total_wins} | Loss: {engine.total_losses}")
                
            elif cmd == "🏆 لوحة الأداء":
                # رسم اللوحة خفيف نسبياً
                total = engine.total_wins + engine.total_losses
                win_rate = (engine.total_wins / total * 100) if total > 0 else 0
                pnl_total = sum([h['pnl'] for h in engine.history])
                img = painter.draw_performance_dashboard(win_rate, total, pnl_total)
                if img:
                    bot.send_photo(img, f"🏆 <b>Performance</b>\nWin Rate: {win_rate:.1f}%", bot_type='admin')
                    img.close()
                    del img
            
            elif cmd == "📡 فحص رادار" or cmd == "📸 شارت فوري":
                # هنا فقط نسمح برسم الشارت عند الطلب
                data = get_best_market_opportunity()
                if data:
                    chart_slice = data['df'].tail(40) # 40 شمعة فقط للسرعة
                    target = data['price'] * 1.01
                    msg = f"📡 <b>SCAN</b>: {data['symbol']} | ADX: {data['adx']:.1f}"
                    img = painter.draw_entry_chart(chart_slice, data['price'], data['price']*0.99, target, data['symbol'], mode="SCAN")
                    if img:
                        bot.send_photo(img, msg, bot_type='admin')
                        img.close()
                        del img
                    del data

            # 2. البحث عن صفقات (SNIPER ENTRY)
            # ----------------------------------
            for symbol in config.TARGETS:
                try:
                    df, price = get_yahoo_data(symbol)
                    if df is None: continue
                    
                    # استراتيجية مخففة للدخول:
                    # ADX > 20 (بدلاً من 25 لزيادة الفرص) + RSI ليس متشبعاً
                    adx = df['ADX_14'].iloc[-1]
                    rsi = df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns else 50
                    
                    if symbol not in engine.positions and adx > 20 and 30 < rsi < 70:
                        # دخول بسيط يعتمد على قوة التريند
                        atr = (df['High'] - df['Low']).mean()
                        pos = engine.open_position(symbol, 'LONG', price, atr)
                        
                        if pos:
                            # 🔥 هنا نرسل الصورة واااااجب (للاحتفال بالصفقة)
                            chart_slice = df.tail(50)
                            msg = (
                                f"🚀 <b>EXECUTION</b>\n"
                                f"💎 <b>{symbol} - LONG</b>\n"
                                f"💵 Entry: {price:.4f}\n"
                                f"📈 ADX: {adx:.1f} (Strong)\n"
                                f"🎯 TP: {pos['tp']:.4f} | 🛑 SL: {pos['sl']:.4f}"
                            )
                            img = painter.draw_entry_chart(chart_slice, price, pos['sl'], pos['tp'], symbol, mode="ENTRY")
                            if img:
                                bot.send_photo(img, msg, bot_type='news') # إرسال للقناة
                                img.close()
                                del img
                except: continue
                gc.collect()

            # 3. الرادار التلقائي (نص فقط - لتوفير الذاكرة)
            # ---------------------------------------------
            if time.time() - last_radar_time > 180: # كل 3 دقائق
                data = get_best_market_opportunity()
                if data:
                    trend_icon = "🔥" if data['adx'] > 25 else "📈"
                    msg = (
                        f"📡 <b>MARKET PULSE</b>\n"
                        f"Top Asset: <b>{data['symbol']}</b>\n"
                        f"Price: {data['price']:.4f}\n"
                        f"Trend: {data['adx']:.1f} {trend_icon}\n"
                        f"<i>(Chart available on entry or manual request)</i>"
                    )
                    bot.send_news(msg) # نص فقط
                    
                    del data
                    last_radar_time = time.time()
                    gc.collect()

            # 4. إدارة الصفقات المفتوحة
            current_prices = {}
            for symbol in config.TARGETS:
                _, price = get_yahoo_data(symbol)
                if price > 0: current_prices[symbol] = price
            
            closed = engine.manage_positions(current_prices)
            for pos, pnl, reason in closed:
                icon = "✅" if pnl > 0 else "❌"
                bot.send_news(f"{icon} <b>CLOSED {pos['symbol']}</b>\nPnL: {pnl:.2f}$\nReason: {reason}")
            
            del current_prices
            gc.collect()
            
            time.sleep(2)

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
 
