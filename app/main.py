from fastapi import FastAPI, Request
import requests

from app.config import BOT_TOKEN, REMOVE_BG_API_KEY, OPENAI_API_KEY
from app.state import user_modes, user_data
from app.menus import get_main_menu, get_tz_choice_menu, get_tz_back_menu, get_tz_pro_upload_menu, get_pro_question_menu
from app.telegram_api import send_message, send_document, get_file_path, answer_callback_query
from app.services.remove_bg import remove_background_from_url
from app.services.openai_service import generate_tz_lite, generate_tz_pro_questions, generate_tz_pro_result
from app.handlers.callback_handler import handle_callback_query
from app.handlers.text_handler import handle_text_message
from app.handlers.photo_handler import handle_photo_message
from app.handlers.document_handler import handle_document_message

app = FastAPI() 

@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "callback_query" in data:
        callback = data["callback_query"]
        return handle_callback_query(callback)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        if "photo" in data["message"]:
            return handle_photo_message(data["message"])        

        elif "document" in data["message"]:
            return handle_document_message(data["message"])

        elif "text" in data["message"]:
            return handle_text_message(data["message"])

    return {"ok": True}