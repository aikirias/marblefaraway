# APE - Modelo de Datos Detallado

## Esquema de Base de Datos

### Diagrama de Relaciones (ERD)

```mermaid
erDiagram
    projects ||--o{ project_team_assignments : "1:N"
    teams ||--o{ project_team_assignments : "1:N"
    teams ||--o{ tier_capacity : "1:N"
    
    projects {
        int id PK "Identificador único del proyecto"
        text name "Nombre del proyecto"
        int priority "Orden de ejecución (1=más prioritario)"
        text phase "Campo legacy, no usado actualmente"
        date start_date "Fecha de inicio del proyecto"
        date due_date_wo_qa "Fecha límite sin QA"
        date due_date_with_qa "Fecha límite con QA"
    }
    
    teams {
        int id PK "Identificador único del equipo"
        text name UNIQUE "Nombre del equipo (Arch, Devs, Model, Dqa)"
        int total_devs "Capacidad máxima del equipo"
        int busy_devs "Desarrolladores ocupados actualmente"
    }
    
    project_team_assignments {
        int id PK "Identificador único de la asignación"
        int project_id FK "Referencia al proyecto"
        int team_id FK "Referencia al equipo"
        int tier "Nivel de complejidad (1-4)"
        numeric devs_assigned "Desarrolladores asignados (permite decimales)"
        numeric max_devs "Máximo de desarrolladores permitidos"
        int estimated_hours "Horas estimadas (override manual)"
        date start_date "Fecha de inicio de la asignación"
        date ready_to_start_date "Fecha cuando puede comenzar"
        date paused_on "Fecha de pausa (si aplica)"
        int pending_hours "Horas pendientes"
        text status "Estado actual de la asignación"
    }
    
    tier_capacity {
        int id PK "Identificador único"
        int team_id FK "Referencia al equipo"
        int tier "Nivel de complejidad (1-4)"
        int hours_per_person "Horas base por persona para este tier"
    }
```

## Descripción Detallada de Tablas

### 1. Tabla `projects`

**Propósito**: Almacena la información básica de cada proyecto interno de desarrollo.

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | SERIAL PRIMARY KEY | Identificador único autogenerado | 1, 2, 3... |
| `name` | TEXT NOT NULL | Nombre descriptivo del proyecto | "Sistema de Facturación v2.0" |
| `priority` | INTEGER NOT NULL | Orden de ejecución (menor número = mayor prioridad) | 1, 2, 3... |
| `phase` | TEXT NOT NULL | Campo legacy, actualmente no utilizado | "" |
| `start_date` | DATE NOT NULL | Fecha planificada de inicio del proyecto | 2024-01-15 |
| `due_date_wo_qa` | DATE NOT NULL | Fecha límite sin considerar QA | 2024-03-15 |
| `due_date_with_qa` | DATE NOT NULL | Fecha límite incluyendo QA | 2024-03-30 |

**Notas Importantes**:
- La `priority` determina el orden en la simulación de forecasting
- Las fechas `due_date_*` son informativas; el sistema calcula fechas reales basándose en capacidad

### 2. Tabla `teams`

**Propósito**: Define los equipos especializados y su capacidad actual.

| Campo | Tipo | Descripción | Valores Actuales |
|-------|------|-------------|------------------|
| `id` | SERIAL PRIMARY KEY | Identificador único | 1, 2, 3, 4 |
| `name` | TEXT UNIQUE | Nombre del equipo especializado | "Arch", "Devs", "Model", "Dqa" |
| `total_devs` | INTEGER DEFAULT 0 | Capacidad máxima del equipo | 2, 6, 4, 4 |
| `busy_devs` | INTEGER DEFAULT 0 | Desarrolladores ocupados actualmente | 0, 0, 0, 0 |

**Equipos Configurados**:
- **Arch** (Architecture): 2 desarrolladores - Diseño y arquitectura
- **Devs** (Development): 6 desarrolladores - Implementación
- **Model** (Modeling): 4 desarrolladores - Modelado de datos
- **Dqa** (Data Quality Assurance): 4 desarrolladores - Testing

