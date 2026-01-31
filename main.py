# main.py
# V41: HALAL SPOT TRADER (No Dependencies) 🦅
# -------------------------------------------------------------
import ccxt
import pandas as pd  # 👈 فقط باندا العادية
import time
import schedule
from datetime import datetime
import config
from telegram_bot import TelegramBot
from ai_brain import QuantModel
# from vision import ChartPainter  <-- سنعطل الرسام مؤقتاً لتخفيف الأحمال


# تشغيل السيرفر للبقاء حياً
try:
    from keep_alive import keep_alive
    keep_alive()
except: pass

# تهيئة الأدوات
bot = TelegramBot()
brain = QuantModel()
painter = ChartPainter()

# الاتصال بالمنصة (بايننس كمثال للبيانات)
exchange = ccxt.binance({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'} # 👈 تأكيد هام: سبوت فقط
})

class HalalEngine:
    def __init__(self):
        self.usdt_balance = config.INITIAL_CAPITAL
        self.portfolio = {} # هنا نخزن العملات التي اشتريناها (Coin: Amount)
        self.history = []

    def fetch_data(self, symbol):
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=config.TIMEFRAME, limit=100)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except Exception as e:
            print(f"Data Error {symbol}: {e}")
            return None

    def execute_trade(self, symbol, signal, price, rsi):
        # 🟢 منطق الشراء (BUY SPOT)
        if signal == "BUY":
            # شرط: لا نشتري إذا كنا نملك العملة بالفعل (نمنع التكرار حالياً)
            if symbol in self.portfolio: return
            
            # شرط: هل يوجد رصيد USDT كافٍ؟
            if self.usdt_balance >= config.USDT_PER_TRADE:
                amount = config.USDT_PER_TRADE / price
                self.portfolio[symbol] = {'entry': price, 'amount': amount, 'time': datetime.now()}
                self.usdt_balance -= config.USDT_PER_TRADE
                
                msg = (f"🟢 <b>HALAL BUY: {symbol}</b>\n"
                       f"💵 Price: {price:.4f}\n"
                       f"📉 RSI: {rsi:.2f}\n"
                       f"🦅 Action: Own the asset (Spot)")
                bot.send_news(msg)
                print(msg)

        # 🔴 منطق البيع (SELL SPOT)
        elif signal == "SELL":
            # شرط: يجب أن نكون مالكين للعملة لكي نبيعها
            if symbol in self.portfolio:
                data = self.portfolio[symbol]
                # شرط ربحي: نبيع فقط بربح (أو وقف خسارة طفيف إذا انعكس السوق بقوة)
                # هنا سنجعلها بسيطة: نبيع عند الإشارة
                revenue = data['amount'] * price
                pnl = revenue - config.USDT_PER_TRADE
                
                self.usdt_balance += revenue
                del self.portfolio[symbol] # خروج من العملة
                
                icon = "💰" if pnl > 0 else "🛡️"
                msg = (f"{icon} <b>HALAL SELL: {symbol}</b>\n"
                       f"💵 Exit Price: {price:.4f}\n"
                       f"💎 PnL: {pnl:.2f} USDT\n"
                       f"⏱️ Held since: {data['time'].strftime('%H:%M')}")
                bot.send_news(msg)

    def scan_market(self):
        print(f"🦅 Scanning Market... Balance: {self.usdt_balance:.2f} USDT")
        
        for symbol in config.TARGETS:
            df = self.fetch_data(symbol)
            if df is None: continue
            
            signal, rsi = brain.analyze_market(df)
            current_price = df['close'].iloc[-1]
            
            # تنفيذ الأوامر
            self.execute_trade(symbol, signal, current_price, rsi)
            
            # تقرير لمن يملك العملة حالياً (Trailing Check)
            if symbol in self.portfolio:
                entry = self.portfolio[symbol]['entry']
                profit_pct = ((current_price - entry) / entry) * 100
                if profit_pct > 1.5: # إذا الربح تجاوز 1.5%
                     # هنا يمكن إضافة كود لرفع الوقف، لكن في السبوت ننتظر إشارة البيع من العقل
                     pass

def run_bot():
    bot.send_admin("🕌 <b>HALAL SPOT BOT STARTED</b>\n- Mode: Spot Only (No Leverage)\n- Strategy: Buy Dips, Sell Rips")
    engine = HalalEngine()
    
    # الفحص كل دقيقة (لأن السيرفر قوي)
    schedule.every(30).seconds.do(engine.scan_market)
    
    while True:
        try:
            schedule.run_pending()
            
            # تفقد أوامر تليجرام
            cmd = bot.get_updates()
            if cmd == "💰 الرصيد":
                # حساب قيمة المحفظة الكلية
                total_assets = engine.usdt_balance
                # إضافة قيمة العملات المفتوحة
                for sym, data in engine.portfolio.items():
                    # نحتاج سعر حالي تقريبي (نتجاهله هنا للسرعة ونحسب الدخول)
                    total_assets += (data['amount'] * data['entry']) # تقريبي
                
                msg = (f"💰 <b>Islamic Portfolio</b>\n"
                       f"💵 USDT Free: {engine.usdt_balance:.2f}\n"
                       f"👜 Open Assets: {len(engine.portfolio)}\n"
                       f"📊 Total Est: {total_assets:.2f} $")
                bot.send_admin(msg)
                
            time.sleep(1)
            
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
 
