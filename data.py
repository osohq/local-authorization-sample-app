import os
import time

from oso_cloud import Oso, typed_var, Value
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from model import Card, Company, Department, Team, User

oso = Oso(
    url=os.environ["OSO_URL"],
    api_key=os.environ["OSO_AUTH"],
    data_bindings="oso_local.yaml",
)
uri = os.environ["DATABASE_URL"]
engine = create_engine(uri, echo=True)


def get_user_cards(user_id, past):
    LIMIT = 30
    sql_fragment = oso.list_local(Value("User", user_id), "view", "Card", "cards.card_id")

    query = select(Card.card_id, Card.owner_id)
    query = query.filter(text(sql_fragment))

    with Session(engine) as session:
        count = session.execute(select(func.count()).select_from(query)).scalar()

    if past is not None:
        query = query.filter(Card.card_id > past)

    query = query.order_by(Card.card_id)
    query = query.limit(LIMIT)

    sql = str(query)

    with Session(engine) as session:
        start = time.perf_counter()
        cards = session.execute(query).mappings().all()
        query_time = time.perf_counter() - start

    return {
        "cards": [dict(card) for card in cards],
        "total_cards": count,
        "past": cards[-1].card_id if cards and len(cards) == LIMIT else None,
        "sql": sql,
        "oso_fragment": sql_fragment,
        "query_time": query_time,
    }


def get_users(past):
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_
    user = aliased(User)
    team = aliased(Team)
    manager = aliased(User)
    
    query = select(
        user.user_id, 
        user.team_id, 
        user.name,
        manager.user_id.label("manager_id"),
        manager.name.label("manager_name")
    )
    query = query.outerjoin(team, team.team_id == user.team_id)
    # Manager is another user in the same team with is_team_manager = TRUE
    query = query.outerjoin(
        manager,
        and_(manager.team_id == user.team_id, manager.is_team_manager == True)  # noqa: E712
    )
    
    if past is not None:
        query = query.filter(user.user_id > past)
    query = query.order_by(user.user_id)
    query = query.limit(30)

    with Session(engine) as session:
        users = session.execute(query).mappings().all()

    return {
        "users": [dict(user) for user in users],
        "past": users[-1].user_id if users else None,
    }


def get_user(user_id):
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_
    user = aliased(User)
    team = aliased(Team)
    manager = aliased(User)
    department = aliased(Department)
    company = aliased(Company)
    department_head = aliased(User)
    company_admin = aliased(User)
    
    query = select(
        user.user_id, 
        user.team_id, 
        user.name, 
        team.name.label("team_name"),
        manager.user_id.label("manager_id"),
        manager.name.label("manager_name"),
        department.name.label("department_name"),
        department_head.user_id.label("department_head_id"),
        department_head.name.label("department_head_name"),
        company.name.label("company_name"),
        company_admin.user_id.label("company_admin_id"),
        company_admin.name.label("company_admin_name")
    )
    query = query.outerjoin(team, team.team_id == user.team_id)
    query = query.outerjoin(manager, and_(manager.team_id == user.team_id, manager.is_team_manager == True))  # noqa: E712
    query = query.outerjoin(department, department.department_id == user.department_id)
    query = query.outerjoin(department_head, and_(department_head.department_id == department.department_id, department_head.is_department_head == True))  # noqa: E712
    query = query.outerjoin(company, company.company_id == user.company_id)
    query = query.outerjoin(company_admin, and_(company_admin.company_id == company.company_id, company_admin.is_company_admin == True))  # noqa: E712
    query = query.filter(user.user_id == user_id)

    with Session(engine) as session:
        user = session.execute(query).mappings().one_or_none()

    return user


def get_transitive_reports(user_id):
    user = typed_var("User")
    return oso.build_query(("managed_by", user, Value("User", user_id))).evaluate(user)


def get_direct_reports(user_id):
    user = typed_var("User")
    return oso.build_query(("direct_manager", user, Value("User", user_id))).evaluate(user)
