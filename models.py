from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str]
    name: Mapped[str]
    place_id: Mapped[int | None]
    is_sick: Mapped[bool] = mapped_column(default=False)
