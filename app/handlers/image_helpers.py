import logging

from app.config import BOT_TOKEN
from app.menus import get_main_menu, get_tz_pro_upload_menu
from app.services.openai_service import generate_tz_lite
from app.services.remove_bg import remove_background_from_url
from app.state import user_data, user_modes
from app.telegram_api import get_file_path, send_document, send_message
from app.texts import (
    MSG_GENERATING_TZ_LITE,
    MSG_MAX_3_PHOTOS,
    MSG_PHOTO_RECEIVED_TEMPLATE,
    MSG_REMOVE_BG_ERROR,
    MSG_TZ_GENERATION_ERROR,
)

logger = logging.getLogger(__name__)


def extract_image_url(message):
    if "photo" in message:
        file_id = message["photo"][-1]["file_id"]
    else:
        document = message.get("document", {})
        mime_type = document.get("mime_type", "")
        if not mime_type.startswith("image/"):
            return None
        file_id = document["file_id"]

    file_path = get_file_path(file_id)
    if not file_path:
        return None

    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"


def store_tz_pro_photo(chat_id, file_url, max_photos=3):
    photos = user_data.setdefault(chat_id, {}).setdefault("photos", [])

    if len(photos) >= max_photos:
        return None

    photos.append(file_url)
    return len(photos)


def handle_tz_pro_upload(chat_id, file_url):
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


def handle_tz_lite_generation(chat_id, file_url):
    send_message(chat_id, MSG_GENERATING_TZ_LITE)

    try:
        tz_text = generate_tz_lite(file_url)
        user_modes[chat_id] = None
        send_message(chat_id, tz_text, reply_markup=get_main_menu())
    except Exception as exc:
        logger.exception("TZ Lite generation failed for chat_id=%s", chat_id)
        send_message(
            chat_id,
            MSG_TZ_GENERATION_ERROR.format(error=str(exc)),
            reply_markup=get_main_menu(),
        )

    return {"ok": True}


def handle_remove_bg_result(chat_id, file_url):
    result = remove_background_from_url(file_url)

    if result["success"]:
        send_document(chat_id, result["content"], "removed_bg.png")
    else:
        logger.error("remove.bg failed for chat_id=%s status=%s", chat_id, result["status_code"])
        send_message(
            chat_id,
            MSG_REMOVE_BG_ERROR.format(
                status_code=result["status_code"],
                error_text=result["error_text"],
            ),
            reply_markup=get_main_menu(),
        )

    return {"ok": True}
