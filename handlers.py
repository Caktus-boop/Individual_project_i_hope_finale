from aiogram import F, Router
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import keyboards as kb
from utils import choose_place, create_timetable, create_table_separate_rows

router = Router()

ADMIN_IDS = {"1377739047", "263585469"}  # Черников Денис, Захарова Олеся
DENIS_ID = "1377739047"

class AdminStates(StatesGroup):
    waiting_name_delete = State()

class UserStates(StatesGroup):
    choosing_place = State()

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


@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот дежурств активирован")


@router.message(Command('set_place'))
async def set_place(message: Message, state: FSMContext):
    await message.answer("Выберите место:", reply_markup=kb.main)
    await state.set_state(UserStates.choosing_place)


@router.message(UserStates.choosing_place, F.text.in_(places.keys()))
async def handle_place(message: Message, state: FSMContext):
    text = message.text
    pl_id, max_people = places[text]
    await choose_place(message, pl_id, max_people)
    await state.clear()


@router.message(UserStates.choosing_place)
async def handle_wrong_place(message: Message):
    await message.answer("Пожалуйста, выберите место из предложенных кнопок")


@router.message(Command('timetable_text'))
async def timetable_text(message: Message):
    text = (
        "<b>РАСПИСАНИЕ ДЕЖУРСТВА</b>\n\n"
        "<b>СТОЛОВАЯ:</b>\n" + create_timetable(1) + "\n\n"
        "<b>ВХОД:</b>\n" + create_timetable(2) + "\n\n"
        "<b>СПОРТЗАЛ:</b>\n" + create_timetable(3) + "\n\n"
        "<b>2 ЭТАЖ:</b>\n"
        "Левое Крыло: " + create_timetable(4) + "\n"
        "Рекреация: " + create_timetable(5) + "\n"
        "Правое Крыло: " + create_timetable(6) + "\n\n"
        "<b>3 ЭТАЖ:</b>\n"
        "Левое Крыло: " + create_timetable(7) + "\n"
        "Рекреация: " + create_timetable(8) + "\n"
        "Правое Крыло: " + create_timetable(9) + "\n\n"
        "<b>4 ЭТАЖ:</b>\n"
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


@router.message(Command('delete'))
async def admin_delete_start(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("У вас нет доступа")
        return
    await message.answer("Введите имя и фамилию ученика которого хотите снять с дежурства:")
    await state.set_state(AdminStates.waiting_name_delete)


@router.message(AdminStates.waiting_name_delete)
async def admin_delete_confirm(message: Message, state: FSMContext):
    from database import Session
    from models import Users
    from sqlalchemy import select

    name = message.text.strip()
    admin_name = message.from_user.full_name

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
            if str(message.from_user.id) != DENIS_ID:
                await message.bot.send_message(
                    DENIS_ID,
                    f"🔔 <b>Действие админа</b>\n"
                    f"Администратор: {admin_name}\n"
                    f"Действие: снял(а) с дежурства\n"
                    f"Ученик: {name}",
                    parse_mode="HTML"
                )

    await state.clear()
