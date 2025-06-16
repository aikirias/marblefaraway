CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  priority INTEGER NOT NULL,
  phase TEXT NOT NULL,
  start_date DATE NOT NULL,
  due_date_wo_qa DATE NOT NULL,
  due_date_with_qa DATE NOT NULL
);

-- Teams table: available capacity per area
CREATE TABLE teams (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  total_devs INTEGER NOT NULL DEFAULT 0,
  busy_devs INTEGER NOT NULL DEFAULT 0
);

-- Assignments: links projects and teams with allocation details
CREATE TABLE project_team_assignments (
  id SERIAL PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  devs_assigned NUMERIC(4,2) NOT NULL,
  max_devs NUMERIC(4,2) NOT NULL,
  estimated_hours INTEGER NOT NULL,
  start_date DATE,
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