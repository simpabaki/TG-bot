from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    consent = State()
    full_name = State()
    phone = State()
    waiting_for_screenshot = State()