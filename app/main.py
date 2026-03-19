from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })


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


def remove_background_from_url(image_url):
    response = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        data={
            "image_url": image_url,
            "size": "auto"
        },
        headers={
            "X-Api-Key": REMOVE_BG_API_KEY
        },
        timeout=120
    )

    if response.status_code == 200:
        return {
            "success": True,
            "content": response.content
        }

    return {
        "success": False,
        "status_code": response.status_code,
        "error_text": response.text
    }


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
            file_id = photo_list[-1]["file_id"]
            file_path = get_file_path(file_id)

            if file_path:
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                send_message(chat_id, "Фото получено. Удаляю фон, это может занять до 20–40 секунд.")

                result = remove_background_from_url(file_url)

                if result["success"]:
                    send_document(chat_id, result["content"], "removed_bg.png")
                else:
                    error_message = (
                        "Не удалось удалить фон.\n"
                        f"Код ошибки: {result['status_code']}\n"
                        f"Ответ сервиса: {result['error_text']}"
                    )
                    send_message(chat_id, error_message)
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
                    send_message(chat_id, "Файл изображения получен. Удаляю фон, это может занять до 20–40 секунд.")

                    result = remove_background_from_url(file_url)

                    if result["success"]:
                        send_document(chat_id, result["content"], "removed_bg.png")
                    else:
                        error_message = (
                            "Не удалось удалить фон.\n"
                            f"Код ошибки: {result['status_code']}\n"
                            f"Ответ сервиса: {result['error_text']}"
                        )
                        send_message(chat_id, error_message)
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