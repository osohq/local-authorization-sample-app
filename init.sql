DROP SCHEMA IF EXISTS demo_app CASCADE;
CREATE SCHEMA demo_app;

SELECT pg_catalog.set_config('search_path', 'demo_app', false);

-- Companies table
CREATE TABLE demo_app.companies (
  company_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL
);

-- Departments table
CREATE TABLE demo_app.departments (
  department_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  company_id UUID NOT NULL REFERENCES demo_app.companies(company_id) ON DELETE CASCADE
);

-- Teams table
CREATE TABLE demo_app.teams (
  team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  parent_team_id UUID REFERENCES demo_app.teams(team_id) ON DELETE SET NULL,
  company_id UUID NOT NULL REFERENCES demo_app.companies(company_id) ON DELETE CASCADE
);

-- Users table
CREATE TABLE demo_app.users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  team_id UUID REFERENCES demo_app.teams(team_id) ON DELETE SET NULL,
  department_id UUID REFERENCES demo_app.departments(department_id) ON DELETE SET NULL,
  company_id UUID NOT NULL REFERENCES demo_app.companies(company_id) ON DELETE CASCADE,
  is_company_admin BOOLEAN NOT NULL DEFAULT FALSE,
  is_department_head BOOLEAN NOT NULL DEFAULT FALSE,
  is_team_manager BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE demo_app.cards (
  card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL REFERENCES demo_app.users
);

-- Updated indexes after schema refactor
CREATE INDEX idx_departments_company_id ON demo_app.departments(company_id);
CREATE INDEX idx_teams_parent_team_id ON demo_app.teams(parent_team_id);
CREATE INDEX idx_teams_company_id ON demo_app.teams(company_id);
CREATE INDEX idx_users_team_id ON demo_app.users(team_id);
CREATE INDEX idx_users_department_id ON demo_app.users(department_id);
CREATE INDEX idx_users_is_department_head ON demo_app.users(is_department_head);
CREATE INDEX idx_users_is_team_manager ON demo_app.users(is_team_manager);
CREATE INDEX idx_users_is_company_admin ON demo_app.users(is_company_admin);
CREATE INDEX idx_users_company_id ON demo_app.users(company_id);
CREATE INDEX idx_cards_owner_id ON demo_app.cards(owner_id);
CREATE INDEX idx_cards_card_id_owner_id ON demo_app.cards(card_id, owner_id);