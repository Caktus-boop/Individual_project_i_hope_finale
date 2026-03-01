import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from datetime import datetime
from sqlalchemy import select, update
from aiogram.types import Message

from database import Session
from models import Users


async def choose_place(message: Message, pl_id: int, max_people=2):

    if datetime.now().weekday() == 4:
        await message.answer("В день дежурства запись закрыта")
        return

    with Session() as session:

        user = session.execute(
            select(Users).where(Users.tg_id == str(message.from_user.id))
        ).scalar()

        if not user:
            await message.answer("Вы не зарегистрированы")
            return

        count = session.execute(
            select(Users).where(Users.place_id == pl_id)
        ).scalars().all()

        if len(count) >= max_people:
            await message.answer("Это место уже занято")
            return

        session.execute(
            update(Users)
            .where(Users.tg_id == str(message.from_user.id))
            .values(place_id=pl_id)
        )
        session.commit()

        await message.answer("Вы записаны")


def create_timetable(pl_id: int):
    with Session() as session:
        place = select(Users.name).where(Users.place_id == pl_id)
        result = session.execute(place).all()

        names = ""
        for row in result:
            names += row[0] + ", "

        return names[:-2]


def create_table_separate_rows():
    places_row1 = ["СТОЛОВАЯ", "ВХОД", "СПОРТЗАЛ"]
    names_row1 = [
        create_timetable(1).replace(", ", "\n"),
        create_timetable(2).replace(", ", "\n"),
        create_timetable(3).replace(", ", "\n")
    ]

    places_row2 = ["КРЫЛО", "2 ЭТАЖ РЕКРЕАЦИЯ", "КРЫЛО"]
    names_row2 = [
        create_timetable(4).replace(", ", "\n"),
        create_timetable(5).replace(", ", "\n"),
        create_timetable(6).replace(", ", "\n")
    ]

    places_row3 = ["КРЫЛО", "3 ЭТАЖ РЕКРЕАЦИЯ", "КРЫЛО"]
    names_row3 = [
        create_timetable(7).replace(", ", "\n"),
        create_timetable(8).replace(", ", "\n"),
        create_timetable(9).replace(", ", "\n")
    ]

    places_row4 = ["КРЫЛО", "4 ЭТАЖ РЕКРЕАЦИЯ", "КРЫЛО"]
    names_row4 = [
        create_timetable(10).replace(", ", "\n"),
        create_timetable(11).replace(", ", "\n"),
        create_timetable(12).replace(", ", "\n")
    ]

    all_rows = [
        places_row1,
        names_row1,
        places_row2,
        names_row2,
        places_row3,
        names_row3,
        places_row4,
        names_row4,
    ]

    fig, ax = plt.subplots(figsize=(16, 14))
    ax.axis("tight")
    ax.axis("off")

    table = ax.table(cellText=all_rows, cellLoc="center", loc="center")

    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1, 8)

    for (i, j), cell in table.get_celld().items():
        if i % 2 == 0:
            cell.get_text().set_weight("bold")
            cell.get_text().set_fontsize(25)
            cell.set_facecolor("#e3f2fd")
            cell.set_height(0.1)
        else:
            cell.get_text().set_fontsize(20)
            cell.set_facecolor("#f5f5f5")
            cell.set_height(0.3)

        cell.set_edgecolor("#424242")
        cell.set_linewidth(1.5)

    plt.tight_layout()
    plt.savefig("table_final.png", dpi=300, bbox_inches="tight", facecolor="white")
