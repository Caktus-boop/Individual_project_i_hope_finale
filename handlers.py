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


for text, (pl_id, max_people) in places.items():

    @router.message(F.text == text)
    async def handle_place(message: Message, pl_id=pl_id, max_people=max_people):
        await choose_place(message, pl_id, max_people)


@router.message(Command('timetable_text'))
async def timetable_text(message: Message):
    result = ""
    for i in range(1, 13):
        result += f"{i}: {create_timetable(i)}\n"
    await message.answer(result)


@router.message(Command('timetable_image'))
async def timetable_image(message: Message):
    create_table_separate_rows()
    photo = FSInputFile("table_final.png")
    await message.answer_photo(photo)