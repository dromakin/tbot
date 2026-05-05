from aiogram.fsm.state import State, StatesGroup


class AskQuestionState(StatesGroup):
    waiting_text = State()


class CreateLectureState(StatesGroup):
    waiting_number = State()
    waiting_title = State()
    waiting_description = State()
    waiting_datetime = State()
    waiting_format = State()
    waiting_stream_url = State()
    waiting_materials_url = State()
