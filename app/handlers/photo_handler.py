from app.handlers.image_helpers import (
    extract_image_url,
    handle_remove_bg_result,
    handle_tz_lite_generation,
    handle_tz_pro_upload,
)
from app.menus import get_main_menu, get_tz_pro_upload_menu
from app.state import user_modes
from app.telegram_api import send_message
from app.texts import (
    MSG_FILE_PATH_UNAVAILABLE,
    MSG_GENERATING_REMOVE_BG_PHOTO,
    MSG_TELEGRAM_PHOTO_UNAVAILABLE,
    MSG_TZ_PHOTO_RECEIVED,
)

def handle_photo_message(message):
    chat_id = message["chat"]["id"]
    current_mode = user_modes.get(chat_id)
    file_url = extract_image_url(message)
    logger.info("Handling photo message for chat_id=%s mode=%s", chat_id, current_mode)

    if current_mode == "tz_pro_wait_photos":
        if not file_url:
            send_message(chat_id, MSG_TELEGRAM_PHOTO_UNAVAILABLE, reply_markup=get_tz_pro_upload_menu())
            return {"ok": True}

        return handle_tz_pro_upload(chat_id, file_url)

    if current_mode == "tz_lite_wait_photo":
        if not file_url:
            send_message(chat_id, MSG_TELEGRAM_PHOTO_UNAVAILABLE, reply_markup=get_main_menu())
            return {"ok": True}

        return handle_tz_lite_generation(chat_id, file_url)

    if current_mode == "tz":
        send_message(chat_id, MSG_TZ_PHOTO_RECEIVED, reply_markup=get_main_menu())
        return {"ok": True}

    if not file_url:
        send_message(chat_id, MSG_FILE_PATH_UNAVAILABLE, reply_markup=get_main_menu())
        return {"ok": True}

    send_message(chat_id, MSG_GENERATING_REMOVE_BG_PHOTO, reply_markup=get_main_menu())
    return handle_remove_bg_result(chat_id, file_url)
