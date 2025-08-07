DROP SCHEMA IF EXISTS demo_app CASCADE;
CREATE SCHEMA demo_app;

SELECT pg_catalog.set_config('search_path', 'demo_app', false);

-- Companies table
CREATE TABLE demo_app.companies (
  company_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID NOT NULL REFERENCES demo_app.users(user_id) ON DELETE CASCADE,
  name TEXT NOT NULL
);

-- Departments table
CREATE TABLE demo_app.departments (
  department_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  company_id UUID NOT NULL REFERENCES demo_app.companies(company_id) ON DELETE CASCADE,
  head_of_department_id UUID REFERENCES demo_app.users(user_id) ON DELETE SET NULL
);

-- Teams table
CREATE TABLE demo_app.teams (
  team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  department_id UUID NOT NULL REFERENCES demo_app.departments(department_id) ON DELETE CASCADE,
  parent_team_id UUID REFERENCES demo_app.teams(team_id) ON DELETE SET NULL,
  managed_by UUID REFERENCES demo_app.users(user_id) ON DELETE SET NULL,
  company_id UUID NOT NULL REFERENCES demo_app.companies(company_id) ON DELETE CASCADE
);

-- Users table
CREATE TABLE demo_app.users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  team_id UUID REFERENCES demo_app.teams(team_id) ON DELETE SET NULL,
  company_id UUID NOT NULL REFERENCES demo_app.companies(company_id) ON DELETE CASCADE
);

CREATE TABLE demo_app.cards (
  card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL REFERENCES demo_app.users
);

CREATE INDEX idx_departments_company_id ON demo_app.departments(company_id);

CREATE INDEX idx_teams_department_id ON demo_app.teams(department_id);
CREATE INDEX idx_teams_parent_team_id ON demo_app.teams(parent_team_id);
CREATE INDEX idx_teams_managed_by ON demo_app.teams(managed_by);
CREATE INDEX idx_teams_company_id ON demo_app.teams(company_id);

CREATE INDEX idx_users_team_id ON demo_app.users(team_id);
CREATE INDEX idx_users_company_id ON demo_app.users(company_id);

CREATE INDEX idx_cards_owner_id ON demo_app.cards(owner_id);