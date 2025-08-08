import logging
import csv
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

API_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = YOUR_ADMIN_ID  # Замените на числовой user_id администратора
CSV_FILE = "clients.csv"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

def init_csv():
    try:
        with open(CSV_FILE, "x", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "username", "name", "phone", "submitted_at", "status", "reason", "file_id"])
    except FileExistsError:
        pass

def user_exists(user_id):
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return any(str(row["user_id"]) == str(user_id) for row in reader)

def add_user(data):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🚀 Начать", callback_data="begin")
    )
    await message.reply("Добро пожаловать! Нажмите кнопку ниже, чтобы начать.", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "begin")
async def begin_handler(callback_query: types.CallbackQuery):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Согласен", callback_data="agree")
    )
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, согласись на обработку персональных данных.", reply_markup=kb)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "agree")
async def agree_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("Вы согласились.")
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    await bot.send_message(callback_query.from_user.id, "Спасибо! Теперь пришлите, пожалуйста, скриншот отзыва в виде фотографии 📸")

@dp.message_handler(commands=["выгрузка"])
async def export_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply_document(open(CSV_FILE, "rb"))
    else:
        await message.reply("У вас нет прав на эту команду.")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    user = message.from_user
    if user_exists(user.id):
        await message.reply("Вы уже отправляли отзыв. Спасибо!")
        return

    file_id = message.photo[-1].file_id
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    username = f"@{user.username}" if user.username else ""
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    add_user([user.id, username, name, "", now, "ожидает", "", file_id])

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user.id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")
    )

    await bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=f"Отзыв от {username or name} (ID: {user.id})",
        reply_markup=kb
    )
    await message.reply("Спасибо! Ваш отзыв отправлен на проверку.")

@dp.callback_query_handler(lambda c: c.data.startswith(("approve_", "reject_")))
async def process_callback(callback_query: types.CallbackQuery):
    action, uid = callback_query.data.split("_")
    uid = int(uid)

    updated = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        for row in reader:
            if str(row["user_id"]) == str(uid):
                row["status"] = "одобрено" if action == "approve" else "отклонено"
                row["reason"] = "" if action == "approve" else "Не прошёл модерацию"
            updated.append(row)

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=updated[0].keys())
        writer.writeheader()
        writer.writerows(updated)

    caption = "✅ Обработано" if action == "approve" else "❌ Отказано"
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(caption, callback_data="noop")
        )
    )

    await callback_query.answer("Обновлено.")
    if action == "approve":
        await bot.send_message(uid, "Ваш отзыв одобрен! Спасибо 🌟")
    else:
        await bot.send_message(uid, "К сожалению, ваш отзыв не прошёл модерацию.")

# Обработка любых других сообщений (не фото)
@dp.message_handler()
async def unknown_message(message: types.Message):
    await message.reply("Пожалуйста, отправьте СКРИНШОТ отзыва в виде фотографии 📸")

if __name__ == "__main__":
    init_csv()
    executor.start_polling(dp, skip_updates=True)
