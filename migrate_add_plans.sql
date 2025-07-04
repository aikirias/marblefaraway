-- Migración para agregar sistema de planes persistentes
-- Permite guardar y comparar resultados de simulaciones

-- Tabla principal de planes
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    checksum VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash del contenido del plan
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT false,
    simulation_date DATE NOT NULL, -- Fecha base de la simulación
    total_assignments INTEGER NOT NULL DEFAULT 0,
    total_projects INTEGER NOT NULL DEFAULT 0
);

-- Tabla de asignaciones del plan (snapshot de assignments calculados)
CREATE TABLE plan_assignments (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    assignment_id INTEGER NOT NULL, -- ID original del assignment
    project_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    project_priority INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    tier INTEGER NOT NULL,
    devs_assigned NUMERIC(4,2) NOT NULL,
    estimated_hours INTEGER NOT NULL,
    calculated_start_date DATE NOT NULL,
    calculated_end_date DATE NOT NULL,
    pending_hours INTEGER NOT NULL DEFAULT 0,
    ready_to_start_date DATE NOT NULL
);

-- Índices para optimizar consultas
CREATE INDEX idx_plans_checksum ON plans(checksum);
CREATE INDEX idx_plans_active ON plans(is_active);
CREATE INDEX idx_plans_created_at ON plans(created_at DESC);
CREATE INDEX idx_plan_assignments_plan_id ON plan_assignments(plan_id);
CREATE INDEX idx_plan_assignments_project_id ON plan_assignments(project_id);
CREATE INDEX idx_plan_assignments_team_id ON plan_assignments(team_id);
CREATE INDEX idx_plan_assignments_dates ON plan_assignments(calculated_start_date, calculated_end_date);

-- Constraint para asegurar que solo hay un plan activo a la vez
CREATE UNIQUE INDEX idx_plans_single_active ON plans(is_active) WHERE is_active = true;

-- Vista para resumen de planes con estadísticas
CREATE VIEW plan_summary AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.checksum,
    p.created_at,
    p.is_active,
    p.simulation_date,
    p.total_assignments,
    p.total_projects,
    COUNT(pa.id) as assignment_count,
    MIN(pa.calculated_start_date) as earliest_start,
    MAX(pa.calculated_end_date) as latest_end,
    COUNT(DISTINCT pa.project_id) as unique_projects,
    COUNT(DISTINCT pa.team_id) as unique_teams,
    SUM(pa.pending_hours) as total_hours
FROM plans p
LEFT JOIN plan_assignments pa ON p.id = pa.plan_id
GROUP BY p.id, p.name, p.description, p.checksum, p.created_at, 
         p.is_active, p.simulation_date, p.total_assignments, p.total_projects
ORDER BY p.created_at DESC;

-- Comentarios para documentación
COMMENT ON TABLE plans IS 'Almacena snapshots de resultados de simulación como planes persistentes';
COMMENT ON TABLE plan_assignments IS 'Asignaciones calculadas para cada plan, con fechas de inicio y fin';
COMMENT ON COLUMN plans.checksum IS 'Hash SHA-256 del contenido del plan para detectar cambios';
COMMENT ON COLUMN plans.is_active IS 'Indica si este es el plan actualmente activo (solo uno puede estar activo)';
COMMENT ON VIEW plan_summary IS 'Vista con estadísticas resumidas de cada plan';