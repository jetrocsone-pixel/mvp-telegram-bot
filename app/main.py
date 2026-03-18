from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")

@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        # Сначала фото
        if "photo" in data["message"]:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

            requests.post(url, json={
                "chat_id": chat_id,
                "text": "Фото получено. Следующим шагом подключим скачивание изображения."
            })

        # Потом текст
        elif "text" in data["message"]:
            text = data["message"]["text"]

            reply_text = (
                "Бот работает.\n\n"
                "Отправь фотографию товара.\n\n"
                f"Твой текст: {text}"
            )

            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

            requests.post(url, json={
                "chat_id": chat_id,
                "text": reply_text
            })

    return {"ok": True}