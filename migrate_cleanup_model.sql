-- Migración para limpiar modelo de datos APE
-- Elimina campos redundantes y obsoletos identificados en el análisis

BEGIN;

-- 1. Crear tabla de respaldo para verificar datos antes de eliminar
CREATE TEMP TABLE project_backup AS
SELECT 
    id,
    name,
    horas_trabajadas,
    horas_totales_estimadas,
    phase,
    (SELECT COALESCE(SUM(estimated_hours), 0) 
     FROM project_team_assignments 
     WHERE project_id = projects.id) as calculated_total_hours
FROM projects;

-- 2. Mostrar comparación de datos para verificación
SELECT 
    'VERIFICACION DE DATOS ANTES DE MIGRACIÓN' as info,
    COUNT(*) as total_projects,
    SUM(horas_trabajadas) as total_horas_trabajadas,
    SUM(horas_totales_estimadas) as total_horas_estimadas,
    SUM(calculated_total_hours) as total_calculado_assignments
FROM project_backup;

-- 3. Eliminar columnas redundantes de la tabla projects
ALTER TABLE projects DROP COLUMN IF EXISTS horas_trabajadas;
ALTER TABLE projects DROP COLUMN IF EXISTS horas_totales_estimadas;
ALTER TABLE projects DROP COLUMN IF EXISTS phase;

-- 4. Eliminar columna poco usada de project_team_assignments
ALTER TABLE project_team_assignments DROP COLUMN IF EXISTS paused_on;

-- 5. Verificar estructura final
SELECT 
    'ESTRUCTURA FINAL DE PROJECTS' as info,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'projects' 
ORDER BY ordinal_position;

SELECT 
    'ESTRUCTURA FINAL DE PROJECT_TEAM_ASSIGNMENTS' as info,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'project_team_assignments' 
ORDER BY ordinal_position;

-- 6. Mostrar resumen de cambios
SELECT 
    'RESUMEN DE LIMPIEZA COMPLETADA' as info,
    'Eliminados de projects: horas_trabajadas, horas_totales_estimadas, phase' as campos_eliminados_projects,
    'Eliminados de assignments: paused_on' as campos_eliminados_assignments;

COMMIT;

-- Nota: Los datos de respaldo están en project_backup (tabla temporal)
-- Si necesitas revertir, ejecuta ROLLBACK antes del COMMIT