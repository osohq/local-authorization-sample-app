import os
import random
from collections import deque

from sqlalchemy import create_engine, text

COMPANIES = 10
CEO_REPORTS_TOTAL = 6000
DIRECT_REPORTS = 3
CARDS_PER = 6

with open("words.txt", "r") as f:
    last_names = f.read().splitlines()

first_names = ["Alice", "Bob", "Chris", "Drew", "Eve"]

def random_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def create_company(conn):
    ceo_name = f"{random.choice(first_names)} Boss"
    [ceo_id] = conn.execute(text(f"INSERT INTO users(manager_id, name) VALUES (null, '{ceo_name}') RETURNING user_id")).scalars()

    values = ', '.join([f"('{ceo_id}')"] * CARDS_PER)
    cards_query = text(f"INSERT INTO cards(manager_id) VALUES {values}")
    conn.execute(cards_query)

    frontier = deque([ceo_id])
    for _ in range(CEO_REPORTS_TOTAL // DIRECT_REPORTS):
        manager = frontier.popleft()
        values = ', '.join(f"('{manager}', '{random_name()}')" for _ in range(DIRECT_REPORTS))
        user_query = text(f"INSERT INTO users(manager_id, name) VALUES {values} RETURNING user_id")
        new_user_ids = list(conn.execute(user_query).scalars())
        frontier.extend(new_user_ids)
        values = ', '.join(
            f"('{user_id}')"
            for user_id in new_user_ids
            for _ in range(CARDS_PER)
        )
        cards_query = text(f"INSERT INTO cards(manager_id) VALUES {values}")
        conn.execute(cards_query)


def seed_data():
    uri = os.environ["DATABASE_URL"]
    engine = create_engine(uri)

    with engine.connect() as conn:
        # initialize schema
        with open("init.sql", "r") as init_sql:
            query = text(init_sql.read())
            conn.execute(query)

        # fill data
        for _ in range(COMPANIES):
            create_company(conn)

        conn.commit()


if __name__ == '__main__':
    seed_data()
