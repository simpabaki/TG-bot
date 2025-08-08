from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from gsheet import get_config, save_user_to_sheet
from config import SHEET_NAME

router = Router()
config = get_config(SHEET_NAME)
admin_id = int(config["admin_id"])

@router.message(CommandStart())
async def start_handler(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Начать")]],
        resize_keyboard=True
    )
    await message.answer("Нажмите кнопку, чтобы начать", reply_markup=kb)

@router.message(F.text == "Начать")
async def ask_consent(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Согласен", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Для участия нужно согласие на обработку данных. Нажмите кнопку ниже:", reply_markup=kb)

@router.message(F.contact)
async def handle_contact(message: Message):
    user = message.from_user
    user_data = {
        "user_id": user.id,
        "full_name": user.full_name,
        "username": user.username or "",
        "phone_number": message.contact.phone_number
    }
    save_user_to_sheet(user_data)
    await message.answer("Спасибо! Пришлите, пожалуйста, фото отзыва.", reply_markup=ReplyKeyboardRemove())

@router.message(F.photo)
async def handle_photo(message: Message):
    photo_id = message.photo[-1].file_id
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{message.from_user.id}")
            ]
        ]
    )
    await message.bot.send_photo(
        chat_id=admin_id,
        photo=photo_id,
        caption=f"Новый отзыв от @{message.from_user.username or 'без username'}",
        reply_markup=inline_kb
    )
    await message.answer("Отзыв отправлен на модерацию!")

@router.message()
async def not_photo_handler(message: Message):
    await message.answer("Пожалуйста, отправьте фото отзыва.")

@router.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def handle_callback(callback: CallbackQuery):
    action, user_id = callback.data.split("_")
    user_id = int(user_id)

    if action == "approve":
        await callback.bot.send_message(chat_id=user_id, text=f"{config['approve_text']}
{config['mini_course_link']}")
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="✅ Обработано", callback_data="noop")]]
            )
        )
    elif action == "reject":
        await callback.bot.send_message(chat_id=user_id, text=config["reject_text"])
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ Отклонено", callback_data="noop")]]
            )
        )
    await callback.answer()
