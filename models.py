from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str]
    name: Mapped[str]
    place_id: Mapped[int | None] = mapped_column(
        ForeignKey('timetable.id', ondelete='CASCADE')
    )


class Timetable(Base):
    __tablename__ = 'timetable'

    id: Mapped[int] = mapped_column(primary_key=True)
    floor: Mapped[int]
    pos: Mapped[int]