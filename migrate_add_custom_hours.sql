-- Agregar campo para horas estimadas personalizadas por assignment
ALTER TABLE project_team_assignments 
ADD COLUMN custom_estimated_hours INTEGER DEFAULT NULL;

-- Comentario: 
-- - Si custom_estimated_hours es NULL, se usa el tier para calcular las horas
-- - Si custom_estimated_hours tiene valor, se usa ese valor en lugar del tier