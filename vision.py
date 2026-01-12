# vision.py
# V26: Dynamic Chart Painter 🦅
# -------------------------------------
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import mplfinance as mpf

class ChartPainter:
    def __init__(self):
        pass

    def draw_entry_chart(self, df, entry_price, sl, tp, symbol, mode="ENTRY"):
        try:
            # إعداد الألوان والتصميم
            mc = mpf.make_marketcolors(up='#2ebd85', down='#f6465d', edge='inherit', wick='inherit', volume='in')
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
            
            # تحديد الخطوط (الدخول - الهدف - الوقف)
            hlines = dict(hlines=[entry_price, tp, sl], 
                          colors=['blue', 'green', 'red'], 
                          linewidths=[1.5, 1.5, 1.5], 
                          alpha=0.8)
            
            # عنوان الشارت الديناميكي
            title = f"{symbol} - {mode} POINT: {entry_price}"

            # إنشاء الصورة في الذاكرة
            buf = io.BytesIO()
            mpf.plot(df, type='candle', style=s, 
                     title=title,
                     hlines=hlines, 
                     volume=False, 
                     savefig=dict(fname=buf, dpi=100, bbox_inches='tight'))
            
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Vision Error: {e}")
            return None
