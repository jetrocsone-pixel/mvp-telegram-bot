from app.menus import get_main_menu
from fastapi import FastAPI, Request
import requests
import os
from openai import OpenAI

from app.config import BOT_TOKEN, REMOVE_BG_API_KEY, OPENAI_API_KEY
from app.state import user_modes, user_data

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI() 

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

        if "photo" in data["message"]:
            current_mode = user_modes.get(chat_id)
            if current_mode == "tz":
                send_message(
                    chat_id,
                    "Фото для ТЗ получено.\nСледующим шагом подключим сбор описания товара и генерацию ТЗ.",
                    reply_markup=get_main_menu()
                )
                return {"ok": True}            
            photo_list = data["message"]["photo"]
            file_id = photo_list[-1]["file_id"]
            file_path = get_file_path(file_id)

            if file_path:
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                send_message(
                    chat_id,
                    "Фото получено. Удаляю фон, это может занять до 20–40 секунд.",
                    reply_markup=get_main_menu()
                )

                result = remove_background_from_url(file_url)

                if result["success"]:
                    send_document(chat_id, result["content"], "removed_bg.png")
                else:
                    error_message = (
                        "Не удалось удалить фон.\n"
                        f"Код ошибки: {result['status_code']}\n"
                        f"Ответ сервиса: {result['error_text']}"
                    )
                    send_message(chat_id, error_message, reply_markup=get_main_menu())
            else:
                send_message(chat_id, "Не удалось получить путь к фото.", reply_markup=get_main_menu())

        elif "document" in data["message"]:
            current_mode = user_modes.get(chat_id)
            if current_mode == "tz":
                document = data["message"]["document"]
                mime_type = document.get("mime_type", "")

                if mime_type.startswith("image/"):
                    send_message(
                        chat_id,
                        "Файл изображения для ТЗ получен.\nСледующим шагом подключим сбор описания товара и генерацию ТЗ.",
                        reply_markup=get_main_menu()
                    )
                else:
                    send_message(
                        chat_id,
                        "Для ТЗ нужен файл-изображение. Отправь фото товара.",
                        reply_markup=get_main_menu()
                    )

                return {"ok": True}            
            document = data["message"]["document"]
            mime_type = document.get("mime_type", "")

            if mime_type.startswith("image/"):
                file_id = document["file_id"]
                file_path = get_file_path(file_id)

                if file_path:
                    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    send_message(
                        chat_id,
                        "Файл изображения получен. Удаляю фон, это может занять до 20–40 секунд.",
                        reply_markup=get_main_menu()
                    )

                    result = remove_background_from_url(file_url)

                    if result["success"]:
                        send_document(chat_id, result["content"], "removed_bg.png")
                    else:
                        error_message = (
                            "Не удалось удалить фон.\n"
                            f"Код ошибки: {result['status_code']}\n"
                            f"Ответ сервиса: {result['error_text']}"
                        )
                        send_message(chat_id, error_message, reply_markup=get_main_menu())
                else:
                    send_message(chat_id, "Не удалось получить путь к файлу изображения.", reply_markup=get_main_menu())
            else:
                send_message(
                    chat_id,
                    "Я принимаю только изображения. Отправь фото товара как фото или как файл-изображение.",
                    reply_markup=get_main_menu()
                )

        elif "text" in data["message"]:
            text = data["message"]["text"].strip()

            if text == "/start":
                user_modes[chat_id] = None
                send_message(
                    chat_id,
                    "Добро пожаловать.\n\nВыбери нужное действие в меню ниже.",
                    reply_markup=get_main_menu()
                )

            elif text == "Удалить фон":
                user_modes[chat_id] = "remove_bg"
                send_message(
                    chat_id,
                    "Отправь фото товара.\nЛучше всего отправлять как файл без сжатия.",
                    reply_markup=get_main_menu()
                )

            elif text == "Создать ТЗ":
                user_modes[chat_id] = "tz"
                send_message(
                    chat_id,
                    "Режим создания ТЗ активирован.\n\n"
                    "Шаг 1: отправь фото товара.\n"
                    "Лучше всего отправлять как файл без сжатия.",
                    reply_markup=get_main_menu()
                )

            elif text == "Сгенерировать обложки":
                send_message(
                    chat_id,
                    "Режим генерации обложек подключим следующим этапом.",
                    reply_markup=get_main_menu()
                )

            elif text == "Помощь":
                user_modes[chat_id] = None
                send_message(
                    chat_id,
                    "Я умею:\n"
                    "1. Удалять фон у товара\n"
                    "2. Готовить ТЗ для фотоворонки\n"
                    "3. Генерировать обложки\n\n"
                    "Сейчас полностью работает функция удаления фона.",
                    reply_markup=get_main_menu()
                )

            else:
                send_message(
                    chat_id,
                    "Выбери действие в меню ниже.",
                    reply_markup=get_main_menu()
                )

    return {"ok": True}