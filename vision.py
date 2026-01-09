# vision.py
# نظام الرسم البياني مع إصلاح الذاكرة (Memory Leak Fix)
# -------------------------------------
import matplotlib
matplotlib.use('Agg') # وضع عدم العرض لتوفير الذاكرة
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import io
import gc

class ChartPainter:
    def draw_entry_chart(self, df, entry, sl, tp, title_type="ENTRY"):
        buf = io.BytesIO()
        try:
            # تنظيف مسبق صارم
            plt.close('all')
            
            # إعداد الألوان
            mc = mpf.make_marketcolors(up='#2ebd85', down='#f6465d', edge='inherit', wick='inherit', volume='in')
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
            
            # تحديد العنوان واللون
            if title_type == "ENTRY":
                title = f"SNIPER ENTRY: {entry}"
                line_color = 'blue'
            elif title_type == "RADAR":
                title = f"Target: RADAR @ {entry}"
                line_color = 'green'
            else:
                title = f"MARKET CHECK: {entry}"
                line_color = 'gray'

            # إضافة خط الدخول
            addplots = [
                mpf.make_addplot([entry]*len(df), color=line_color, width=1, linestyle='-'),
            ]
            
            # الرسم
            mpf.plot(
                df, type='candle', style=s, title=title,
                ylabel='Price', volume=False, 
                savefig=dict(fname=buf, dpi=60, bbox_inches='tight', format='png'), # جودة متوسطة للسرعة
                addplot=addplots,
                num_panels=1,
                closefig=True # إغلاق الشكل فوراً
            )
            
            buf.seek(0)
            return buf
            
        except Exception as e:
            print(f"Vision Error: {e}")
            return None
        finally:
            # تنظيف نهائي إجباري
            plt.close('all')
            gc.collect()
