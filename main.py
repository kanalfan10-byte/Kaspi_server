from fastapi import FastAPI, Request, HTTPException
import requests

app = FastAPI()

# --- ТВОЙ TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8135133326:AAH1sRHovfzjRcyeDGqeCALoMF_qvwS4C6k"
TELEGRAM_CHAT_ID = "5070282357"

def send_telegram_message(text: str):
    """Отправка сообщения в твой Telegram чат."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

def parse_amount(data: dict) -> int:
    """
    Пытаемся достать сумму из разных полей.
    Возвращаем сумму в тенге (целое число) или 0.
    """
    # Популярные названия полей: amount, sum, value, total
    for key in ("amount", "sum", "value", "total"):
        if key in data:
            try:
                return int(float(data[key]))
            except Exception:
                pass
    return 0

@app.post("/payment")
async def payment_handler(request: Request):
    data = await request.json()
    print("Получено:", data)

    amount = parse_amount(data)
    if amount <= 0:
        # нет суммы – игнор
        send_telegram_message(f"⚠️ Платёж без суммы: {data}")
        raise HTTPException(status_code=400, detail="No valid amount in JSON.")

    # проверка кратности 100
    if amount % 100 != 0:
        send_telegram_message(f"⚠️ Неправильная сумма {amount}₸ (не кратно 100). Данные: {data}")
        raise HTTPException(status_code=400, detail="Amount must be multiple of 100.")

    games = amount // 100

    # уведомление
    send_telegram_message(
        f"💸 Оплата Kaspi!\n"
        f"Сумма: {amount}₸\n"
        f"Игры: {games}\n"
        f"Данные: {data}"
    )

    # пока ESP32 нет — просто печать. Потом сюда добавим запрос на автомат.
    print(f"Надо запустить {games} игр (ESP32 позже).")

    return {"ok": True, "amount": amount, "games": games}
