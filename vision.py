# vision.py
# V34: MEMORY OPTIMIZED PAINTER 🦅
import matplotlib
matplotlib.use('Agg') # مهم جداً للسيرفرات لتقليل الاستهلاك
import matplotlib.pyplot as plt
import io
import mplfinance as mpf
import pandas as pd
import gc

class ChartPainter:
    def __init__(self):
        pass

    def draw_entry_chart(self, df, entry_price, sl, tp, symbol, mode="ENTRY"):
        try:
            # تنظيف استباقي
            plt.close('all')
            gc.collect()

            # تجهيز البيانات
            df_plot = df.copy()
            df_plot.columns = [c.capitalize() for c in df_plot.columns]
            if df_plot.index.tz is not None:
                df_plot.index = df_plot.index.tz_localize(None)
            df_plot.index.name = 'Date'

            # الإعدادات
            mc = mpf.make_marketcolors(up='#2ebd85', down='#f6465d', edge='inherit', wick='inherit', volume='in')
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
            
            hlines = dict(hlines=[entry_price, tp, sl], 
                          colors=['blue', 'green', 'red'], 
                          linewidths=[1.5, 1.5, 1.5], alpha=0.8)
            
            title = f"{symbol} - {mode}: {entry_price:.4f}"
            
            buf = io.BytesIO()
            # الرسم مع إغلاق الفوري
            fig, axlist = mpf.plot(df_plot, type='candle', style=s, title=title,
                     hlines=hlines, volume=False, 
                     savefig=dict(fname=buf, dpi=80, bbox_inches='tight'), returnfig=True) # خفضنا الدقة لـ 80 لتوفير الذاكرة
            
            # 🧹 تنظيف الذاكرة اليدوي (مهم جداً)
            for ax in axlist:
                ax.clear()
            fig.clear()
            plt.close(fig)
            plt.close('all')
            del df_plot
            gc.collect()

            buf.seek(0)
            return buf
        except Exception as e:
            print(f"Vision Error: {e}")
            plt.close('all')
            return None

    def draw_performance_dashboard(self, win_rate, total_trades, pnl):
        try:
            plt.close('all')
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.set_facecolor('black')
            fig.patch.set_facecolor('black')
            
            color = '#2ebd85' if win_rate >= 50 else '#f6465d'
            ax.barh([0], [win_rate], color=color, height=0.5)
            ax.barh([0], [100], color='#333333', height=0.5, zorder=0)
            
            ax.text(50, 0, f"{win_rate:.1f}% Win Rate", color='white', ha='center', va='center', fontsize=15, fontweight='bold')
            status = "🔥 ON FIRE!" if win_rate > 70 else "🤖 ACTIVE"
            ax.text(50, 0.4, status, color='yellow', ha='center', fontsize=12, fontweight='bold')
            info_text = f"Trades: {total_trades} | PnL: {pnl:.2f}$"
            ax.text(50, -0.4, info_text, color='white', ha='center', fontsize=10)

            ax.set_xlim(0, 100); ax.set_ylim(-1, 1); ax.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='black', dpi=80)
            
            # تنظيف
            plt.close(fig)
            plt.close('all')
            gc.collect()

            buf.seek(0)
            plt.close()
            return buf
        except Exception as e:
            plt.close('all')
            return None
