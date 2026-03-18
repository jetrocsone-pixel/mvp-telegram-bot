from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })


def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
    response = requests.get(url, params={"file_id": file_id})
    data = response.json()

    if data.get("ok"):
        return data["result"]["file_path"]

    return None


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        # 1. Если пришло фото
        if "photo" in data["message"]:
            photo_list = data["message"]["photo"]
            file_id = photo_list[-1]["file_id"]  # берём самое большое фото
            file_path = get_file_path(file_id)

            if file_path:
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                send_message(chat_id, f"Фото получено.\nfile_id: {file_id}\nfile_path: {file_path}\nfile_url: {file_url}")
            else:
                send_message(chat_id, "Не удалось получить путь к фото.")

        # 2. Если пришёл файл
        elif "document" in data["message"]:
            document = data["message"]["document"]
            mime_type = document.get("mime_type", "")

            if mime_type.startswith("image/"):
                file_id = document["file_id"]
                file_path = get_file_path(file_id)

                if file_path:
                    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    send_message(chat_id, f"Файл изображения получен.\nfile_id: {file_id}\nfile_path: {file_path}\nfile_url: {file_url}")
                else:
                    send_message(chat_id, "Не удалось получить путь к файлу изображения.")
            else:
                send_message(chat_id, "Я принимаю только изображения. Отправь фото товара как фото или как файл-изображение.")

        # 3. Если пришёл текст
        elif "text" in data["message"]:
            text = data["message"]["text"]

            reply_text = (
                "Бот работает.\n\n"
                "Отправь фотографию товара.\n"
                "Лучше всего — как файл, чтобы не терялось качество.\n\n"
                f"Твой текст: {text}"
            )

            send_message(chat_id, reply_text)

    return {"ok": True}