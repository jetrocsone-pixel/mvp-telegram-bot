from app.config import BOT_TOKEN
from app.state import user_modes, user_data
from app.menus import get_main_menu, get_tz_pro_upload_menu
from app.telegram_api import send_message, send_document, get_file_path
from app.services.remove_bg import remove_background_from_url
from app.services.openai_service import generate_tz_lite


def handle_document_message(message):
    chat_id = message["chat"]["id"]
    current_mode = user_modes.get(chat_id)

    document = message["document"]
    mime_type = document.get("mime_type", "")

    if current_mode == "tz_pro_wait_photos":
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

    return {"ok": True}