# telegram_bot.py
# نسخة تثبيت الأزرار (Persistent Keyboard)
# -------------------------------------
import requests
import json
import config

class TelegramBot:
    def __init__(self):
        # إعداد بوت التحكم
        self.control_token = config.CONTROL_BOT_TOKEN
        self.control_url = f"https://api.telegram.org/bot{self.control_token}/"
        
        # إعداد بوت الرادار
        self.news_token = config.NEWS_BOT_TOKEN
        self.news_url = f"https://api.telegram.org/bot{self.news_token}/"
        
        self.chat_id = config.CHAT_ID
        self.offset = 0

        # تصميم لوحة المفاتيح الثابتة
        self.keyboard = json.dumps({
            "keyboard": [
                ["💰 الرصيد", "📡 فحص رادار"],
                ["📸 شارت فوري", "📊 تقرير شامل"],
                ["▶️ تشغيل", "🛑 إيقاف"]
            ],
            "resize_keyboard": True,
            "is_persistent": True, # يجبر الأزرار على البقاء
            "one_time_keyboard": False
        })

    # إرسال رسالة لبوت التحكم (مع الأزرار دائماً)
    def send_admin(self, message):
        try:
            url = self.control_url + "sendMessage"
            data = {
                "chat_id": self.chat_id, 
                "text": message, 
                "parse_mode": "HTML",
                "reply_markup": self.keyboard # إرفاق الأزرار مع كل رسالة
            }
            requests.post(url, data=data, timeout=5)
        except: pass

    # إرسال لبوت الرادار (بدون أزرار)
    def send_news(self, message):
        try:
            url = self.news_url + "sendMessage"
            data = {"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}
            requests.post(url, data=data, timeout=5)
        except: pass

    # إرسال صورة
    def send_photo(self, photo_buf, caption="", bot_type='news'):
        try:
            if bot_type == 'news':
                url = self.news_url + "sendPhoto"
                data = {"chat_id": self.chat_id, "caption": caption, "parse_mode": "HTML"}
            else:
                # لبوت التحكم نرسل الأزرار مع الصورة أيضاً
                url = self.control_url + "sendPhoto"
                data = {
                    "chat_id": self.chat_id, 
                    "caption": caption, 
                    "parse_mode": "HTML",
                    "reply_markup": self.keyboard
                }
                
            photo_buf.seek(0)
            files = {'photo': photo_buf}
            requests.post(url, data=data, files=files, timeout=10)
        except Exception as e:
            print(f"Photo Error: {e}")

    def check_updates(self):
        try:
            url = self.control_url + "getUpdates"
            params = {"offset": self.offset, "timeout": 1}
            resp = requests.get(url, params=params, timeout=3)
            data = resp.json()
            
            if "result" in data and len(data["result"]) > 0:
                last_update = data["result"][-1]
                self.offset = last_update["update_id"] + 1
                if "message" in last_update and "text" in last_update["message"]:
                    return last_update["message"]["text"]
            return None
        except: return None
    
    def show_keyboard(self, msg):
        self.send_admin(msg)
