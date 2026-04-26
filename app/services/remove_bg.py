import logging

import requests

from app.config import REMOVE_BG_API_KEY

logger = logging.getLogger(__name__)


def remove_background_from_url(image_url):
    if not REMOVE_BG_API_KEY:
        return {
            "success": False,
            "status_code": None,
            "error_text": "Не задан REMOVE_BG_API_KEY."
        }

    try:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            data={
                "image_url": image_url,
                "size": "auto"
            },
            headers={
                "X-Api-Key": REMOVE_BG_API_KEY
            },
            timeout=120
        )
    except requests.RequestException as exc:
        logger.exception("remove.bg request failed")
        return {
            "success": False,
            "status_code": None,
            "error_text": str(exc)
        }

    if response.status_code == 200:
        return {
            "success": True,
            "content": response.content
        }

    return {
        "success": False,
        "status_code": response.status_code,
        "error_text": response.text
    }
