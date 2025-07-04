-- Migración para agregar campo priority_order a plan_assignments
-- Permite guardar las prioridades específicas de cada plan

ALTER TABLE plan_assignments 
ADD COLUMN priority_order INTEGER;

-- Crear índice para optimizar consultas por prioridad
CREATE INDEX idx_plan_assignments_priority_order ON plan_assignments(priority_order);

-- Comentario para documentación
COMMENT ON COLUMN plan_assignments.priority_order IS 'Orden de prioridad específico del proyecto en este plan';