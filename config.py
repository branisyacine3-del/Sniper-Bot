# config.py
# ملف الإعدادات - النسخة الآمنة لـ GitHub
# -------------------------------------

# اترك هذه القيم كما هي الآن (سندخل المفاتيح الحقيقية في إعدادات السيرفر لاحقاً)
API_KEY = "RENDER_ENV_VAR"
SECRET_KEY = "RENDER_ENV_VAR"
BOT_TOKEN = "RENDER_ENV_VAR"
CHAT_ID = "RENDER_ENV_VAR"

# إعدادات التداول
TIMEFRAME = '5m'         # الفريم الزمني الأساسي
FILTER_TIMEFRAME = '1h'  # فريم الفلترة (الاتجاه العام)
RISK_PER_TRADE = 0.02    # المخاطرة 2% من الرصيد
INITIAL_CAPITAL = 100.0  # رصيد المحاكاة
CONFIDENCE_THRESHOLD = 0.60 # نسبة ثقة الذكاء المطلوبة
