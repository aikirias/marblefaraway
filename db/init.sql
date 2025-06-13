-- Areas table (e.g., Data QA, Model, Architecture, Develop)
CREATE TABLE areas (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

-- People per area with available FTE (0.25, 0.5, 0.75, 1)
CREATE TABLE people (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  area_id INTEGER NOT NULL REFERENCES areas(id),
  availability NUMERIC(3,2) NOT NULL CHECK (availability IN (0.25, 0.5, 0.75, 1))
);

-- Projects with dynamic priority (1..N)
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  priority INTEGER NOT NULL,
  start_date DATE NOT NULL,
  due_date DATE NOT NULL
);

-- Assignments: link projects and people with estimated hours
CREATE TABLE assignments (
  id SERIAL PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  person_id INTEGER NOT NULL REFERENCES people(id),
  hours_estimated INTEGER NOT NULL
);