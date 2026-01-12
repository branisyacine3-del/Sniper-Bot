# telegram_bot.py
# V33: Classic Keyboard Layout 🦅
import requests
import time
import json

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
            print(f"Send Photo Error: {e}")

    def send_admin(self, text):
        url = f"https://api.telegram.org/bot{self.control_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        requests.post(url, data=data)
        
    def send_news(self, text):
        url = f"https://api.telegram.org/bot{self.news_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        requests.post(url, data=data)

    def show_keyboard(self, text):
        # هنا التغيير: استخدام keyboard بدلاً من inline_keyboard لتثبيت الأزرار بالأسفل
        keyboard = {
            "keyboard": [
                [{"text": "💰 الرصيد"}, {"text": "📡 فحص رادار"}],
                [{"text": "📸 شارت فوري"}, {"text": "📊 تقرير شامل"}],
                [{"text": "🏆 لوحة الأداء"}], 
                [{"text": "▶️ تشغيل"}, {"text": "🛑 إيقاف"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        url = f"https://api.telegram.org/bot{self.control_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'reply_markup': json.dumps(keyboard)}
        requests.post(url, data=data)

    def get_updates(self):
        url = f"https://api.telegram.org/bot{self.control_token}/getUpdates?offset={self.offset}&timeout=1"
        try:
            resp = requests.get(url).json()
            if "result" in resp:
                for item in resp["result"]:
                    self.offset = item["update_id"] + 1
                    if "message" in item and "text" in item["message"]:
                        return item["message"]["text"]
        except:
            pass
        return None
