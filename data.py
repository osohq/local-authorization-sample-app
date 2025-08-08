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
    start = time.perf_counter()
    sql_fragment = oso.list_local(Value("User", user_id), "view", "Card", "cards.card_id")
    oso_query_time = time.perf_counter() - start

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
        db_query_time = time.perf_counter() - start

    return {
        "cards": [dict(card) for card in cards],
        "total_cards": count,
        "past": cards[-1].card_id if cards and len(cards) == LIMIT else None,
        "sql": sql,
        "oso_fragment": sql_fragment,
        "oso_query_time": oso_query_time,
        "db_query_time": db_query_time,
    }


def get_users(past):
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_, func
    user = aliased(User)
    team = aliased(Team)
    parent_team = aliased(Team)
    mgr_same = aliased(User)
    mgr_parent = aliased(User)

    query = select(
        user.user_id,
        user.team_id,
        user.name,
        func.coalesce(mgr_same.user_id, mgr_parent.user_id).label("manager_id"),
        func.coalesce(mgr_same.name, mgr_parent.name).label("manager_name"),
    )

    query = query.outerjoin(team, team.team_id == user.team_id)
    # manager in same team
    query = query.outerjoin(
        mgr_same,
        and_(mgr_same.team_id == user.team_id, mgr_same.is_team_manager == True)  # noqa: E712
    )
    # parent team & its manager
    query = query.outerjoin(parent_team, parent_team.team_id == team.parent_team_id)
    query = query.outerjoin(
        mgr_parent,
        and_(mgr_parent.team_id == parent_team.team_id, mgr_parent.is_team_manager == True)  # noqa: E712
    )

    if past is not None:
        query = query.filter(user.user_id > past)
    query = query.order_by(user.user_id).limit(30)

    with Session(engine) as session:
        users = session.execute(query).mappings().all()

    return {
        "users": [dict(user) for user in users],
        "past": users[-1].user_id if users else None,
    }


def get_user(user_id):
    from sqlalchemy.orm import aliased
    from sqlalchemy import and_, func, select

    u  = aliased(User)        # the user we're looking up
    t  = aliased(Team)        # their team
    pt = aliased(Team)        # parent team
    m1 = aliased(User)        # manager in same team
    m2 = aliased(User)        # manager in parent team
    dh = aliased(User)        # department head
    ca = aliased(User)        # company admin

    query = (
        select(
            u.user_id,
            u.name,
            u.team_id,
            func.coalesce(m1.user_id, m2.user_id).label("manager_id"),
            func.coalesce(m1.name,    m2.name   ).label("manager_name"),
            dh.user_id.label("department_head_id"),
            dh.name.label("department_head_name"),
            ca.user_id.label("company_admin_id"),
            ca.name.label("company_admin_name"),
        )
        .outerjoin(t,  t.team_id == u.team_id)
        .outerjoin(m1, and_(
            m1.team_id == u.team_id,
            m1.is_team_manager == True,
            u.is_team_manager == False
        ))
        .outerjoin(pt, pt.team_id == t.parent_team_id)
        .outerjoin(m2, and_(
            m2.team_id == pt.team_id,
            m2.is_team_manager == True,
            u.is_team_manager == True
        ))
        .outerjoin(dh, and_(dh.department_id == u.department_id, dh.is_department_head, u.is_department_head == False))
        .outerjoin(ca, and_(ca.company_id == u.company_id, ca.is_company_admin, u.is_company_admin == False))
        .where(u.user_id == user_id)
    )

    with Session(engine) as session:
        result = session.execute(query).mappings().one_or_none()

    return result


def get_transitive_reports(user_id):
    user = typed_var("User")
    return oso.build_query(("managed_by", user, Value("User", user_id))).evaluate(user)


def get_direct_reports(user_id):
    user = typed_var("User")
    return oso.build_query(("direct_manager", user, Value("User", user_id))).evaluate(user)
