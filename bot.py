import asyncio
import os
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from sqlalchemy import update, select

from fastapi import FastAPI
import uvicorn

from handlers import router
from database import Session, engine
from models import Users, Base

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(engine)

from sqlalchemy import select

def seed_students():
    students = [
        ("1398362563", "Маришка"),
      ("5274553435", "Головашов Александр"),
      ("263585469", "Захарова Олеся")
      ("5272462695", "Ребдев Владимир")
      ("1834321017", "Заблоцкая Дарья")
      ("1377739047", "Черников Денис")
      ("5103011143", "Жданова Мария")
      ("6499705219", "Слезкин Андрей")
      ("5482201891", "Микерина Мария")
      ("869306765", "Павлова София")
      ("1923053849", "Кононенко Арина")
      ("5127186542", "Тузова Елизавета")
      ("1643399283", "Унгуряну Емелина")
      ("5404894731", "Смирнова Вера")
      ("5419242333", "Чувашев Патрик")
      ("5286740634", "Петровский Артём")
      ("1745917525", "Кахоров Коил")
      ("1147528459", "Левашева Александра")
      ("6375084446", "Пропокенко Егор")
      ("1750628026", "Исаев Михаил")
      ("1522953852", "Полонейчик Роман")
      ("5281471578", "Долев Алий")
      ("2074542737", "Павлов Тимофей")
      ("6090119655", "Аксёнова Маргорита")
      ("1965208888", "Артемьев Михаил")
      ("898040758", "Чижиков Артём")
      ("1963703320", "Харьковский Ян")
      ("5129101608", "Крамер Захар")
      ("917219738", "Нейлис Алина")
      ("5513999339", "Ариян Мария")
      ("1675113168", "Семенов Лёша")
      ("808056745", "Власова Юля")
      ("1367290236", "Гришина Настя")
        
    ]

    with Session() as session:
        for tg_id, name in students:
            exists = session.execute(
                select(Users).where(Users.tg_id == tg_id)
            ).scalar()

            if not exists:
                session.add(Users(tg_id=tg_id, name=name))

        session.commit()

seed_students()

app = FastAPI()


@app.get("/")
async def root():
    return {"status": "bot is running"}


async def scheduler():
    while True:
        now = datetime.now()

        if now.weekday() == 3 and now.hour == 21 and now.minute == 0:
            await random_place()

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


async def start_bot():
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


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
