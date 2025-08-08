from fastapi import FastAPI, Request
import uvicorn
import os

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import SHEET_NAME
from gsheet import get_config
from handlers import router

app = FastAPI()

# Получаем конфиг из таблицы
config = get_config(SHEET_NAME)
BOT_TOKEN = config["bot_token"]
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{os.environ.get('WEBHOOK_BASE')}{WEBHOOK_PATH}"

# Настраиваем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

@app.get("/")
def ping():
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

def start_api_server():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
