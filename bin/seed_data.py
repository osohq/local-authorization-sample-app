import os
import math
import random
import time
from collections import deque
from itertools import islice

from sqlalchemy import create_engine, text

# data constants: modify to change the amt of data generated
COMPANIES = 1000
CEO_REPORTS_TOTAL = 6000
DIRECT_REPORTS = 3
CARDS_PER = 6

# performance constants: probably don't modify these.
USER_CHUNKS = 1000
CARD_CHUNKS = 10000

with open("words.txt", "r") as f:
    last_names = f.read().splitlines()

first_names = ["Alice", "Bob", "Chris", "Drew", "Eve"]

def random_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def chunks(it, size):
    it = iter(it)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            return
        yield chunk


def create_companies(conn):
    ceo_names = ', '.join(f"(null, '{random.choice(first_names)} Boss')" for _ in range(COMPANIES))
    frontier = list(conn.execute(text(f"INSERT INTO users(manager_id, name) VALUES {ceo_names} RETURNING user_id")).scalars())

    iterations = math.ceil(math.log(CEO_REPORTS_TOTAL, DIRECT_REPORTS))
    for i in range(iterations):
        print(f"  Depth {i+1}/{iterations}..")
        new_frontier = []
        total_chunks = math.ceil(len(frontier) / USER_CHUNKS)
        start = time.perf_counter()
        for i, chunk in enumerate(chunks(frontier, USER_CHUNKS), 1):
            print(end=f"  ..adding chunk {i} / {total_chunks}\r")
            values = ', '.join(
                f"('{manager}', '{random_name()}')"
                for manager in chunk
                for _ in range(DIRECT_REPORTS)
            )
            user_query = text(f"INSERT INTO users(manager_id, name) VALUES {values} RETURNING user_id")
            new_user_ids = conn.execute(user_query).scalars()
            new_frontier.extend(new_user_ids)
        frontier = new_frontier
        elapsed = time.perf_counter() - start
        print(f"\n  ..done in {elapsed:.6f}s")


def create_cards(conn):
    start = time.perf_counter()

    offset = 0
    while True:
        cards_query = text(f"""
        INSERT INTO cards(owner_id)
        SELECT user_id FROM (
            SELECT user_id FROM users
            ORDER BY user_id
            LIMIT {CARD_CHUNKS}
            OFFSET {offset}
        ) _(user_id), generate_series(1, {CARDS_PER})
        RETURNING owner_id
        """)
        row = conn.execute(cards_query).first()
        if row is None:
            break
        [uuid] = row
        print(end=f"  for user {uuid}\r")
        offset += CARD_CHUNKS

    elapsed = time.perf_counter() - start
    print(f"\ndone in {elapsed:.6f}s")

def seed_data():
    uri = os.environ["DATABASE_URL"]
    engine = create_engine(uri)

    with engine.connect() as conn:
        start = time.perf_counter()
        # initialize schema
        print("Initializing schema")
        with open("init.sql", "r") as init_sql:
            query = text(init_sql.read())
            conn.execute(query)

        # add users
        print(f"Creating {COMPANIES} companies")
        create_companies(conn)

        # give everyone their cards
        print("\nAdding cards")
        create_cards(conn)

        conn.commit()

        elapsed = time.perf_counter() - start
        print(f"data gen complete in {elapsed:.6f}s!")


if __name__ == '__main__':
    seed_data()