### 3. Tabla `project_team_assignments`

**Propósito**: Tabla central que vincula proyectos con equipos y define los parámetros de estimación.

| Campo | Tipo | Descripción | Rango/Formato |
|-------|------|-------------|---------------|
| `id` | SERIAL PRIMARY KEY | Identificador único | Autogenerado |
| `project_id` | INTEGER FK | Referencia a `projects.id` | CASCADE DELETE |
| `team_id` | INTEGER FK | Referencia a `teams.id` | CASCADE DELETE |
| `tier` | INTEGER NOT NULL | Nivel de complejidad | 1, 2, 3, 4 |
| `devs_assigned` | NUMERIC(4,2) | Desarrolladores asignados | 0.25, 0.5, 1.0, 1.5... |
| `max_devs` | NUMERIC(4,2) | Límite máximo de desarrolladores | >= devs_assigned |
| `estimated_hours` | INTEGER | Override manual de horas | 0 = usar tier_capacity |
| `start_date` | DATE | Fecha de inicio de esta fase | Nullable |
| `ready_to_start_date` | DATE | Cuándo puede comenzar esta fase | Nullable |
| `paused_on` | DATE | Fecha de pausa (si aplica) | Nullable |
| `pending_hours` | INTEGER | Horas restantes por completar | Para tracking de progreso |
| `status` | TEXT | Estado actual | "Not Started", "In Progress", "Completed" |

**Lógica de Estimación**:
```sql
-- Si hay override manual
IF estimated_hours > 0 THEN
    horas_necesarias = estimated_hours
ELSE
    -- Usar matriz de tier_capacity
    horas_necesarias = tier_capacity.hours_per_person * devs_assigned
END IF
```

### 4. Tabla `tier_capacity`

**Propósito**: Matriz de configuración que define las horas base por equipo y nivel de complejidad.

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | SERIAL PRIMARY KEY | Identificador único | Autogenerado |
| `team_id` | INTEGER FK | Referencia a `teams.id` | 1, 2, 3, 4 |
| `tier` | INTEGER NOT NULL | Nivel de complejidad | 1, 2, 3, 4 |
| `hours_per_person` | INTEGER NOT NULL | Horas base por desarrollador | 16, 32, 72, 240 |

## Matriz de Configuración Actual

### Horas por Tier y Equipo

| team_id | Equipo | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---------|--------|--------|--------|--------|--------|
| 1 | Arch | 16h | 32h | 72h | 240h |
| 2 | Devs | 16h | 40h | 80h | 120h |
| 3 | Model | 40h | 80h | 120h | 160h |
| 4 | Dqa | 8h | 24h | 40h | - |

**Observaciones**:
- **Arch** tiene el mayor rango (16h → 240h) reflejando la variabilidad en complejidad arquitectural
- **Dqa** no tiene Tier 4, sugiriendo que el testing no escala tanto con la complejidad
- **Model** tiene horas base más altas, indicando que el modelado es inherentemente más complejo

## Queries Importantes para Forecasting

### 1. Cargar Proyectos por Prioridad
```sql
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.priority
FROM projects p
ORDER BY p.priority;
```

### 2. Obtener Asignaciones con Capacidad de Tier
```sql
SELECT 
    pta.project_id,
    p.name as project_name,
    pta.team_id,
    t.name as phase,
    pta.tier,
    pta.devs_assigned,
    pta.estimated_hours,
    tc.hours_per_person
FROM project_team_assignments pta
JOIN projects p ON pta.project_id = p.id
JOIN teams t ON pta.team_id = t.id
JOIN tier_capacity tc ON (pta.team_id = tc.team_id AND pta.tier = tc.tier)
ORDER BY p.priority, 
         CASE t.name 
             WHEN 'Arch' THEN 1
             WHEN 'Model' THEN 2  
             WHEN 'Devs' THEN 3
             WHEN 'Dqa' THEN 4
         END;
```

