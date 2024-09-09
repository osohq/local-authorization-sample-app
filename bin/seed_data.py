from sqlalchemy import create_engine, text
from collections import deque

COMPANIES = 10
CEO_REPORTS_TOTAL = 1000
DIRECT_REPORTS = 3
CARDS_PER = 6

def create_company(conn):
    [ceo_id] = conn.execute(text("INSERT INTO users(manager_id) VALUES (null) RETURNING user_id")).scalars()

    cards_query = text("INSERT INTO cards(manager_id) VALUES {}".format(', '.join([f"('{ceo_id}')"] * CARDS_PER)))
    conn.execute(cards_query)

    frontier = deque([ceo_id])
    for _ in range(CEO_REPORTS_TOTAL // DIRECT_REPORTS):
        manager = frontier.popleft()
        user_query = text("INSERT INTO users(manager_id) VALUES {} RETURNING user_id".format(', '.join([f"('{manager}')"] * DIRECT_REPORTS)))
        new_user_ids = conn.execute(user_query).scalars()
        frontier.extend(new_user_ids)


def seed_data():
    engine = create_engine("postgresql://localhost", echo=True)

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
