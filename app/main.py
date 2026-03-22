from fastapi import FastAPI, Request

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
        message = data["message"]

        if "photo" in message:
            return handle_photo_message(message)

        elif "document" in message:
            return handle_document_message(message)

        elif "text" in message:
            return handle_text_message(message)

    return {"ok": True}