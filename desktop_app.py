import threading
import webview

from app import app


def start_flask():

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )


if __name__ == "__main__":

    flask_thread = threading.Thread(
        target=start_flask
    )

    flask_thread.daemon = True

    flask_thread.start()

    webview.create_window(
        "Hindalco AI Assistant",
        "http://127.0.0.1:5000",
        width=1400,
        height=900
    )

    webview.start()