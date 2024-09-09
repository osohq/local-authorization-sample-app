import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column

class Base(sqlalchemy.orm.DeclarativeBase): ...

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "demo_app"}

    user_id: Mapped[str] = mapped_column(primary_key=True)
    manager_id: Mapped[str]


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = {"schema": "demo_app"}

    card_id: Mapped[str] = mapped_column(primary_key=True)
    manager_id: Mapped[str]
