# config.py
# V26: Invincible Configuration 🦅
# -------------------------------------

# 1. إعدادات السوق (تعدد الجبهات)
TARGETS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
TIMEFRAME = '5m'

# 2. الفلتر الدفاعي (الدرع)
ADX_THRESHOLD = 25.0       # أي تريند أضعف من 25 ممنوع الدخول فيه
CONFIDENCE_THRESHOLD = 0.80 # الذكاء الاصطناعي يجب أن يكون واثقاً فوق 80%

# 3. المحفظة الذكية (إدارة الأموال)
INITIAL_CAPITAL = 100.0    # رأس المال
NORMAL_RISK = 0.02         # المخاطرة العادية (2%)
HIGH_RISK = 0.05           # المخاطرة للصفقات الذهبية (5%)
LEVERAGE = 5               # الرافعة المالية (اختياري للحسابات الحقيقية)

# 4. مفاتيح النظام (لا تغيرها)
API_KEY = "YOUR_BINANCE_API_KEY"
SECRET_KEY = "YOUR_BINANCE_SECRET_KEY"
CONTROL_BOT_TOKEN = "7549306041:AAH8a... (ضع التوكن الخاص بك)"
NEWS_BOT_TOKEN = "7734139988:AAH... (ضع التوكن الخاص بك)"
CHAT_ID = "6350961806"
