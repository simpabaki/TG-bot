import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from config import SHEET_NAME
from handlers import router
from gsheet import get_config, update_user_status  # ← добавили функцию обновления

async def start_bot():
    config = get_config(SHEET_NAME)
    TOKEN = config['bot_token']

    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery):
        action, user_id = callback.data.split("_")
        user_id = int(user_id)

        if action == "approve":
            # Обновляем статус в Google Таблице
            update_user_status(SHEET_NAME, user_id, "approved")

            # Отправляем ссылку пользователю
            await bot.send_message(
                chat_id=user_id,
                text=f"{config['approve_text']}\n{config['mini_course_link']}"
            )
            await callback.message.answer("✅ Пользователь получил ссылку.")
        
        elif action == "reject":
            # Обновляем статус в Google Таблице
            update_user_status(SHEET_NAME, user_id, "rejected")

            # Уведомляем пользователя
            await bot.send_message(
                chat_id=user_id,
                text=config['reject_text']
            )
            await callback.message.answer("❌ Пользователь получил отказ.")

        await callback.answer()

    await dp.start_polling(bot)

if name == "main":
    import threading
    from server import start_api_server
    threading.Thread(target=start_api_server).start()
    asyncio.run(start_bot())
