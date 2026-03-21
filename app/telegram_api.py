import requests

from app.config import BOT_TOKEN


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(url, json=payload)


def send_document(chat_id, file_bytes, filename="result.png"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {
        "document": (filename, file_bytes, "image/png")
    }
    data = {
        "chat_id": chat_id
    }
    requests.post(url, data=data, files=files)


def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
    response = requests.get(url, params={"file_id": file_id})
    data = response.json()

    if data.get("ok"):
        return data["result"]["file_path"]

    return None