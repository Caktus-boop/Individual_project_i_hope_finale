from aiogram import F, Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command

import keyboards as kb
from utils import choose_place, create_timetable, create_table_separate_rows

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот дежурств активирован")


@router.message(Command('set_place'))
async def set_place(message: Message):
    await message.answer("Выберите место:", reply_markup=kb.main)


places = {
    "Столовая": (1, 4),
    "ВХОД": (2, 3),
    "Спортзал": (3, 2),
    "Левое крыло(2)": (4, 2),
    "Рекреация(2)": (5, 2),
    "Правое крыло(2)": (6, 2),
    "Левое крыло(3)": (7, 2),
    "Рекреация(3)": (8, 2),
    "Правое крыло(3)": (9, 2),
    "Левое крыло(4)": (10, 2),
    "Рекреация(4)": (11, 2),
    "Правое крыло(4)": (12, 2),
}


from aiogram import F

@router.message(F.text.in_(places.keys()))
async def handle_place(message: Message):
    text = message.text
    pl_id, max_people = places[text]
    await choose_place(message, pl_id, max_people)

@router.message(Command('timetable_text'))
async def timetable_text(message: Message):

    text = (
        "📋 <b>РАСПИСАНИЕ ДЕЖУРСТВА</b>\n\n"

        "🍽 <b>СТОЛОВАЯ:</b>\n" + create_timetable(1) + "\n\n"
        "🚪 <b>ВХОД:</b>\n" + create_timetable(2) + "\n\n"
        "🏀 <b>СПОРТЗАЛ:</b>\n" + create_timetable(3) + "\n\n"

        "🏢 <b>2 ЭТАЖ:</b>\n"
        "Левое Крыло: " + create_timetable(4) + "\n"
        "Рекреация: " + create_timetable(5) + "\n"
        "Правое Крыло: " + create_timetable(6) + "\n\n"

        "🏢 <b>3 ЭТАЖ:</b>\n"
        "Левое Крыло: " + create_timetable(7) + "\n"
        "Рекреация: " + create_timetable(8) + "\n"
        "Правое Крыло: " + create_timetable(9) + "\n\n"

        "🏢 <b>4 ЭТАЖ:</b>\n"
        "Левое Крыло: " + create_timetable(10) + "\n"
        "Рекреация: " + create_timetable(11) + "\n"
        "Правое Крыло: " + create_timetable(12)
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command('timetable_image'))
async def timetable_image(message: Message):
    create_table_separate_rows()
    photo = FSInputFile("table_final.png")
    await message.answer_photo(photo)

#Админка
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ADMIN_IDS = {"1377739047", "263585469"}  # Черников Денис, Захарова Олеся

class AdminStates(StatesGroup):
    waiting_name_delete = State()
    waiting_place = State()
    waiting_name_add = State()

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="➕ Добавить", callback_data="admin_add"),
        InlineKeyboardButton(text="➖ Удалить", callback_data="admin_delete"),
    ]
])

@router.message(Command('admin'))
async def admin_panel(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("У вас нет доступа")
        return
    await message.answer("Панель администратора:", reply_markup=admin_keyboard)

from aiogram.types import CallbackQuery

@router.callback_query(F.data == "admin_delete")
async def admin_delete_start(callback: CallbackQuery, state: FSMContext):
    if str(callback.from_user.id) not in ADMIN_IDS:
        return
    await callback.message.answer("Введите имя и фамилию ученика которого хотите снять с дежурства:")
    await state.set_state(AdminStates.waiting_name_delete)
    await callback.answer()

@router.message(AdminStates.waiting_name_delete)
async def admin_delete_confirm(message: Message, state: FSMContext):
    from database import Session
    from models import Users
    from sqlalchemy import select

    name = message.text.strip()
    with Session() as session:
        user = session.execute(
            select(Users).where(Users.name == name)
        ).scalar()

        if user is None:
            await message.answer("Такого человека в базе нет, ты точно правильно написал(-а)?")
        elif user.place_id is None:
            await message.answer(f"{name} и так не записан(а) на дежурство")
        else:
            user.place_id = None
            session.commit()
            await message.answer(f"{name} снят(а) с дежурства ✅")

    await state.clear()

@router.callback_query(F.data == "admin_add")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    if str(callback.from_user.id) not in ADMIN_IDS:
        return
    await callback.message.answer("Выберите место:", reply_markup=kb.main)
    await state.set_state(AdminStates.waiting_place)
    await callback.answer()

@router.message(AdminStates.waiting_place, F.text.in_(places.keys()))
async def admin_add_place(message: Message, state: FSMContext):
    await state.update_data(place=message.text)
    await message.answer("Введите имя и фамилию ученика:")
    await state.set_state(AdminStates.waiting_name_add)

@router.message(AdminStates.waiting_name_add)
async def admin_add_confirm(message: Message, state: FSMContext):
    from database import Session
    from models import Users
    from sqlalchemy import select, update

    name = message.text.strip()
    data = await state.get_data()
    place_text = data.get("place")
    pl_id, max_people = places[place_text]

    with Session() as session:
        user = session.execute(
            select(Users).where(Users.name == name)
        ).scalar()

        if user is None:
            await message.answer("Такого человека в базе нет, ты точно правильно написал(-а)?")
            await state.clear()
            return

        if user.place_id is not None:
            await message.answer(f"{name} уже записан(а) на дежурство")
            await state.clear()
            return

        busy_count = session.execute(
            select(Users).where(Users.place_id == pl_id)
        ).scalars().all()

        if len(busy_count) >= max_people:
            await message.answer("Это место уже занято")
            await state.clear()
            return

        session.execute(
            update(Users)
            .where(Users.name == name)
            .values(place_id=pl_id)
        )
        session.commit()
        await message.answer(f"{name} записан(а) на {place_text} ✅")

    await state.clear()

    with Session() as session:
        user = session.execute(
            select(Users).where(Users.name == name)
        ).scalar()

        if user is None:
            await message.answer("Такого человека в базе нет, ты точно правильно написал(-а)?")
            await state.clear()
            return

        if user.place_id is not None:
            await message.answer(f"{name} уже записан(а) на дежурство")
            await state.clear()
            return

        busy_count = session.execute(
            select(Users).where(Users.place_id == pl_id)
        ).scalars().all()

        if len(busy_count) >= max_people:
            await message.answer("Это место уже занято")
            await state.clear()
            return

        user.place_id = pl_id
        session.commit()
        await message.answer(f"{name} записан(а) на {place_text} ✅")

    await state.clear()
