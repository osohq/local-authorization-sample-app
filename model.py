import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class Base(sqlalchemy.orm.DeclarativeBase):
    """SQLAlchemy declarative base."""

class Company(Base):
    __tablename__ = "companies"
    __table_args__ = {"schema": "demo_app"}

    company_id: Mapped[str] = mapped_column(primary_key=True)
    admin_id: Mapped[str] = mapped_column(ForeignKey("demo_app.users.user_id"), nullable=False)
    name: Mapped[str]

class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": "demo_app"}

    department_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    company_id: Mapped[str] = mapped_column(ForeignKey("demo_app.companies.company_id"), nullable=False)
    head_of_department_id: Mapped[str | None] = mapped_column(ForeignKey("demo_app.users.user_id"))

class Team(Base):
    __tablename__ = "teams"
    __table_args__ = {"schema": "demo_app"}

    team_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    department_id: Mapped[str] = mapped_column(ForeignKey("demo_app.departments.department_id"), nullable=False)
    parent_team_id: Mapped[str | None] = mapped_column(ForeignKey("demo_app.teams.team_id"))
    managed_by: Mapped[str | None] = mapped_column(ForeignKey("demo_app.users.user_id"))
    company_id: Mapped[str] = mapped_column(ForeignKey("demo_app.companies.company_id"), nullable=False)

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "demo_app"}

    user_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    team_id: Mapped[str | None] = mapped_column(ForeignKey("demo_app.teams.team_id"))
    company_id: Mapped[str] = mapped_column(ForeignKey("demo_app.companies.company_id"), nullable=False)

class Card(Base):
    __tablename__ = "cards"
    __table_args__ = {"schema": "demo_app"}

    card_id: Mapped[str] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("demo_app.users.user_id"), nullable=False)
