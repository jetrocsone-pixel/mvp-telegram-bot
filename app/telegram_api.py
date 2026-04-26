import logging

import requests

from app.config import BOT_TOKEN

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = (10, 60)
TELEGRAM_TEXT_LIMIT = 4096


def _telegram_url(method):
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


def _post_telegram(method, *, json=None, data=None, files=None):
    try:
        response = requests.post(
            _telegram_url(method),
            json=json,
            data=data,
            files=files,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()

        if not payload.get("ok", True):
            logger.error("Telegram API returned error for %s: %s", method, payload)
            return None

        return payload
    except requests.RequestException:
        logger.exception("Telegram API request failed for %s", method)
        return None
    except ValueError:
        logger.exception("Telegram API returned non-JSON response for %s", method)
        return None


def _get_telegram(method, *, params=None):
    try:
        response = requests.get(
            _telegram_url(method),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()

        if not payload.get("ok", True):
            logger.error("Telegram API returned error for %s: %s", method, payload)
            return None

        return payload
    except requests.RequestException:
        logger.exception("Telegram API request failed for %s", method)
        return None
    except ValueError:
        logger.exception("Telegram API returned non-JSON response for %s", method)
        return None


def _split_text(text, limit=TELEGRAM_TEXT_LIMIT):
    if len(text) <= limit:
        return [text]

    chunks = []
    remaining = text

    while len(remaining) > limit:
        split_index = remaining.rfind("\n", 0, limit)
        if split_index <= 0:
            split_index = limit

        chunks.append(remaining[:split_index].rstrip())
        remaining = remaining[split_index:].lstrip("\n")

    if remaining:
        chunks.append(remaining)

    return chunks


def send_message(chat_id, text, reply_markup=None):
    chunks = _split_text(text)
    sent_all = True

    for index, chunk in enumerate(chunks):
        payload = {
            "chat_id": chat_id,
            "text": chunk
        }

        if reply_markup and index == len(chunks) - 1:
            payload["reply_markup"] = reply_markup

        sent_all = _post_telegram("sendMessage", json=payload) is not None and sent_all

    return sent_all


def send_document(chat_id, file_bytes, filename="result.png"):
    files = {
        "document": (filename, file_bytes, "image/png")
    }
    data = {
        "chat_id": chat_id
    }
    return _post_telegram("sendDocument", data=data, files=files) is not None


def get_file_path(file_id):
    payload = _get_telegram("getFile", params={"file_id": file_id})

    if payload:
        return payload["result"]["file_path"]

    return None


def answer_callback_query(callback_query_id):
    return _post_telegram("answerCallbackQuery", json={
        "callback_query_id": callback_query_id
    }) is not None
