# main.py
# V34: MEMORY GUARD EDITION (Stable) 🦅
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
import os
import gc # استدعاء عامل النظافة
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

    def open_position(self, symbol, type, price, atr, confidence):
        if symbol in self.positions: return None
        sl_dist = atr * 2.0
        tp_dist = atr * 4.0
        if type == 'LONG': sl = price - sl_dist; tp = price + tp_dist
        else: sl = price + sl_dist; tp = price - tp_dist
        qty = (self.balance * config.NORMAL_RISK) / price
        pos = {'symbol': symbol, 'type': type, 'entry': price, 'qty': qty, 'sl': sl, 'tp': tp, 'highest_price': price}
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
                self.history.append({'pnl': pnl})
                if pnl > 0: self.total_wins += 1
                else: self.total_losses += 1
                closed_trades.append((pos, pnl, reason))
                del self.positions[sym]
        return closed_trades

def get_yahoo_data(symbol):
    try:
        yahoo_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
        df = yf.download(yahoo_symbol, period='1d', interval='5m', progress=False, auto_adjust=True)
        if df.empty: return None, 0.0
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.capitalize() for c in df.columns]
        required = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required): return None, 0.0
        price = df['Close'].iloc[-1]
        df.ta.adx(high='High', low='Low', close='Close', length=14, append=True)
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
                best_data = {'symbol': symbol, 'price': price, 'adx': adx, 'df': df, 'vol': df['Volume'].iloc[-1] if 'Volume' in df.columns else 0}
        except: continue
        
        # تنظيف جزئي داخل الحلقة
        gc.collect()
        
    return best_data

def run_bot():
    engine = TradingEngine()
    bot.show_keyboard("🦅 <b>V34: MEMORY OPTIMIZED</b>\n- Cycle: 3 Minutes ⏳\n- RAM: Protected 🛡️")
    
    last_radar_time = time.time() - 180 
    
    while True:
        try:
            cmd = bot.get_updates()
            
            if cmd == "💰 الرصيد":
                bot.send_admin(f"💰 Balance: {engine.balance:.2f}$")
                
            elif cmd == "📊 تقرير شامل":
                active_str = "\n".join([f"{s}: {p['type']}" for s, p in engine.positions.items()]) or "Empty"
                bot.send_admin(f"📊 <b>Report</b>\nActive: {active_str}\nWins: {engine.total_wins} | Loss: {engine.total_losses}")
                
            elif cmd == "🏆 لوحة الأداء":
                total = engine.total_wins + engine.total_losses
                win_rate = (engine.total_wins / total * 100) if total > 0 else 0
                pnl_total = sum([h['pnl'] for h in engine.history])
                img = painter.draw_performance_dashboard(win_rate, total, pnl_total)
                if img:
                    bot.send_photo(img, f"🏆 <b>Performance</b>\nWin Rate: {win_rate:.1f}%", bot_type='admin')
                    img.close()
                    del img # حذف من الذاكرة
            
            elif cmd == "📡 فحص رادار" or cmd == "📸 شارت فوري":
                data = get_best_market_opportunity()
                if data:
                    trend_icon = "🚀 STRONG" if data['adx'] > 25 else "📈 RISING"
                    atr = (data['df']['High'] - data['df']['Low']).mean()
                    target = data['price'] + (atr * 4)
                    
                    msg = (
                        f"📡 <b>MANUAL SCAN</b>\n"
                        f"💎 <b>{data['symbol']}</b> | 💵 <b>{data['price']:.4f}</b>\n"
                        f"🌍 <b>Trend:</b> {trend_icon} (ADX: {data['adx']:.0f})\n"
                        f"🎯 <b>Target:</b> {target:.2f}"
                    )
                    
                    img = painter.draw_entry_chart(data['df'], data['price'], data['price']*0.98, target, data['symbol'], mode="SCAN")
                    if img:
                        bot.send_photo(img, msg, bot_type='admin')
                        img.close()
                        del img
                    else:
                        bot.send_admin(msg)
                    
                    # تنظيف البيانات الكبيرة
                    del data
            
            # الرادار التلقائي (كل 180 ثانية = 3 دقائق) لتخفيف الحمل
            if time.time() - last_radar_time > 180:
                data = get_best_market_opportunity()
                if data:
                    trend_icon = "🚀 STRONG" if data['adx'] > 25 else "📈 RISING"
                    atr = (data['df']['High'] - data['df']['Low']).mean()
                    target = data['price'] + (atr * 4)

                    msg = (
                        f"📡 <b>RADAR (3m)</b>\n"
                        f"💎 <b>{data['symbol']}</b>\n"
                        f"💵 <b>{data['price']:.4f}</b>\n"
                        f"🌍 <b>Trend:</b> {trend_icon} (ADX: {data['adx']:.0f})\n"
                        f"🎯 <b>Target:</b> {target:.2f}"
                    )
                    
                    img = painter.draw_entry_chart(data['df'], data['price'], data['price']*0.98, target, data['symbol'], mode="RADAR")
                    if img:
                        bot.send_photo(img, msg, bot_type='news')
                        img.close()
                        del img
                    
                    del data # حذف البيانات الضخمة
                    last_radar_time = time.time()
                    
                    # 🗑️ التفريغ الكبير للذاكرة بعد كل دورة رادار
                    gc.collect() 

            # إدارة التداول
            current_prices = {}
            for symbol in config.TARGETS:
                _, price = get_yahoo_data(symbol)
                if price > 0: current_prices[symbol] = price
            engine.manage_positions(current_prices)
            
            # تنظيف المتغيرات المؤقتة
            del current_prices
            gc.collect()
            
            time.sleep(1.5)

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
