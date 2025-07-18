from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Твой Telegram токен и chat_id
TELEGRAM_TOKEN = "8135133326:AAH1sRHovfzjRcyeDGqeCALoMF_qvwS4C6k"
TELEGRAM_CHAT_ID = "5070282357"

# Функция отправки сообщения в Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)

# Обработка POST-запроса от Kaspi
@app.post("/payment")
async def payment_handler(request: Request):
    data = await request.json()
    print("Получено:", data)

    # Отправка сообщения в Telegram
    send_telegram_message(f"💸 Поступила оплата!\n\n{data}")

    return {"ok": True}
