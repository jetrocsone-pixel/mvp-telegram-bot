import requests

from app.config import REMOVE_BG_API_KEY


def remove_background_from_url(image_url):
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