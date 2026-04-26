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
    MSG_GENERATING_REMOVE_BG_FILE,
    MSG_ONLY_IMAGE_FOR_TZ,
    MSG_ONLY_IMAGE_FOR_TZ_LITE,
    MSG_ONLY_IMAGE_FOR_TZ_PRO,
    MSG_ONLY_IMAGES,
    MSG_TZ_FILE_RECEIVED,
)

def handle_document_message(message):
    chat_id = message["chat"]["id"]
    current_mode = user_modes.get(chat_id)
    file_url = extract_image_url(message)
    logger.info("Handling document message for chat_id=%s mode=%s", chat_id, current_mode)

    if current_mode == "tz_pro_wait_photos":
        if not file_url:
            send_message(chat_id, MSG_ONLY_IMAGE_FOR_TZ_PRO, reply_markup=get_tz_pro_upload_menu())
            return {"ok": True}

        return handle_tz_pro_upload(chat_id, file_url)

    if current_mode == "tz_lite_wait_photo":
        if not file_url:
            send_message(chat_id, MSG_ONLY_IMAGE_FOR_TZ_LITE, reply_markup=get_main_menu())
            return {"ok": True}

        return handle_tz_lite_generation(chat_id, file_url)

    if current_mode == "tz":
        if file_url:
            send_message(chat_id, MSG_TZ_FILE_RECEIVED, reply_markup=get_main_menu())
        else:
            send_message(chat_id, MSG_ONLY_IMAGE_FOR_TZ, reply_markup=get_main_menu())
        return {"ok": True}

    if not file_url:
        send_message(chat_id, MSG_ONLY_IMAGES, reply_markup=get_main_menu())
        return {"ok": True}

    send_message(chat_id, MSG_GENERATING_REMOVE_BG_FILE, reply_markup=get_main_menu())
    return handle_remove_bg_result(chat_id, file_url)
