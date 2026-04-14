import asyncio
import os
import logging
from datetime import datetime
import aiohttp

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from sqlalchemy import update, select

from fastapi import FastAPI
import uvicorn

from handlers import router
from database import Session, engine
from models import Users, Base

logging.basicConfig(level=logging.INFO)

from sqlalchemy import text

Base.metadata.create_all(engine)

from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_sick BOOLEAN DEFAULT FALSE"))
        conn.commit()
    except Exception:
        pass
        
from sqlalchemy import select

def seed_students():
    students = [
      ("5274553435", "Головашов Александр"),
      ("263585469", "Захарова Олеся"),
      ("5272462695", "Ребдев Владимир"),
      ("1834321017", "Заблоцкая Дарья"),
      ("1377739047", "Черников Денис"),
      ("5103011143", "Жданова Мария"),
      ("6499705219", "Слезкин Андрей"),
      ("5482201891", "Микерина Мария"),
      ("869306765", "Павлова София"),
      ("1923053849", "Кононенко Арина"),
      ("5127186542", "Тузова Елизавета"),
      ("1643399283", "Унгуряну Емелина"),
      ("5404894731", "Смирнова Вера"),
      ("5419242333", "Чувашев Патрик"),
      ("5286740634", "Петровский Артём"),
      ("1745917525", "Кахоров Коил"),
      ("1147528459", "Левашева Александра"),
      ("6375084446", "Пропокенко Егор"),
      ("1750628026", "Исаев Михаил"),
      ("1522953852", "Полонейчик Роман"),
      ("5281471578", "Долев Алий"),
      ("2074542737", "Павлов Тимофей"),
      ("6090119655", "Аксёнова Маргарита"),
      ("1965208888", "Артемьев Михаил"),
      ("898040758", "Чижиков Артём"),
      ("1963703320", "Харьковский Ян"),
      ("5129101608", "Крамер Захар"),
      ("917219738", "Нейлис Алина"),
      ("5513999339", "Ариян Марина"),
      ("1675113168", "Семенов Лёша"),
      ("808056745", "Власова Юля"),
      ("1367290236", "Гришина Настя"),
      ("8721917051", "Сахань Артём")  
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


async def scheduler(bot):
    last_ran = {}
    while True:
        now = datetime.now()

        # Самопинг чтобы не засыпать
        try:
            async with aiohttp.ClientSession() as client:
                await client.get("https://duty-bot-ig46.onrender.com/")
        except Exception:
            pass

        key_clear = f"clear_{now.weekday()}_{now.hour}"
        key_random = f"random_{now.weekday()}_{now.hour}"

        if now.weekday() == 3 and now.hour == 17 and now.minute >= 30 and key_random not in last_ran:
            await random_place(bot)
            last_ran[key_random] = True

        if now.weekday() == 4 and now.hour == 20 and now.minute >= 59 and key_clear not in last_ran:
            await clear_timetable()
            last_ran[key_clear] = True

        await asyncio.sleep(55)


async def clear_timetable():
    logging.info("clear_timetable вызвана")
    with Session() as session:
        session.execute(update(Users).values(place_id=None))
        session.commit()
    logging.info("clear_timetable выполнена успешно")


async def random_place(bot=None):
    from random import shuffle

    EXCLUDED_IDS = {"1377739047"}  # Черников Денис — всегда без места

    with Session() as session:
        users = session.execute(
            select(Users).where(Users.place_id == None, Users.is_sick == False)
        ).scalars().all()

        excluded = [u for u in users if u.tg_id in EXCLUDED_IDS]
        to_assign = [u for u in users if u.tg_id not in EXCLUDED_IDS]

        shuffle(to_assign)

        place_limits = {
            1: 4, 2: 3, 3: 2, 4: 2, 5: 2, 6: 2,
            7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2
        }

        place_counts = {}
        for pl_id, limit in place_limits.items():
            count = session.execute(
                select(Users).where(Users.place_id == pl_id)
            ).scalars().all()
            place_counts[pl_id] = len(count)

        available_places = [
            pl_id for pl_id, limit in place_limits.items()
            if place_counts[pl_id] < limit
        ]

        for user in to_assign:
            if not available_places:
                break
            pl_id = available_places[0]
            session.execute(
                update(Users)
                .where(Users.id == user.id)
                .values(place_id=pl_id)
            )
            place_counts[pl_id] += 1
            if place_counts[pl_id] >= place_limits[pl_id]:
                available_places.pop(0)

        session.commit()

        hall_users = session.execute(
            select(Users).where(Users.place_id == 2)
        ).scalars().all()

        for u in hall_users:
            try:
                await bot.send_message(
                    u.tg_id,
                    " Ты дежуришь на <b>ВХОДЕ</b> завтра!",
                    parse_mode="HTML"
                )
            except Exception:
                pass

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

    asyncio.create_task(scheduler(bot))

    while True:
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logging.warning(f"Polling упал: {type(e).__name__}: {e}, перезапускаем через 5 секунд...")
            await asyncio.sleep(5)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
