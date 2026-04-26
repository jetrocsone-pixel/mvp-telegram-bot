from app.handlers.image_helpers import extract_image_url, store_tz_pro_photo
from app.menus import get_main_menu, get_tz_pro_upload_menu
from app.services.openai_service import generate_tz_lite
from app.services.remove_bg import remove_background_from_url
from app.state import user_modes
from app.telegram_api import send_document, send_message


def handle_document_message(message):
    chat_id = message["chat"]["id"]
    current_mode = user_modes.get(chat_id)
    file_url = extract_image_url(message)

    if current_mode == "tz_pro_wait_photos":
        if not file_url:
            send_message(
                chat_id,
                "Для ТЗ Pro нужен файл-изображение.\nОтправь фото товара.",
                reply_markup=get_tz_pro_upload_menu(),
            )
            return {"ok": True}

        photo_count = store_tz_pro_photo(chat_id, file_url)

        if photo_count is None:
            send_message(
                chat_id,
                "Можно загрузить максимум 3 фото.\n\nНажми «Готово», чтобы перейти дальше.",
                reply_markup=get_tz_pro_upload_menu(),
            )
        else:
            send_message(
                chat_id,
                f"Фото {photo_count} из 3 получено.\nМожешь отправить ещё фото или нажать «Готово».",
                reply_markup=get_tz_pro_upload_menu(),
            )

        return {"ok": True}

    if current_mode == "tz_lite_wait_photo":
        if not file_url:
            send_message(
                chat_id,
                "Для ТЗ Lite нужен файл-изображение.\nОтправь фото товара.",
                reply_markup=get_main_menu(),
            )
            return {"ok": True}

        send_message(
            chat_id,
            "Генерирую ТЗ Lite. Это может занять до 20-40 секунд.",
        )

        try:
            tz_text = generate_tz_lite(file_url)
            user_modes[chat_id] = None
            send_message(chat_id, tz_text, reply_markup=get_main_menu())
        except Exception as e:
            send_message(
                chat_id,
                f"Ошибка генерации ТЗ:\n{str(e)}",
                reply_markup=get_main_menu(),
            )

        return {"ok": True}

    if current_mode == "tz":
        if file_url:
            send_message(
                chat_id,
                "Файл изображения для ТЗ получен.\nСледующим шагом подключим сбор описания товара и генерацию ТЗ.",
                reply_markup=get_main_menu(),
            )
        else:
            send_message(
                chat_id,
                "Для ТЗ нужен файл-изображение. Отправь фото товара.",
                reply_markup=get_main_menu(),
            )

        return {"ok": True}

    if not file_url:
        send_message(
            chat_id,
            "Я принимаю только изображения. Отправь фото товара как фото или как файл-изображение.",
            reply_markup=get_main_menu(),
        )
        return {"ok": True}

    send_message(
        chat_id,
        "Файл изображения получен. Удаляю фон, это может занять до 20-40 секунд.",
        reply_markup=get_main_menu(),
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

    return {"ok": True}
