import os
import random
from collections import deque

from sqlalchemy import create_engine, text

COMPANIES = 1000
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

    frontier = [ceo_id]
    count = 0
    while count < CEO_REPORTS_TOTAL:
        count += len(frontier) * DIRECT_REPORTS
        values = ', '.join(
            f"('{manager}', '{random_name()}')"
            for manager in frontier
            for _ in range(DIRECT_REPORTS)
        )
        user_query = text(f"INSERT INTO users(manager_id, name) VALUES {values} RETURNING user_id")
        new_user_ids = conn.execute(user_query).scalars()
        frontier.extend(new_user_ids)


def seed_data():
    uri = os.environ["DATABASE_URL"]
    engine = create_engine(uri)

    with engine.connect() as conn:
        # initialize schema
        with open("init.sql", "r") as init_sql:
            query = text(init_sql.read())
            conn.execute(query)

        # fill data
        for i in range(COMPANIES):
            print(end=f" Creating company {i+1} / {COMPANIES}\r")
            create_company(conn)

        print("\nAdding cards")

        # give everyone their cards
        cards_query = text(f"""
        INSERT INTO cards(owner_id)
        SELECT user_id FROM users, generate_series(1, {CARDS_PER});
        """)
        conn.execute(cards_query)

        conn.commit()


if __name__ == '__main__':
    seed_data()
