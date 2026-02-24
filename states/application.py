from aiogram.fsm.state import State, StatesGroup


class ApplicationStates(StatesGroup):
    waiting_name = State()
    waiting_city = State()
    waiting_organization = State()
    waiting_referral = State()
    confirming = State()
