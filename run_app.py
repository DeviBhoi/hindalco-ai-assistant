import webview
import threading
from app import app

def run_flask():
    app.run()

threading.Thread(target=run_flask).start()

webview.create_window(
    "Hindalco AI Assistant",
    "http://127.0.0.1:5000",
    width=1400,
    height=900
)

webview.start()