import logging

from app.menus import get_main_menu, get_tz_choice_menu
from app.state import user_data, user_modes
from app.telegram_api import send_message
from app.texts import (
    BUTTON_CREATE_TZ,
    BUTTON_GENERATE_COVERS,
    BUTTON_HELP,
    BUTTON_REMOVE_BG,
    MSG_CHOOSE_MENU_ACTION,
    MSG_COVERS_STUB,
    MSG_HELP,
    MSG_SEND_PRODUCT_PHOTO,
    MSG_TZ_CHOICE,
    MSG_WELCOME,
)

logger = logging.getLogger(__name__)


def handle_text_message(message):
    chat_id = message["chat"]["id"]
    text = message["text"].strip()
    logger.info("Handling text message for chat_id=%s text=%s", chat_id, text)

    if text == "/start":
        user_modes[chat_id] = None
        send_message(chat_id, MSG_WELCOME, reply_markup=get_main_menu())

    elif text == BUTTON_REMOVE_BG:
        user_modes[chat_id] = "remove_bg"
        send_message(chat_id, MSG_SEND_PRODUCT_PHOTO, reply_markup=get_main_menu())

    elif text == BUTTON_CREATE_TZ:
        user_modes[chat_id] = None
        user_data[chat_id] = {}
        send_message(chat_id, MSG_TZ_CHOICE, reply_markup=get_tz_choice_menu())

    elif text == BUTTON_GENERATE_COVERS:
        send_message(chat_id, MSG_COVERS_STUB, reply_markup=get_main_menu())

    elif text == BUTTON_HELP:
        user_modes[chat_id] = None
        send_message(chat_id, MSG_HELP, reply_markup=get_main_menu())

    else:
        send_message(chat_id, MSG_CHOOSE_MENU_ACTION, reply_markup=get_main_menu())

    return {"ok": True}
