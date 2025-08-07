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
    Seed the database with companies, departments, teams, and users that fit
    the schema defined in `init.sql` and the constants declared at the top of
    this file.

    The function performs the following for each company:
      1. Create an *admin* user (referenced by the company as `admin_id`).
      2. Create `DEPARTMENTS_PER_COMPANY` departments, each with its own *head* user.
      3. For every department, create `TEAMS_PER_DEPARTMENT` top-level teams and
         recursively add sub-teams up to `MAX_SUBTEAM_DEPTH` levels deep, with
         `TEAMS_PER_TEAM` children per team.
      4. For every team, create `USERS_PER_TEAM` users (one of whom is the
         manager, referenced by the team as `managed_by`).
    """
    import uuid

    # ------------------------------------------------------------------ helpers
    def _q(val):
        """Quote a value for interpolation into an SQL string."""
        if val is None:
            return "null"
        return f"'{str(val).replace("'", "''")}'"

    def _bulk_insert(table: str, columns: list[str], rows: list[tuple], *, chunk_size: int = USER_CHUNKS):
        """Fast (and very simple) bulk INSERT for demo data."""
        if not rows:
            return
        cols_sql = ", ".join(columns)
        for chunk in chunks(rows, chunk_size):
            values_sql = ", ".join(
                "(" + ", ".join(_q(v) for v in row) + ")" for row in chunk
            )
            conn.execute(text(f"INSERT INTO {table} ({cols_sql}) VALUES {values_sql}"))

    def _create_team_hierarchy(company_id, department_id, parent_team_id, depth, team_rows, user_rows):
        """Recursively create a team (and its sub-teams) plus users."""
        team_id = uuid.uuid4()
        manager_id = uuid.uuid4()
        team_name = f"Team {team_id.hex[:8]}"

        # Team row
        team_rows.append((team_id, team_name, department_id, parent_team_id, manager_id, company_id))

        # Manager user
        user_rows.append((manager_id, random_name(), team_id, company_id))

        # Additional users for the team
        for _ in range(USERS_PER_TEAM - 1):
            user_id = uuid.uuid4()
            user_rows.append((user_id, random_name(), team_id, company_id))

        # Recurse into sub-teams
        if depth < MAX_SUBTEAM_DEPTH - 1:
            for _ in range(TEAMS_PER_TEAM):
                _create_team_hierarchy(company_id, department_id, team_id, depth + 1, team_rows, user_rows)

    # ---------------------------------------------------------------- walk & collect rows
    print("Disabling foreign-key constraints for bulk insert …")
    conn.execute(text("SET session_replication_role = 'replica'"))

    try:
        company_rows: list[tuple] = []
        department_rows: list[tuple] = []
        team_rows: list[tuple] = []
        user_rows: list[tuple] = []

        for c_idx in range(COMPANIES):
            company_id = uuid.uuid4()
            admin_id = uuid.uuid4()
            company_name = f"Company {c_idx + 1}"

            # Company and its admin
            company_rows.append((company_id, admin_id, company_name))
            user_rows.append((admin_id, random_name(), None, company_id))

            # Departments for this company
            for d_idx in range(DEPARTMENTS_PER_COMPANY):
                department_id = uuid.uuid4()
                hod_id = uuid.uuid4()
                department_name = f"Department {d_idx + 1} – {company_name}"

                department_rows.append((department_id, department_name, company_id, hod_id))
                user_rows.append((hod_id, random_name(), None, company_id))

                # Top-level teams
                for _ in range(TEAMS_PER_DEPARTMENT):
                    _create_team_hierarchy(company_id, department_id, None, 0, team_rows, user_rows)

        # ---------------------------------------------------------------- insert rows
        _bulk_insert("companies", ["company_id", "admin_id", "name"], company_rows)
        _bulk_insert("users", ["user_id", "name", "team_id", "company_id"], user_rows)
        _bulk_insert("departments", ["department_id", "name", "company_id", "head_of_department_id"], department_rows)
        _bulk_insert("teams", ["team_id", "name", "department_id", "parent_team_id", "managed_by", "company_id"], team_rows)
    finally:
        print("Re-enabling foreign-key constraints …")
        conn.execute(text("SET session_replication_role = 'origin'"))


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
