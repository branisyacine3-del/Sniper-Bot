import os

# config.py
# V40: Halal Spot Configuration 🦅🕌
# -------------------------------------

# 1. القائمة البيضاء (العملات الحلال والقوية فقط)
# نتداول USDT لأننا نشتري العملة به (Spot)
TARGETS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'MATIC/USDT', 'ADA/USDT']
TIMEFRAME = '15m'  # الفريم الربع ساعة أفضل للسبوت لتقليل الضوضاء

# 2. فلتر السيولة (Spot Needs Volume)
MIN_VOLUME_USDT = 100000  # العملة يجب أن يكون فيها سيولة كافية

# 3. إدارة رأس المال (بدون رافعة)
INITIAL_CAPITAL = 100.0    # المبلغ التجريبي
USDT_PER_TRADE = 15.0      # المبلغ المخصص لكل صفقة (مثلاً 15 دولار)
# ملاحظة: في السبوت لا توجد رافعة LEVERAGE = 1 تلقائياً

# 4. المفاتيح (تسحب من البيئة أو توضع هنا للتجربة)
API_KEY = os.getenv("API_KEY", "ZoaVcxC2owmMJY1x1BLRrV9zxhxlgPpnw94QY2vVCOpCRhnwjEM2G1f8LBvVJ6rP")
SECRET_KEY = os.getenv("SECRET_KEY", "h0nxkM47tJ7hDBVsoZTVihdguVcybKkpszP1YKTuLf8nzmwjy7Pp9JZkSmIshjaL")

# مفاتيح تليجرام
CONTROL_BOT_TOKEN = "8240825398:AAHK88iipy_ivrw7BsHRTTyBG0VtmwDl5D8"
NEWS_BOT_TOKEN = "8442235395:AAE9FyBdjOrd4KMZApFM496uQ4N42iWsqWo"
CHAT_ID = "7408327565"