### 3. Verificar Capacidad Disponible por Equipo
```sql
SELECT 
    t.id,
    t.name,
    t.total_devs,
    t.busy_devs,
    (t.total_devs - t.busy_devs) as available_devs
FROM teams t;
```

## Algoritmo de Simulación (Pseudocódigo)

```python
def simulate_project_schedule():
    # 1. Cargar datos base
    projects = load_projects_by_priority()
    teams_capacity = load_teams_capacity()
    assignments = load_assignments_with_tier_capacity()
    
    # 2. Estructuras de simulación
    active_assignments_by_team = {team_id: [] for team_id in teams}
    project_completion_dates = {}
    
    # 3. Procesar cada proyecto por prioridad
    for project in projects:
        project_phases = get_phases_for_project(project.id)  # Arch, Model, Devs, Dqa
        project_start = today
        
        # 4. Procesar fases secuencialmente
        for phase in ["Arch", "Model", "Devs", "Dqa"]:
            assignment = project_phases[phase]
            
            # Calcular horas necesarias
            if assignment.estimated_hours > 0:
                hours_needed = assignment.estimated_hours
            else:
                hours_needed = assignment.tier_capacity * assignment.devs_assigned
            
            # Calcular días necesarios
            hours_per_day = assignment.devs_assigned * 8
            days_needed = ceil(hours_needed / hours_per_day)
            
            # Encontrar primera fecha disponible
            start_date = max(project_start, assignment.ready_to_start_date)
            while not team_has_capacity(assignment.team_id, start_date, days_needed, assignment.devs_assigned):
                start_date = next_business_day(start_date)
            
            # Registrar asignación
            end_date = start_date + business_days(days_needed)
            active_assignments_by_team[assignment.team_id].append({
                'start': start_date,
                'end': end_date,
                'devs': assignment.devs_assigned
            })
            
            # Actualizar inicio del siguiente fase
            project_start = next_business_day(end_date)
        
        # Registrar fecha de finalización del proyecto
        project_completion_dates[project.id] = project_start

def team_has_capacity(team_id, start_date, days_needed, devs_required):
    """Verifica si el equipo tiene capacidad suficiente en el período"""
    team = teams_capacity[team_id]
    
    for day_offset in range(days_needed):
        check_date = start_date + business_days(day_offset)
        
        # Calcular desarrolladores ocupados en esta fecha
        occupied_devs = team.busy_devs
        for assignment in active_assignments_by_team[team_id]:
            if assignment['start'] <= check_date <= assignment['end']:
                occupied_devs += assignment['devs']
        
        # Verificar si hay capacidad suficiente
        if occupied_devs + devs_required > team.total_devs:
            return False
    
    return True
```

## Consideraciones para Mejoras en Forecasting

### Variables Críticas para "What-If"

1. **Priority Manipulation**: Cambiar `projects.priority` afecta el orden de simulación
2. **Resource Allocation**: Modificar `devs_assigned` cambia duración y capacidad requerida
3. **Complexity Adjustment**: Cambiar `tier` altera las horas base necesarias
4. **Capacity Planning**: Ajustar `teams.total_devs` para simular contrataciones/reasignaciones

### Métricas de Optimización Propuestas

```sql
-- Utilización promedio por equipo
SELECT 
    t.name,
    AVG(occupied_devs / total_devs * 100) as avg_utilization
FROM teams t
JOIN simulation_results sr ON t.id = sr.team_id
GROUP BY t.name;

-- Identificar cuellos de botella
SELECT 
    team_name,
    COUNT(*) as projects_delayed,
    AVG(delay_days) as avg_delay
FROM bottleneck_analysis
GROUP BY team_name
ORDER BY projects_delayed DESC;
```

Este modelo de datos está optimizado para la simulación de cronogramas y permite flexibilidad en la configuración de complejidades y capacidades, siendo la base perfecta para implementar funcionalidades avanzadas de "what-if" analysis.