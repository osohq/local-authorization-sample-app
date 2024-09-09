import os

from flask import Flask, request
from oso_cloud import Oso, Value
import sqlalchemy
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Mapped, mapped_column, Session

app = Flask(__name__)
oso = Oso(
    url=os.environ["OSO_URL"],
    api_key=os.environ["OSO_AUTH"],
    data_bindings="oso_local.yaml",
)
engine = create_engine("postgresql://localhost", echo=True)

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


@app.route("/api/users/<user_id>/cards")
def user_cards(user_id):
    past = request.args.get("past")
    sql_fragment = oso.list_local(Value("User", user_id), "card.read", "Card", "cards.manager_id")

    query = select(Card.card_id, Card.manager_id)
    if past is not None:
        query.filter(Card.card_id > past)
    query = query.filter(text(sql_fragment))
    query = query.order_by(Card.card_id)
    query = query.limit(30)

    with Session(engine) as session:
        cards = session.execute(query).mappings().all()
    return [dict(card) for card in cards]


@app.route("/api/users")
def users():
    past = request.args.get("past")

    query = select(User.user_id, User.manager_id)
    if past is not None:
        query.filter(User.user_id > past)
    query = query.order_by(User.user_id)
    query = query.limit(30)

    with Session(engine) as session:
        users = session.execute(query).mappings().all()

    return {
        "users": [dict(user) for user in users],
        "past": users[-1].user_id if users else None,
    }


@app.route("/users")
def hello_world():
    return "hello world"
