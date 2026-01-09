# keep_alive.py
# سيرفر ويب بسيط لإرضاء Render
# -------------------------------------
from flask import Flask
from threading import Thread
import logging

# إخفاء الرسائل المزعجة
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return "I am alive! 🦅 Sniper Bot is Running."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
