from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import requests

app = FastAPI()

# --- НАСТРОЙКИ ---
TELEGRAM_BOT_TOKEN = "8135133326:AAH1sRHovfzjRcyeDGqeCALoMF_qvwS4C6k"
TELEGRAM_CHAT_ID = "5070282357"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "ramazan2025"

# --- Хранилище авторизованных IP ---
authorized_ips = set()

# --- ОТПРАВКА В TELEGRAM ---
def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка Telegram:", e)

# --- ПАРСИНГ СУММЫ ---
def parse_amount(data: dict) -> int:
    for key in ("amount", "sum", "value", "total"):
        if key in data:
            try:
                return int(float(data[key]))
            except Exception:
                pass
    return 0

# --- СТРАНИЦА ВХОДА ---
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return """
    <html>
    <head>
        <title>Kaspi Вход</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh; padding: 20px; }
            form { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 360px; }
            input { margin: 10px 0; padding: 10px; width: 100%; border-radius: 6px; border: 1px solid #ccc; font-size: 16px; }
            button { background: #28a745; color: white; padding: 12px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; }
            h2 { text-align: center; color: #333; }
        </style>
    </head>
    <body>
        <form method="post" action="/login">
            <h2>Вход</h2>
            <input type="text" name="username" placeholder="Логин" required><br>
            <input type="password" name="password" placeholder="Пароль" required><br>
            <button type="submit">Войти</button>
        </form>
    </body>
    </html>
    """

# --- ЛОГИН ---
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    client_ip = request.client.host
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        authorized_ips.add(client_ip)
        return RedirectResponse(url="/panel", status_code=302)
    return HTMLResponse("<h3>❌ Неверный логин или пароль.</h3><a href='/'>Назад</a>", status_code=401)

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
@app.get("/panel", response_class=HTMLResponse)
async def control_panel(request: Request):
    client_ip = request.client.host
    if client_ip not in authorized_ips:
        return RedirectResponse(url="/", status_code=302)

    return """
    <html>
    <head>
        <title>Панель Kaspi</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; background: #eef2f7; display: flex; justify-content: center; align-items: center; height: 100vh; padding: 20px; }
            .box { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; width: 100%; max-width: 400px; }
            h2 { color: #333; }
            button { padding: 12px 24px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 8px; cursor: pointer; margin-top: 10px; width: 100%; }
            button:hover { background: #0056b3; }
            .exit { background: #dc3545; }
            .exit:hover { background: #b52a37; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>Kaspi Панель</h2>
            <form method="post" action="/test">
                <button type="submit">💸 Отправить тест оплаты</button>
            </form><br>
            <form method="post" action="/logout">
                <button type="submit" class="exit">🚪 Выйти</button>
            </form>
        </div>
    </body>
    </html>
    """

# --- ВЫХОД ---
@app.post("/logout")
async def logout(request: Request):
    client_ip = request.client.host
    authorized_ips.discard(client_ip)
    return RedirectResponse(url="/", status_code=302)

# --- ТЕСТ ОПЛАТЫ ---
@app.post("/test")
async def test_payment():
    dummy_data = {"amount": 300, "from": "ТЕСТЕР"}
    amount = parse_amount(dummy_data)
    games = amount // 100
    send_telegram_message(f"💸 ТЕСТОВАЯ ОПЛАТА!\nСумма: {amount}₸\nИгры: {games}\nДанные: {dummy_data}")
    return RedirectResponse(url="/panel", status_code=302)

# --- НАСТОЯЩАЯ ОПЛАТА ---
@app.post("/payment")
async def payment_handler(request: Request):
    data = await request.json()
    print("Получено:", data)

    amount = parse_amount(data)
    if amount <= 0:
        send_telegram_message(f"⚠️ Платёж без суммы: {data}")
        raise HTTPException(status_code=400, detail="Нет суммы.")

    if amount % 100 != 0:
        send_telegram_message(f"⚠️ Неправильная сумма {amount}₸ (не кратно 100). Данные: {data}")
        raise HTTPException(status_code=400, detail="Сумма должна быть кратна 100.")

    games = amount // 100
    send_telegram_message(
        f"💸 Оплата Kaspi!\n"
        f"Сумма: {amount}₸\n"
        f"Игры: {games}\n"
        f"Данные: {data}"
    )
    return {"ok": True, "amount": amount, "games": games}
