from aiogram import F, Router
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import keyboards as kb
from utils import choose_place, create_timetable, create_table_separate_rows

router = Router()

ADMIN_IDS = {"1377739047", "263585469","1398362563"}  # Черников Денис, Захарова Олеся, Маришка
DENIS_ID = "1377739047"

class AdminStates(StatesGroup):
    waiting_name_delete = State()


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
async def set_place(message: Message):
    await message.answer("Выберите место:", reply_markup=kb.main)

@router.message(Command('timetable_text'))
async def timetable_text(message: Message):
    text = (
        "📋 <b>РАСПИСАНИЕ ДЕЖУРСТВА</b>\n\n"
        "🍽 <b>СТОЛОВАЯ:</b>\n" + create_timetable(1) + "\n\n"
        "🚪 <b>ВХОД:</b>\n" + create_timetable(2) + "\n\n"
        "🏀 <b>СПОРТЗАЛ:</b>\n" + create_timetable(3) + "\n\n"
        "🏢 <b>2 ЭТАЖ:</b>\n"
        "Левое крыло: " + create_timetable(4) + "\n"
        "Рекреация: " + create_timetable(5) + "\n"
        "Правое крыло: " + create_timetable(6) + "\n\n"
        "🏢 <b>3 ЭТАЖ:</b>\n"
        "Левое крыло: " + create_timetable(7) + "\n"
        "Рекреация: " + create_timetable(8) + "\n"
        "Правое крыло: " + create_timetable(9) + "\n\n"
        "🏢 <b>4 ЭТАЖ:</b>\n"
        "Левое крыло: " + create_timetable(10) + "\n"
        "Рекреация: " + create_timetable(11) + "\n"
        "Правое крыло: " + create_timetable(12)
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

class AddStudentStates(StatesGroup):
    waiting_place = State()
    waiting_name = State()


@router.message(Command('add_student'))
async def add_student_start(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("У вас нет прав")
        return
    await message.answer("Выберите место:", reply_markup=kb.main)
    await state.set_state(AddStudentStates.waiting_place)


@router.message(AddStudentStates.waiting_place, F.text.in_(places.keys()))
async def add_student_place(message: Message, state: FSMContext):
    await state.update_data(place=message.text)
    await message.answer("Введите имя и фамилию ученика:")
    await state.set_state(AddStudentStates.waiting_name)


@router.message(AddStudentStates.waiting_place)
async def add_student_wrong_place(message: Message):
    await message.answer("Пожалуйста, выберите место из предложенных кнопок")


@router.message(AddStudentStates.waiting_name)
async def add_student_confirm(message: Message, state: FSMContext):
    from database import Session
    from models import Users
    from sqlalchemy import select, update

    name = message.text.strip()
    admin_name = message.from_user.full_name
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

        if str(message.from_user.id) != DENIS_ID:
            await message.bot.send_message(
                DENIS_ID,
                f"🔔 <b>Действие админа</b>\n"
                f"Администратор: {admin_name}\n"
                f"Действие: записал(а) на дежурство\n"
                f"Ученик: {name}\n"
                f"Место: {place_text}",
                parse_mode="HTML"
            )

    await state.clear()

class SickStates(StatesGroup):
    waiting_name_add = State()
    waiting_name_remove = State()


@router.message(Command('add_sick'))
async def sick_add_start(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("У вас нет прав")
        return
    await message.answer("Введите имя и фамилию заболевшего:")
    await state.set_state(SickStates.waiting_name_add)


@router.message(SickStates.waiting_name_add)
async def sick_add_confirm(message: Message, state: FSMContext):
    from database import Session
    from models import Users
    from sqlalchemy import select, update

    name = message.text.strip()
    admin_name = message.from_user.full_name

    with Session() as session:
        user = session.execute(
            select(Users).where(Users.name == name)
        ).scalar()

        if user is None:
            await message.answer("Такого человека в базе нет, ты точно правильно написал(-а)?")
        elif user.is_sick:
            await message.answer(f"{name} уже в списке больных")
        else:
            session.execute(
                update(Users).where(Users.name == name).values(is_sick=True, place_id=None)
            )
            session.commit()
            await message.answer(f"{name} добавлен(а) в список больных ✅")
            if str(message.from_user.id) != DENIS_ID:
                await message.bot.send_message(
                    DENIS_ID,
                    f"🔔 <b>Действие админа</b>\n"
                    f"Администратор: {admin_name}\n"
                    f"Действие: добавил(а) в список больных\n"
                    f"Ученик: {name}",
                    parse_mode="HTML"
                )

    await state.clear()


@router.message(Command('heal'))
async def sick_remove_start(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("У вас нет прав")
        return
    await message.answer("Введите имя и фамилию выздоровевшего:")
    await state.set_state(SickStates.waiting_name_remove)


@router.message(SickStates.waiting_name_remove)
async def sick_remove_confirm(message: Message, state: FSMContext):
    from database import Session
    from models import Users
    from sqlalchemy import select, update

    name = message.text.strip()
    admin_name = message.from_user.full_name

    with Session() as session:
        user = session.execute(
            select(Users).where(Users.name == name)
        ).scalar()

        if user is None:
            await message.answer("Такого человека в базе нет, ты точно правильно написал(-а)?")
        elif not user.is_sick:
            await message.answer(f"{name} и так не в списке больных")
        else:
            session.execute(
                update(Users).where(Users.name == name).values(is_sick=False)
            )
            session.commit()
            await message.answer(f"{name} убран(а) из списка больных ✅")
            if str(message.from_user.id) != DENIS_ID:
                await message.bot.send_message(
                    DENIS_ID,
                    f"🔔 <b>Действие админа</b>\n"
                    f"Администратор: {admin_name}\n"
                    f"Действие: убрал(а) из списка больных\n"
                    f"Ученик: {name}",
                    parse_mode="HTML"
                )

    await state.clear()

@router.message(Command('sick_show'))
async def sick_show(message: Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("У вас нет прав")
        return
    from database import Session
    from models import Users
    from sqlalchemy import select

    with Session() as session:
        users = session.execute(
            select(Users).where(Users.is_sick == True)
        ).scalars().all()

        if not users:
            await message.answer("Список больных пуст")
            return

        names = "\n".join([f"• {u.name}" for u in users])
        await message.answer(f" <b>Список больных:</b>\n{names}", parse_mode="HTML")

@router.message(F.text.in_(places.keys()))
async def handle_place(message: Message):
    text = message.text
    pl_id, max_people = places[text]
    await choose_place(message, pl_id, max_people)
