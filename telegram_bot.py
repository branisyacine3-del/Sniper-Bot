# telegram_bot.py
# مدير الاتصالات
# -------------------------------------
import requests
import config

class TelegramBot:
    def __init__(self):
        self.token = config.BOT_TOKEN
        self.chat_id = config.CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self.offset = 0

    def send(self, message):
        try:
            url = self.base_url + "sendMessage"
            data = {"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}
            requests.post(url, data=data, timeout=5)
        except: pass

    def send_photo(self, photo_buf, caption="", channel='main'):
        try:
            url = self.base_url + "sendPhoto"
            files = {'photo': photo_buf}
            data = {"chat_id": self.chat_id, "caption": caption}
            requests.post(url, data=data, files=files, timeout=10)
        except Exception as e:
            print(f"Photo Error: {e}")

    def check_updates(self):
        try:
            url = self.base_url + "getUpdates"
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
        self.send(msg)
