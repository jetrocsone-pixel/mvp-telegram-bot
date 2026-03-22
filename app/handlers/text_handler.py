from app.state import user_modes, user_data
from app.menus import get_main_menu, get_tz_choice_menu
from app.telegram_api import send_message


def handle_text_message(message):
    chat_id = message["chat"]["id"]
    text = message["text"].strip()

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