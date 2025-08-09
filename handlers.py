from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from config import SHEET_NAME
from states import Form
from gsheet import get_config, save_user_data, update_user_status
from aiogram import Dispatcher
from aiogram.fsm.storage.base import StorageKey

router = Router()

@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    config = get_config(SHEET_NAME)
    await message.answer(
        config['welcome_text'],
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="✅ Согласен")]],
            resize_keyboard=True
        )
    )
    await state.set_state(Form.consent)

@router.message(F.text == "✅ Согласен")
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

# --- ПРИШЛО ФОТО (нормальный путь)
@router.message(Form.waiting_for_screenshot, F.photo)
async def get_screenshot(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photo_id = message.photo[-1].file_id
    username = message.from_user.username or "не указан"
    config = get_config(SHEET_NAME)
    admin_id = int(config['admin_id'])

    # Сохраняем в таблицу
    save_user_data(
        SHEET_NAME,
        message.from_user.id,
        username,
        user_data['full_name'],
        user_data['phone'],
        "pending"
    )

    caption = (
        "Скрин на проверку\n"
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

    # Пытаемся отправить админу, при ошибке всё равно отвечаем пользователю
    try:
        await message.bot.send_photo(chat_id=admin_id, photo=photo_id, caption=caption, reply_markup=buttons)
    except Exception:
        await message.answer("⚠️ Не удалось отправить скрин администратору. Попробуйте позже.")
    else:
        await message.answer(config['wait_review_text'])
    finally:
        await state.clear()

# --- ПРИШЛО НЕ ФОТО (подсказка и остаёмся в этом же состоянии)
@router.message(Form.waiting_for_screenshot, ~F.photo)
async def not_a_screenshot(message: types.Message):
    config = get_config(SHEET_NAME)
    await message.answer(
        config.get('not_screenshot_text', "это не скрин, пришлите скрин с отзывом")
    )

# ===== Админские колбэки =====

# Клавиатура "Обработано"
processed_kb = types.InlineKeyboardMarkup(
    inline_keyboard=[[types.InlineKeyboardButton(text="Обработано", callback_data="processed")]]
)

@router.callback_query(F.data.startswith("approve_"))
async def approve_cb(callback: types.CallbackQuery):
    config = get_config(SHEET_NAME)
    user_id = int(callback.data.split("_", 1)[1])

    # (не критично) уведомляем пользователя
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"{config['approve_text']}\n{config.get('mini_course_link','')}"
        )
    except Exception:
        pass
    finally:
        # всегда меняем клавиатуру у админа
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=processed_kb
            )
        except Exception:
            pass
        await callback.answer("Одобрено")
    # 2) обновляем статус в таблице
    try:
        update_user_status(SHEET_NAME, user_id, "одобрено")
    except Exception:
        pass

    # 3) меняем кнопки у админа на "Обработано"
    #try:
        #await callback.message.edit_reply_markup(
            #reply_markup=types.InlineKeyboardMarkup(
                #inline_keyboard=[[types.InlineKeyboardButton(text="Обработано", callback_data="processed")]]
            #)
        #)
    #except Exception:
        #try:
            #await callback.message.edit_caption(
                #caption=callback.message.caption or "",
                #reply_markup=types.InlineKeyboardMarkup(
                    #inline_keyboard=[[types.InlineKeyboardButton(text="Обработано", callback_data="processed")]]
                #)
            #)
       # except Exception:
           # pass

   # await callback.answer("Одобрено")


@router.callback_query(F.data.startswith("reject_"))
async def reject_cb(callback: types.CallbackQuery):
    config = get_config(SHEET_NAME)
    user_id = int(callback.data.split("_", 1)[1])

    # 1) Сбрасываем и ставим пользователю шаг согласия (старт)
    try:
        dp = Dispatcher.get_current()
        ctx = FSMContext(
            storage=dp.storage,
            key=StorageKey(bot_id=callback.bot.id, chat_id=user_id, user_id=user_id)
        )
        await ctx.clear()
        await ctx.set_state(Form.consent)  # через FSMContext — корректно для v3
    except Exception as e:
        print("reject_cb FSM error:", e)

    # 2) Шлём «отклонено» + снова стартовый экран
    try:
        await callback.bot.send_message(chat_id=user_id, text=config['reject_text'])
        await callback.bot.send_message(
            chat_id=user_id,
            text=config['welcome_text'],
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="✅ Согласен")]],
                resize_keyboard=True
            )
        )
    except Exception as e:
        print("reject_cb send_message error:", e)

    # 3) Обновляем статус в таблице
    try:
        update_user_status(SHEET_NAME, user_id, "отклонено")
    except Exception as e:
        print("reject_cb sheet error:", e)

    # 4) Меняем кнопки у админа на «Обработано»
    try:
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=processed_kb
        )
    except Exception as e:
        print("reject_cb markup error:", e)

    await callback.answer("Отклонено")
