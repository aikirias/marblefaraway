CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  priority INTEGER NOT NULL,
  phase TEXT NOT NULL,
  start_date DATE NOT NULL,
  due_date_wo_qa DATE NOT NULL,
  due_date_with_qa DATE NOT NULL,
  active BOOLEAN NOT NULL DEFAULT true,
  horas_trabajadas INTEGER NOT NULL DEFAULT 0,
  horas_totales_estimadas INTEGER NOT NULL DEFAULT 0,
  fecha_inicio_real DATE
);

-- Teams table: available capacity per area
CREATE TABLE teams (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  total_devs INTEGER NOT NULL DEFAULT 0,
  busy_devs INTEGER NOT NULL DEFAULT 0
);

-- Assignments: links projects and teams with allocation details
-- Assignments: links projects and teams with allocation details
CREATE TABLE project_team_assignments (
  id SERIAL PRIMARY KEY,
  project_id INTEGER NOT NULL 
    REFERENCES projects(id) ON DELETE CASCADE,
  team_id INTEGER NOT NULL 
    REFERENCES teams(id) ON DELETE CASCADE,
  tier INTEGER NOT NULL,
  devs_assigned NUMERIC(4,2) NOT NULL,
  max_devs NUMERIC(4,2) NOT NULL,
  estimated_hours INTEGER NOT NULL,
  start_date DATE,
  ready_to_start_date DATE,
  paused_on DATE,
  pending_hours INTEGER,
  status TEXT NOT NULL
);


-- Tier-based capacity: defines hours per tier per team
CREATE TABLE tier_capacity (
  id SERIAL PRIMARY KEY,
  team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  tier INTEGER NOT NULL,
  hours_per_person INTEGER NOT NULL
);

INSERT INTO teams (name, total_devs, busy_devs) VALUES
  ('Devs', 6, 0),
  ('Arch', 2, 0),
  ('Model', 4, 0),
  ('Dqa', 4, 0);

-- Default seed data for tier_capacity
INSERT INTO tier_capacity (team_id, tier, hours_per_person)
  SELECT id, 1, 16 FROM teams WHERE name = 'Arch' UNION ALL
  SELECT id, 2, 32 FROM teams WHERE name = 'Arch' UNION ALL
  SELECT id, 3, 72 FROM teams WHERE name = 'Arch' UNION ALL
  SELECT id, 4, 240 FROM teams WHERE name = 'Arch' UNION ALL
  SELECT id, 1, 16 FROM teams WHERE name = 'Devs' UNION ALL
  SELECT id, 2, 40 FROM teams WHERE name = 'Devs' UNION ALL
  SELECT id, 3, 80 FROM teams WHERE name = 'Devs' UNION ALL
  SELECT id, 4, 120 FROM teams WHERE name = 'Devs' UNION ALL
  SELECT id, 1, 40 FROM teams WHERE name = 'Model' UNION ALL
  SELECT id, 2, 80 FROM teams WHERE name = 'Model' UNION ALL
  SELECT id, 3, 120 FROM teams WHERE name = 'Model' UNION ALL
  SELECT id, 4, 160 FROM teams WHERE name = 'Model' UNION ALL
  SELECT id, 1, 8 FROM teams WHERE name = 'Dqa' UNION ALL
  SELECT id, 2, 24 FROM teams WHERE name = 'Dqa' UNION ALL
  SELECT id, 3, 40 FROM teams WHERE name = 'Dqa';