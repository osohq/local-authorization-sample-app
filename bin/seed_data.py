import os
import math
import random
import time
from collections import deque
from itertools import islice

from sqlalchemy import create_engine, text

# data constants: modify to change the amt of data generated
COMPANIES = 100
DEPARTMENTS_PER_COMPANY = 10
TEAMS_PER_DEPARTMENT = 5
TEAMS_PER_TEAM = 3
MAX_SUBTEAM_DEPTH = 3
USERS_PER_TEAM = 5
CARDS_PER_USER = 6

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
    """
    Populate demo_app tables according to the updated schema in init.sql.

    Tables & relevant columns now look like:
      companies(company_id, name)
      departments(department_id, name, company_id)
      teams(team_id, name, parent_team_id, company_id)
      users(user_id, name, team_id, department_id, company_id,
            is_company_admin, is_department_head, is_team_manager)

    Strategy per company:
      • create an admin user (is_company_admin=True)
      • create N departments each with a head user (is_department_head=True)
      • for every department create top-level teams and recursive sub-teams.
        Each team gets USERS_PER_TEAM users; one marked is_team_manager=True.
    """
    import uuid

    # -------------------------------- internal helpers
    def _bulk_insert(table: str, cols: list[str], rows: list[tuple]):
        if not rows:
            return
        cols_sql = ", ".join(cols)
        # simple paramless value interpolation since this is demo data only
        values_chunks = chunks(rows, USER_CHUNKS)
        for chunk in values_chunks:
            value_sql = ", ".join(
                "(" + ", ".join("null" if v is None else f"'{str(v).replace("'", "''")}'" for v in r) + ")"  # noqa: E501
                for r in chunk
            )
            conn.execute(text(f"INSERT INTO {table} ({cols_sql}) VALUES {value_sql}"))

    def _create_team_hierarchy(company_id: str, department_id: str, parent_team_id: str | None, depth: int, team_rows: list, user_rows: list):
        """Recursive team/user creation."""
        team_id = uuid.uuid4()
        team_name = f"Team {team_id.hex[:8]}"
        # store team row (no department FK any more)
        team_rows.append((team_id, team_name, parent_team_id, company_id))

        # manager user
        manager_id = uuid.uuid4()
        user_rows.append((
            manager_id,
            random_name(),
            team_id,
            department_id,
            company_id,
            False,  # is_company_admin
            False,  # is_department_head
            True    # is_team_manager
        ))

        # other users
        for _ in range(USERS_PER_TEAM - 1):
            uid = uuid.uuid4()
            user_rows.append((uid, random_name(), team_id, department_id, company_id, False, False, False))

        if depth < MAX_SUBTEAM_DEPTH - 1:
            for _ in range(TEAMS_PER_TEAM):
                _create_team_hierarchy(company_id, department_id, team_id, depth + 1, team_rows, user_rows)

    # -------------------------------- build rows
    company_rows: list[tuple] = []
    department_rows: list[tuple] = []
    team_rows: list[tuple] = []
    user_rows: list[tuple] = []

    for c_idx in range(COMPANIES):
        company_id = uuid.uuid4()
        company_name = f"Company {c_idx + 1}"

        company_rows.append((company_id, company_name))

        # company admin user
        admin_id = uuid.uuid4()
        user_rows.append((admin_id, random_name(), None, None, company_id, True, False, False))

        # departments
        for d_idx in range(DEPARTMENTS_PER_COMPANY):
            dept_id = uuid.uuid4()
            dept_name = f"Dept {d_idx + 1} – {company_name}"
            department_rows.append((dept_id, dept_name, company_id))

            # department head
            hod_id = uuid.uuid4()
            user_rows.append((hod_id, random_name(), None, dept_id, company_id, False, True, False))

            # teams for this department
            for _ in range(TEAMS_PER_DEPARTMENT):
                _create_team_hierarchy(company_id, dept_id, None, 0, team_rows, user_rows)

    # -------------------------------- insert rows
    _bulk_insert("companies", ["company_id", "name"], company_rows)
    _bulk_insert("departments", ["department_id", "name", "company_id"], department_rows)
    _bulk_insert("teams", ["team_id", "name", "parent_team_id", "company_id"], team_rows)
    _bulk_insert(
        "users",
        [
            "user_id",
            "name",
            "team_id",
            "department_id",
            "company_id",
            "is_company_admin",
            "is_department_head",
            "is_team_manager",
        ],
        user_rows,
    )


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
        ) _(user_id), generate_series(1, {CARDS_PER_USER})
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
