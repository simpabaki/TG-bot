from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from config import SHEET_NAME
from states import Form
from gsheet import get_config, save_user_data

router = Router()

@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    config = get_config(SHEET_NAME)
    # Показываем приветствие и обычную кнопку «Начало»
    await message.answer(
        config['welcome_text'],
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Начало")]],
            resize_keyboard=True
        )
    )
    # Состояние не ставим — начнём после нажатия «Начало»

@router.message(F.text == "Начало")
async def begin(message: types.Message, state: FSMContext):
    config = get_config(SHEET_NAME)
    # После «Начало» просим согласие и показываем кнопку «✅ Согласен»
    await message.answer(
        config['consent_text'],
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="✅ Согласен")]],
            resize_keyboard=True
        )
    )
    await state.set_state(Form.consent)

@router.message(Form.consent, F.text == "✅ Согласен")
async def got_consent(message: types.Message, state: FSMContext):
    config = get_config(SHEET_NAME)
    await message.answer(
        config['ask_full_name'],
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Form.full_name)

@router.message(Form.full_name)
async def get_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    config = get_config(SHEET_NAME)
    await message.answer(config['ask_phone'])
    await state.set_state(Form.phone)

@router.message(Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    config = get_config(SHEET_NAME)
    await message.answer(config['ask_screenshot'])
    await state.set_state(Form.waiting_for_screenshot)

@router.message(Form.waiting_for_screenshot, F.photo)
async def get_screenshot(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photo_id = message.photo[-1].file_id
    username = message.from_user.username or "не указан"
    config = get_config(SHEET_NAME)
    admin_id = int(config['admin_id'])

    save_user_data(SHEET_NAME, message.from_user.id, username, user_data['full_name'], user_data['phone'], "pending")

    caption = (
        f"Скрин на проверку\n"
        f"ФИО: {user_data['full_name']}\n"
        f"Тел: {user_data['phone']}\n"
        f"Ник: @{username}\n"
        f"ID: {message.from_user.id}"
    )

    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{message.from_user.id}"),
            types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{message.from_user.id}")
        ]
    ])

    await message.bot.send_photo(chat_id=admin_id, photo=photo_id, caption=caption, reply_markup=buttons)
    await message.answer(config['wait_review_text'])
