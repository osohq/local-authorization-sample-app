DROP SCHEMA IF EXISTS demo_app CASCADE;
CREATE SCHEMA demo_app;

SELECT pg_catalog.set_config('search_path', 'demo_app', false);

CREATE TABLE demo_app.users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- name TEXT NOT NULL,
  manager_id UUID REFERENCES demo_app.users
);

CREATE TABLE demo_app.cards (
  card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  manager_id UUID NOT NULL REFERENCES demo_app.users
);
