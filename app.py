import os

from flask import Flask, request
from oso_cloud import Oso, Value
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from model import Card, User

app = Flask(__name__)
oso = Oso(
    url=os.environ["OSO_URL"],
    api_key=os.environ["OSO_AUTH"],
    data_bindings="oso_local.yaml",
)
uri = os.environ["DATABASE_URL"]
engine = create_engine(uri, echo=True)


@app.route("/api/users/<user_id>/cards")
def api_user_cards(user_id):
    past = request.args.get("past")
    return get_user_cards(user_id, past)


def get_user_cards(user_id, past):
    LIMIT = 30
    sql_fragment = oso.list_local(Value("User", user_id), "card.read", "Card", "cards.card_id")

    query = select(Card.card_id, Card.manager_id)
    if past is not None:
        query = query.filter(Card.card_id > past)
    query = query.filter(text(sql_fragment))
    query = query.order_by(Card.card_id)
    query = query.limit(LIMIT)

    with Session(engine) as session:
        cards = session.execute(query).mappings().all()

    return {
        "cards": [dict(card) for card in cards],
        "past": cards[-1].card_id if cards and len(cards) == LIMIT else None,
    }


@app.route("/api/users")
def api_users():
    past = request.args.get("past")
    return get_users(past)


def get_users(past):
    query = select(User.user_id, User.manager_id, User.name)
    if past is not None:
        query = query.filter(User.user_id > past)
    query = query.order_by(User.user_id)
    query = query.limit(30)

    with Session(engine) as session:
        users = session.execute(query).mappings().all()

    return {
        "users": [dict(user) for user in users],
        "past": users[-1].user_id if users else None,
    }


def get_user(user_id):
    from sqlalchemy.orm import aliased
    user = aliased(User)
    manager = aliased(User, name="manager")
    query = select(user.user_id, user.manager_id, user.name, manager.name.label("manager_name"))
    query = query.outerjoin(manager, manager.user_id == user.manager_id)
    query = query.filter(user.user_id == user_id)

    with Session(engine) as session:
        user = session.execute(query).mappings().one_or_none()

    return user


page = """<html><head>
<style>
a {{
  text-decoration: none;
}}

a:hover {{
  text-decoration: underline;
}}
</style>
</head><body>{}</body></html>""".format

@app.route("/users")
def html_users():
    past = request.args.get("past")
    users_data = get_users(past)
    if not users_data['users']:
        return page("<h3>Users</h3><em>No results</em>")
    users_list = ''.join(
        f"""<li><a href="/users/{user['user_id']}/cards">{user['name']}</li>"""
        for user in users_data['users']
    )
    return page(f"""
    <h3>Users</h3>
    <ul>{users_list}</ul>
    <a href="/users?past={users_data['past']}">Next Page</a>
    """)


@app.route("/users/<user_id>/cards")
def html_user_cards(user_id):
    past = request.args.get("past")
    user = get_user(user_id)

    if user is None:
        return page(f"""
        <a href="/users">&lt; Users</a>
        <br />
        <h3><em>User not found</em></h3>
        """)

    cards_data = get_user_cards(user_id, past)
    cards_list = ''.join(f"<li>{user['card_id']}</li>" for user in cards_data['cards']) or "No results"
    next_page_button = f"""<a href="/users/{user_id}/cards?past={cards_data['past']}">Next Page</a>""" if cards_data['past'] else ""
    manager_line = f"""Manager: <a href="/users/{user['manager_id']}/cards">{user['manager_name']}</a>""" if user['manager_id'] else ""
    return page(f"""
    <a href="/users">&lt; Users</a>
    <h1>{user['name']}</h1>
    {manager_line}
    <div>
        <h3>Cards</h3>
        <ul>{cards_list}</ul>
        {next_page_button}
    </div>
    """)
