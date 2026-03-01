import asyncio
import os
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from sqlalchemy import update, select

from handlers import router
from database import Session, engine
from models import Users, Base

logging.basicConfig(level=logging.INFO)

# Создание таблиц
Base.metadata.create_all(engine)


async def scheduler():
    while True:
        now = datetime.now()

        # Четверг 21:00
        if now.weekday() == 3 and now.hour == 21 and now.minute == 0:
            await random_place()

        # Суббота 00:00
        if now.weekday() == 5 and now.hour == 0 and now.minute == 0:
            await clear_timetable()

        await asyncio.sleep(60)


async def clear_timetable():
    with Session() as session:
        session.execute(update(Users).values(place_id=None))
        session.commit()


async def random_place():
    from random import choice

    with Session() as session:
        users = session.execute(
            select(Users).where(Users.place_id == None)
        ).scalars().all()

        places = list(range(1, 13))

        for user in users:
            rand_place = choice(places)

            count = session.execute(
                select(Users).where(Users.place_id == rand_place)
            ).scalars().all()

            max_people = 2
            if rand_place == 2:
                max_people = 3
            if rand_place == 1:
                max_people = 4

            if len(count) < max_people:
                session.execute(
                    update(Users)
                    .where(Users.id == user.id)
                    .values(place_id=rand_place)
                )
                session.commit()


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command='start', description='Запуск'),
        BotCommand(command='set_place', description='Выбрать место'),
        BotCommand(command='timetable_text', description='Посмотреть текст'),
        BotCommand(command='timetable_image', description='Посмотреть фото')
    ])

    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())