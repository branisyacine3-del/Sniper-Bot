import requests
import time
import json
import config

class TelegramBot:
    def __init__(self):
        # سحب التوكنات من ملف الكونفيج مباشرة
        self.control_token = config.CONTROL_BOT_TOKEN
        self.news_token = config.NEWS_BOT_TOKEN
        self.chat_id = config.CHAT_ID
        self.offset = 0

    def send_photo(self, photo_file, caption, bot_type='admin'):
        """إرسال الصور (للشارتات والتحليل)"""
        token = self.news_token if bot_type == 'news' else self.control_token
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        try:
            files = {'photo': photo_file}
            data = {'chat_id': self.chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            requests.post(url, files=files, data=data)
        except Exception as e:
            print(f"❌ خطأ في إرسال الصورة: {e}")

    def send_admin(self, text):
        """إرسال رسائل التحكم والتنبيهات الإدارية"""
        url = f"https://api.telegram.org/bot{self.control_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"❌ خطأ في إرسال رسالة الأدمن: {e}")
        
    def send_news(self, text):
        """إرسال إشارات البيع والشراء"""
        url = f"https://api.telegram.org/bot{self.news_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"❌ خطأ في إرسال الأخبار: {e}")

    def show_keyboard(self, text):
        """عرض لوحة التحكم الخاصة بالبوت الإسلامي"""
        keyboard = {
            "keyboard": [
                [{"text": "💰 الرصيد"}, {"text": "🕌 وضع حلال"}],
                [{"text": "📊 تقرير الأصول"}, {"text": "🛑 إيقاف"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        url = f"https://api.telegram.org/bot{self.control_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': text, 'reply_markup': json.dumps(keyboard)}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"❌ خطأ في عرض الكيبورد: {e}")

    def get_updates(self):
        """استقبال الأوامر من المستخدم"""
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
