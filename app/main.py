from fastapi import FastAPI, Request
import requests

from app.config import BOT_TOKEN, REMOVE_BG_API_KEY, OPENAI_API_KEY
from app.state import user_modes, user_data
from app.menus import get_main_menu, get_tz_choice_menu, get_tz_back_menu, get_tz_pro_upload_menu, get_pro_question_menu
from app.telegram_api import send_message, send_document, get_file_path, answer_callback_query
from app.services.remove_bg import remove_background_from_url
from app.services.openai_service import generate_tz_lite, generate_tz_pro_questions

app = FastAPI() 

def format_pro_question(question_data, question_number):
    return (
        f"Вопрос {question_number} из 6\n\n"
        f"{question_data['question']}\n\n"
        f"A. {question_data['options']['A']}\n"
        f"B. {question_data['options']['B']}\n"
        f"C. {question_data['options']['C']}\n"
        f"D. {question_data['options']['D']}"
    )

@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "callback_query" in data:
        callback = data["callback_query"]
        callback_id = callback["id"]
        chat_id = callback["message"]["chat"]["id"]
        callback_data = callback["data"]

        answer_callback_query(callback_id)

        if callback_data == "tz_lite":
            user_modes[chat_id] = "tz_lite_wait_photo"
            user_data[chat_id] = {}

            send_message(
                chat_id,
                "Режим ТЗ Lite активирован.\n\n"
                "Отправь 1 фото товара.\n"
                "Лучше всего отправлять как файл без сжатия.",
                reply_markup=get_tz_back_menu()
            )

        elif callback_data == "tz_pro":
            user_modes[chat_id] = "tz_pro_wait_photos"
            user_data[chat_id] = {
                "photos": []
            }

            send_message(
                chat_id,
                "Режим ТЗ Pro активирован.\n\n"
                "Шаг 1: отправь от 1 до 3 фото товара.\n"
                "Лучше всего отправлять как файл без сжатия.\n\n"
                "Когда закончишь загрузку, нажми «Готово».",
                reply_markup=get_tz_pro_upload_menu()
            )

        elif callback_data == "tz_pro_done":
            photos = user_data.get(chat_id, {}).get("photos", [])

            if len(photos) == 0:
                send_message(
                    chat_id,
                    "Ты ещё не отправил ни одного фото.\n\n"
                    "Сначала отправь от 1 до 3 фото товара, потом нажми «Готово».",
                    reply_markup=get_tz_pro_upload_menu()
                )
            else:
                send_message(
                    chat_id,
                    "Фото получены.\n\n"
                    "Генерирую вопросы для ТЗ Pro. Это может занять до 20–40 секунд."
                )

                try:
                    questions_result = generate_tz_pro_questions(photos)
                    questions = questions_result.get("questions", [])

                    if len(questions) != 6:
                        send_message(
                            chat_id,
                            "Не удалось корректно сформировать 6 вопросов. Попробуй ещё раз.",
                            reply_markup=get_tz_back_menu()
                        )
                    else:
                        user_modes[chat_id] = "tz_pro_questions"
                        user_data[chat_id]["questions"] = questions
                        user_data[chat_id]["answers"] = []
                        user_data[chat_id]["current_question_index"] = 0

                        first_question = questions[0]

                        send_message(
                            chat_id,
                            format_pro_question(first_question, 1),
                            reply_markup=get_pro_question_menu()
                        )

                except Exception as e:
                    send_message(
                        chat_id,
                        f"Ошибка при генерации вопросов:\n{str(e)}",
                        reply_markup=get_tz_back_menu()
                    )

        elif callback_data.startswith("pro_answer_"):
            if user_modes.get(chat_id) != "tz_pro_questions":
                return {"ok": True}

            answer = callback_data.split("_")[-1]

            user_data[chat_id]["answers"].append(answer)
            user_data[chat_id]["current_question_index"] += 1

            current_index = user_data[chat_id]["current_question_index"]
            questions = user_data[chat_id]["questions"]

            if current_index < 6:
                next_question = questions[current_index]

                send_message(
                    chat_id,
                    format_pro_question(next_question, current_index + 1),
                    reply_markup=get_pro_question_menu()
                )
            else:
                user_modes[chat_id] = "tz_pro_mode_choice"

                send_message(
                    chat_id,
                    "Отлично. Все ответы получены.\n\nВыбери формат ТЗ:",
                    reply_markup={
                        "inline_keyboard": [
                            [
                                {"text": "Стандарт", "callback_data": "tz_pro_mode_standard"},
                                {"text": "Баланс", "callback_data": "tz_pro_mode_balance"},
                                {"text": "Креатив", "callback_data": "tz_pro_mode_creative"}
                            ],
                            [
                                {"text": "Назад к выбору ТЗ", "callback_data": "back_to_tz_choice"}
                            ]
                        ]
                    }
                )

        elif callback_data == "back_to_tz_choice":
            user_modes[chat_id] = None
            user_data[chat_id] = {}

            send_message(
                chat_id,
                "Выбери формат ТЗ:",
                reply_markup=get_tz_choice_menu()
            )

        elif callback_data == "back_to_main":
            user_modes[chat_id] = None
            user_data[chat_id] = {}

            send_message(
                chat_id,
                "Возвращаю в главное меню.",
                reply_markup=get_main_menu()
            )

        return {"ok": True}

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        if "photo" in data["message"]:
            current_mode = user_modes.get(chat_id)

            if current_mode == "tz_pro_wait_photos":
                photo_list = data["message"]["photo"]
                file_id = photo_list[-1]["file_id"]
                file_path = get_file_path(file_id)

                if file_path:
                    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

                    if chat_id not in user_data:
                        user_data[chat_id] = {"photos": []}

                    if "photos" not in user_data[chat_id]:
                        user_data[chat_id]["photos"] = []

                    if len(user_data[chat_id]["photos"]) >= 3:
                        send_message(
                            chat_id,
                            "Можно загрузить максимум 3 фото.\n\n"
                            "Нажми «Готово», чтобы перейти дальше.",
                            reply_markup=get_tz_pro_upload_menu()
                        )
                    else:
                        user_data[chat_id]["photos"].append(file_url)

                        send_message(
                            chat_id,
                            f"Фото {len(user_data[chat_id]['photos'])} из 3 получено.\n"
                            "Можешь отправить ещё фото или нажать «Готово».",
                            reply_markup=get_tz_pro_upload_menu()
                        )

                return {"ok": True}
            
            if current_mode == "tz_lite_wait_photo":
                photo_list = data["message"]["photo"]
                file_id = photo_list[-1]["file_id"]
                file_path = get_file_path(file_id)

                if file_path:
                    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

                    send_message(
                        chat_id,
                        "Генерирую ТЗ Lite. Это может занять до 20–40 секунд."
                    )

                    try:
                        tz_text = generate_tz_lite(file_url)

                        user_modes[chat_id] = None

                        send_message(
                            chat_id,
                            tz_text,
                            reply_markup=get_main_menu()
                        )
                    except Exception as e:
                        send_message(
                            chat_id,
                            f"Ошибка генерации ТЗ:\n{str(e)}",
                            reply_markup=get_main_menu()
                        )

                return {"ok": True}
            
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

            if current_mode == "tz_pro_wait_photos":
                document = data["message"]["document"]
                mime_type = document.get("mime_type", "")

                if mime_type.startswith("image/"):
                    file_id = document["file_id"]
                    file_path = get_file_path(file_id)

                    if file_path:
                        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

                        if chat_id not in user_data:
                            user_data[chat_id] = {"photos": []}

                        if "photos" not in user_data[chat_id]:
                            user_data[chat_id]["photos"] = []

                        if len(user_data[chat_id]["photos"]) >= 3:
                            send_message(
                                chat_id,
                                "Можно загрузить максимум 3 фото.\n\n"
                                "Нажми «Готово», чтобы перейти дальше.",
                                reply_markup=get_tz_pro_upload_menu()
                            )
                        else:
                            user_data[chat_id]["photos"].append(file_url)

                            send_message(
                                chat_id,
                                f"Фото {len(user_data[chat_id]['photos'])} из 3 получено.\n"
                                "Можешь отправить ещё фото или нажать «Готово».",
                                reply_markup=get_tz_pro_upload_menu()
                            )
                else:
                    send_message(
                        chat_id,
                        "Для ТЗ Pro нужен файл-изображение.\nОтправь фото товара.",
                        reply_markup=get_tz_pro_upload_menu()
                    )

                return {"ok": True}
                        
            if current_mode == "tz_lite_wait_photo":
                document = data["message"]["document"]
                mime_type = document.get("mime_type", "")

                if mime_type.startswith("image/"):
                    file_id = document["file_id"]
                    file_path = get_file_path(file_id)

                    if file_path:
                        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

                        send_message(
                            chat_id,
                            "Генерирую ТЗ Lite. Это может занять до 20–40 секунд."
                        )

                        try:
                            tz_text = generate_tz_lite(file_url)

                            user_modes[chat_id] = None

                            send_message(
                                chat_id,
                                tz_text,
                                reply_markup=get_main_menu()
                            )
                        except Exception as e:
                            send_message(
                                chat_id,
                                f"Ошибка генерации ТЗ:\n{str(e)}",
                                reply_markup=get_main_menu()
                            )

                return {"ok": True}
            
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
                user_modes[chat_id] = None
                user_data[chat_id] = {}

                send_message(
                    chat_id,
                    "Выбери формат ТЗ:",
                    reply_markup=get_tz_choice_menu()
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