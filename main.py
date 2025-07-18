from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

# --- ТВОЙ TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8135133326:AAH1sRHovfzjRcyeDGqeCALoMF_qvwS4C6k"
TELEGRAM_CHAT_ID = "5070282357"

# --- УЧЕТНЫЕ ДАННЫЕ ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "ramazan2025"

# Хранилище авторизованных сессий (просто по IP — примитивно)
authorized_ips = set()

# --- ОТПРАВКА В TELEGRAM ---
def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

# --- ПАРСИНГ СУММЫ ---
def parse_amount(data: dict) -> int:
    for key in ("amount", "sum", "value", "total"):
        if key in data:
            try:
                return int(float(data[key]))
            except Exception:
                pass
    return 0

# --- СТАРТОВАЯ СТРАНИЦА ---
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return """
    <html><body>
    <h2>Вход на сайт</h2>
    <form method=\"post\" action=\"/login\">
      Логин: <input type=\"text\" name=\"username\"><br>
      Пароль: <input type=\"password\" name=\"password\"><br>
      <input type=\"submit\" value=\"Войти\">
    </form>
    </body></html>
    """

# --- ОБРАБОТКА ЛОГИНА ---
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    client_ip = request.client.host
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        authorized_ips.add(client_ip)
        return RedirectResponse(url="/panel", status_code=302)
    return HTMLResponse("Неверный логин или пароль.", status_code=401)

# --- ПАНЕЛЬ (если авторизован) ---
@app.get("/panel", response_class=HTMLResponse)
async def control_panel(request: Request):
    client_ip = request.client.host
    if client_ip not in authorized_ips:
        return RedirectResponse(url="/", status_code=302)
    return """
    <html><body>
    <h2>Тест оплаты Kaspi</h2>
    <form method=\"post\" action=\"/test\">
      <input type=\"submit\" value=\"Отправить тест оплаты\">
    </form>
    </body></html>
    """

# --- ТЕСТОВАЯ ОПЛАТА ---
@app.post("/test")
async def test_payment():
    dummy_data = {"amount": 300, "from": "ТЕСТЕР"}
    amount = parse_amount(dummy_data)
    games = amount // 100
    send_telegram_message(f"💸 ТЕСТОВАЯ ОПЛАТА!\nСумма: {amount}₸\nИгры: {games}\nДанные: {dummy_data}")
    return RedirectResponse(url="/panel", status_code=302)

# --- НАСТОЯЩАЯ ОПЛАТА ОТ KASPI ---
@app.post("/payment")
async def payment_handler(request: Request):
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
    print(f"Надо запустить {games} игр (ESP32 позже).")
    return {"ok": True, "amount": amount, "games": games}
    
