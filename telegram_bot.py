# telegram_bot.py
# V27: Responsive Interface 🦅
import requests
import time

class TelegramBot:
    def __init__(self):
        import config
        self.control_token = config.CONTROL_BOT_TOKEN
        self.news_token = config.NEWS_BOT_TOKEN
        self.chat_id = config.CHAT_ID
        self.offset = 0

    def send_photo(self, photo_file, caption, bot_type='admin'):
        token = self.news_token if bot_type == 'news' else self.control_token
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        try:
            files = {'photo': photo_file}
            data = {'chat_id': self.chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            requests.post(url, files=files, data=data)
        except Exception as e:
            print(f"Send Error: {e}")

    def send_admin(self, text):
        url = f"https://api.telegram.org/bot{self.control_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        requests.post(url, data=data)
        
    def send_news(self, text):
        url = f"https://api.telegram.org/bot{self.news_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        requests.post(url, data=data)

    def show_keyboard(self, text):
        # لوحة التحكم مع الزر السابع الجديد
        keyboard = {
            "inline_keyboard": [
                [{"text": "💰 الرصيد", "callback_data": "balance"}, {"text": "📡 فحص رادار", "callback_data": "scan"}],
                [{"text": "📸 شارت فوري", "callback_data": "chart"}, {"text": "📊 تقرير شامل", "callback_data": "report"}],
                [{"text": "🏆 لوحة الأداء (New)", "callback_data": "dashboard"}], 
                [{"text": "▶️ تشغيل", "callback_data": "start"}, {"text": "🛑 إيقاف", "callback_data": "stop"}]
            ]
        }
        url = f"https://api.telegram.org/bot{self.control_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'reply_markup': str(keyboard).replace("'", '"')}
        requests.post(url, data=data)

    def get_updates(self):
        # وظيفة محسنة لجلب الضغطات
        url = f"https://api.telegram.org/bot{self.control_token}/getUpdates?offset={self.offset}&timeout=1"
        try:
            resp = requests.get(url).json()
            if "result" in resp:
                for item in resp["result"]:
                    self.offset = item["update_id"] + 1
                    # التحقق من ضغط الزر
                    if "callback_query" in item:
                        return item["callback_query"]["data"]
                    # التحقق من الرسائل النصية
                    if "message" in item and "text" in item["message"]:
                        return item["message"]["text"]
        except:
            pass
        return None
