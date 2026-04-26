import logging

from fastapi import FastAPI, Request

from app.handlers.callback_handler import handle_callback_query
from app.handlers.document_handler import handle_document_message
from app.handlers.photo_handler import handle_photo_message
from app.handlers.text_handler import handle_text_message
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def home():
    logger.info("Healthcheck requested")
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    logger.info("Webhook update received with keys=%s", list(data.keys()))

    if "callback_query" in data:
        callback = data["callback_query"]
        logger.info("Routing callback_query for chat_id=%s", callback["message"]["chat"]["id"])
        return handle_callback_query(callback)

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]

        if "photo" in message:
            logger.info("Routing photo message for chat_id=%s", chat_id)
            return handle_photo_message(message)

        if "document" in message:
            logger.info("Routing document message for chat_id=%s", chat_id)
            return handle_document_message(message)

        if "text" in message:
            logger.info("Routing text message for chat_id=%s", chat_id)
            return handle_text_message(message)

    logger.info("Webhook update ignored")
    return {"ok": True}