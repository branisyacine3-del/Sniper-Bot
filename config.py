# config.py
# إعدادات النظام المزدوج (رادار + تحكم)
# -------------------------------------
import os

# نأخذ القيم من Render
API_KEY = os.environ.get('API_KEY', "YOUR_KEY")
SECRET_KEY = os.environ.get('SECRET_KEY', "YOUR_SECRET")

# 1. بوت التحكم (يستقبل الأوامر ويرد عليك)
CONTROL_BOT_TOKEN = os.environ.get('BOT_TOKEN', "") 
CHAT_ID = os.environ.get('CHAT_ID', "")

# 2. بوت الرادار (يرسل الصفقات والتحليل فقط)
NEWS_BOT_TOKEN = os.environ.get('NEWS_BOT_TOKEN', "") # سنضيفه في Render
NEWS_CHAT_ID = CHAT_ID # يرسل لنفس الشخص (أنت)

# إعدادات التداول
TIMEFRAME = '5m'
FILTER_TIMEFRAME = '1h'
RISK_PER_TRADE = 0.02
INITIAL_CAPITAL = 100.0
CONFIDENCE_THRESHOLD = 0.60
