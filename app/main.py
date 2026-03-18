from fastapi import FastAPI, Request
import requests

app = FastAPI()

BOT_TOKEN = "8591079372:AAGncRoWu_xNfHzTMG879XwB7LEtvxvIyZY"

@app.get("/")
def home():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        reply_text = f"Ты написал: {text}"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(url, json={
            "chat_id": chat_id,
            "text": reply_text
        })

    return {"ok": True}