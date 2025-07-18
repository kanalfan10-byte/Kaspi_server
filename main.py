from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/payment")
async def payment_handler(request: Request):
    data = await request.json()
    print("Получено:", data)
    return {"ok": True}
