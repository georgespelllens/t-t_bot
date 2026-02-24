from aiogram.fsm.state import State, StatesGroup


class CorporateStates(StatesGroup):
    waiting_theater_name = State()
    waiting_city = State()
    waiting_headcount = State()
    waiting_format = State()
    waiting_tasks = State()
    confirming = State()
