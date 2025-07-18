from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import requests

app = FastAPI()

# --- ТЕЛЕГРАМ НАСТРОЙКИ ---
TELEGRAM_BOT_TOKEN = "8135133326:AAH1sRHovfzjRcyeDGqeCALoMF_qvwS4C6k"
TELEGRAM_CHAT_ID = "5070282357"

def send_telegram_message(text: str):
    """Отправка сообщения в Telegram чат."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

def parse_amount(data: dict) -> int:
    """Пытаемся достать сумму из JSON. Ищем поля: amount, sum, value, total."""
    for key in ("amount", "sum", "value", "total"):
        if key in data:
            try:
                return int(float(data[key]))
            except Exception:
                pass
    return 0

@app.post("/payment")
async def payment_handler(request: Request):
    """Обработка платежа от Kaspi или теста."""
    data = await request.json()
    print("Получено:", data)

    amount = parse_amount(data)
    if amount <= 0:
        send_telegram_message(f"⚠️ Платёж без суммы: {data}")
        raise HTTPException(status_code=400, detail="No valid amount in JSON.")

    if amount % 100 != 0:
        send_telegram_message(f"⚠️ Неправильная сумма {amount}₸ (не кратно 100). Данные: {data}")
        raise HTTPException(status_code=400, detail="Amount must be multiple of 100.")

    games = amount // 100

    send_telegram_message(
        f"💸 Оплата Kaspi!\n"
        f"Сумма: {amount}₸\n"
        f"Игры: {games}\n"
        f"Данные: {data}"
    )

    print(f"Надо запустить {games} игр.")

    return {"ok": True, "amount": amount, "games": games}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Главная страница."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kaspi Server</title>
        <script>
            async function testPayment() {
                const response = await fetch("/payment", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ amount: 300, note: "Тест от кнопки" })
                });
                const result = await response.json();
                alert("Тест отправлен! Ответ: " + JSON.stringify(result));
            }
        </script>
    </head>
    <body style="text-align:center; font-family:sans-serif; margin-top:80px;">
        <h1>✅ Kaspi-сервер работает</h1>
        <p>Готов к приёму оплат через Kaspi QR</p>
        <button onclick="testPayment()" style="margin-top:30px; padding:10px 20px; font-size:18px;">🧪 Тест оплаты</button>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
