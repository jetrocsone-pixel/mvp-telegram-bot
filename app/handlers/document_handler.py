import logging

from app.handlers.image_helpers import extract_image_url, store_tz_pro_photo
from app.menus import get_main_menu, get_tz_pro_upload_menu
from app.services.openai_service import generate_tz_lite
from app.services.remove_bg import remove_background_from_url
from app.state import user_modes
from app.telegram_api import send_document, send_message
from app.texts import (
    MSG_GENERATING_REMOVE_BG_FILE,
    MSG_GENERATING_TZ_LITE,
    MSG_MAX_3_PHOTOS,
    MSG_ONLY_IMAGE_FOR_TZ,
    MSG_ONLY_IMAGE_FOR_TZ_LITE,
    MSG_ONLY_IMAGE_FOR_TZ_PRO,
    MSG_ONLY_IMAGES,
    MSG_PHOTO_RECEIVED_TEMPLATE,
    MSG_REMOVE_BG_ERROR,
    MSG_TZ_FILE_RECEIVED,
    MSG_TZ_GENERATION_ERROR,
)

logger = logging.getLogger(__name__)


def handle_document_message(message):
    chat_id = message["chat"]["id"]
    current_mode = user_modes.get(chat_id)
    file_url = extract_image_url(message)
    logger.info("Handling document message for chat_id=%s mode=%s", chat_id, current_mode)

    if current_mode == "tz_pro_wait_photos":
        if not file_url:
            send_message(chat_id, MSG_ONLY_IMAGE_FOR_TZ_PRO, reply_markup=get_tz_pro_upload_menu())
            return {"ok": True}

        photo_count = store_tz_pro_photo(chat_id, file_url)

        if photo_count is None:
            send_message(chat_id, MSG_MAX_3_PHOTOS, reply_markup=get_tz_pro_upload_menu())
        else:
            send_message(
                chat_id,
                MSG_PHOTO_RECEIVED_TEMPLATE.format(count=photo_count),
                reply_markup=get_tz_pro_upload_menu(),
            )

        return {"ok": True}

    if current_mode == "tz_lite_wait_photo":
        if not file_url:
            send_message(chat_id, MSG_ONLY_IMAGE_FOR_TZ_LITE, reply_markup=get_main_menu())
            return {"ok": True}

        send_message(chat_id, MSG_GENERATING_TZ_LITE)

        try:
            tz_text = generate_tz_lite(file_url)
            user_modes[chat_id] = None
            send_message(chat_id, tz_text, reply_markup=get_main_menu())
        except Exception as exc:
            logger.exception("TZ Lite generation from document failed for chat_id=%s", chat_id)
            send_message(
                chat_id,
                MSG_TZ_GENERATION_ERROR.format(error=str(exc)),
                reply_markup=get_main_menu(),
            )

        return {"ok": True}

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

    result = remove_background_from_url(file_url)
    if result["success"]:
        send_document(chat_id, result["content"], "removed_bg.png")
    else:
        logger.error("remove.bg failed for document chat_id=%s status=%s", chat_id, result["status_code"])
        send_message(
            chat_id,
            MSG_REMOVE_BG_ERROR.format(
                status_code=result["status_code"],
                error_text=result["error_text"],
            ),
            reply_markup=get_main_menu(),
        )

    return {"ok": True}
