from app.config import BOT_TOKEN
from app.state import user_data
from app.telegram_api import get_file_path


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
