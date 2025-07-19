from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import requests, sqlite3, os
from datetime import datetime

app = FastAPI()

# --- КОНФИГ ---
TELEGRAM_BOT_TOKEN = "8135133326:AAH1sRHovfzjRcyeDGqeCALoMF_qvwS4C6k"
TELEGRAM_CHAT_ID = "5070282357"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "ramazan2025"

DB_FILE = "payments.db"
authorized_ips = set()


# --- ИНИЦИАЛИЗАЦИЯ БД ---
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT,
                amount INTEGER,
                games INTEGER,
                timestamp TEXT,
                raw_json TEXT
            )
        """)
        conn.commit()
        conn.close()

init_db()


# --- ОТПРАВКА В TELEGRAM ---
def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка Telegram:", e)


# --- СОХРАНЕНИЕ В БД ---
def save_payment(payment_id, amount, games, raw_json):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO payments (payment_id, amount, games, timestamp, raw_json) VALUES (?, ?, ?, ?, ?)",
                   (payment_id, amount, games, datetime.now().isoformat(), str(raw_json)))
    conn.commit()
    conn.close()


# --- ПАРСИНГ СУММЫ ---
def parse_amount(data: dict) -> int:
    try:
        return int(float(data.get("data", {}).get("amount", 0)))
    except:
        return 0


# --- ВЕБ-ИНТЕРФЕЙС: ВХОД ---
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return """
    <html><head><title>Kaspi Вход</title></head><body>
    <form method="post" action="/login">
        <input name="username" placeholder="Логин" required><br>
        <input name="password" placeholder="Пароль" type="password" required><br>
        <button type="submit">Войти</button>
    </form></body></html>
    """


# --- ЛОГИН ---
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        authorized_ips.add(request.client.host)
        return RedirectResponse("/panel", status_code=302)
    return HTMLResponse("Неверные данные", status_code=401)


# --- ПАНЕЛЬ ---
@app.get("/panel", response_class=HTMLResponse)
async def panel(request: Request):
    if request.client.host not in authorized_ips:
        return RedirectResponse("/", status_code=302)

    return """
    <html><body>
    <h2>Панель управления</h2>
    <form method="post" action="/test">
        <button type="submit">Тест оплата</button>
    </form>
    <form method="post" action="/logout">
        <button type="submit">Выйти</button>
    </form>
    </body></html>
    """


# --- ВЫХОД ---
@app.post("/logout")
async def logout(request: Request):
    authorized_ips.discard(request.client.host)
    return RedirectResponse("/", status_code=302)


# --- ТЕСТОВАЯ ОПЛАТА ---
@app.post("/test")
async def test_payment():
    test_data = {
        "event": "payment.success",
        "data": {
            "paymentId": "TEST123",
            "amount": 500,
            "qrId": "kaspi-test",
            "timestamp": datetime.now().isoformat()
        }
    }
    return await payment_handler(Request(scope={"type": "http"}, receive=None), test_data)


# --- ПРИЁМ НАСТОЯЩЕЙ ОПЛАТЫ ---
@app.post("/payment")
async def payment_handler(request: Request, data: dict = None):
    if not data:
        data = await request.json()

    print("Получено:", data)

    amount = parse_amount(data)
    if amount <= 0:
        send_telegram_message(f"⚠️ Нет суммы!\n{data}")
        raise HTTPException(status_code=400, detail="Нет суммы.")

    if amount % 100 != 0:
        send_telegram_message(f"⚠️ Неправильная сумма: {amount}₸ (не кратна 100)")
        raise HTTPException(status_code=400, detail="Сумма должна быть кратна 100.")

    games = amount // 100
    payment_id = data.get("data", {}).get("paymentId", "неизвестно")
    save_payment(payment_id, amount, games, data)

    send_telegram_message(
        f"💸 Оплата Kaspi!\n"
        f"Сумма: {amount}₸\n"
        f"Игры: {games}\n"
        f"ID: {payment_id}"
    )

    return {"ok": True, "amount": amount, "games": games}
