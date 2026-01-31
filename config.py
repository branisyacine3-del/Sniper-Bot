import os

# config.py
# V26: Invincible Configuration (Secure Mode) 🦅
# -------------------------------------

# 1. إعدادات السوق (تعدد الجبهات)
TARGETS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
TIMEFRAME = '5m'

# 2. الفلتر الدفاعي (الدرع)
ADX_THRESHOLD = 25.0       # أي تريند أضعف من 25 ممنوع الدخول فيه
CONFIDENCE_THRESHOLD = 0.80 # الذكاء الاصطناعي يجب أن يكون واثقاً فوق 80%

# 3. المحفظة الذكية (إدارة الأموال)
INITIAL_CAPITAL = 100.0    # رأس المال الافتراضي للحسابات
NORMAL_RISK = 0.02         # المخاطرة العادية (2%)
HIGH_RISK = 0.05           # المخاطرة للصفقات الذهبية (5%)
LEVERAGE = 5               # الرافعة المالية

# 4. مفاتيح النظام (يتم سحبها تلقائياً من إعدادات Render)
# تأكد أن الأسماء في Render مطابقة تماماً لما بين الأقواس هنا
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# توكن بوت التحكم وبوت الأخبار
CONTROL_BOT_TOKEN = os.getenv("8240825398:AAHK88iipy_ivrw7BsHRTTyBG0VtmwDl5D8")
NEWS_BOT_TOKEN = os.getenv("8442235395:AAE9FyBdjOrd4KMZApFM496uQ4N42iWsqWo")

# معرف الشات الخاص بك
CHAT_ID = os.getenv("7408327565")
