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
            await message.answer("Место занято")
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
        names = session.execute(
            select(Users.name).where(Users.place_id == pl_id)
        ).all()

        return ", ".join([n[0] for n in names])


def create_table_separate_rows():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis("off")

    data = []

    for i in range(1, 13):
        data.append([f"{i}", create_timetable(i)])

    table = ax.table(cellText=data, loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)

    plt.savefig("table_final.png", dpi=300, bbox_inches="tight")