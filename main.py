import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from config import SHEET_NAME
from gsheet import get_config
from handlers import router

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
            await bot.send_message(chat_id=user_id, text=f"{config['approve_text']}
{config['mini_course_link']}")
            await callback.message.edit_reply_markup(
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[[types.InlineKeyboardButton("✅ Обработано", callback_data="noop")]]
                )
            )
            await callback.answer("Ссылка отправлена")

        elif action == "reject":
            await bot.send_message(chat_id=user_id, text=config['reject_text'])
            await callback.message.edit_reply_markup(
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[[types.InlineKeyboardButton("❌ Отказано", callback_data="noop")]]
                )
            )
            await callback.answer("Отказ отправлен")

    await dp.start_polling(bot)
