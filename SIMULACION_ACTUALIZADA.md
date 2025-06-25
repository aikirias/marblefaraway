# Simulación Actualizada con Modelos Reales de APE

## Resumen de Cambios Realizados

Se ha actualizado completamente el módulo de simulación para usar la estructura real de la aplicación APE, eliminando los templates predefinidos y trabajando con los modelos reales de teams y projects.

## Cambios Principales

### 1. Modelos Actualizados (`app/modules/simulation/models.py`)

**Antes:**
- Modelos simplificados con `Assignment` básico
- `Team` solo con `total_devs` y `busy_devs`
- Sin concepto de tiers ni capacidades por tier

**Ahora:**
- **`Team`**: Incluye `tier_capacities` (Dict[int, int]) que mapea tier → horas por persona
- **`Project`**: Estructura completa con `priority`, `start_date`, `due_date_wo_qa`, `due_date_with_qa`
- **`Assignment`**: Estructura real con `tier`, `devs_assigned`, `max_devs`, `estimated_hours`, `ready_to_start_date`
- **`SimulationInput`**: Contenedor completo para todos los datos de entrada

### 2. Scheduler Actualizado (`app/modules/simulation/scheduler.py`)

**Funcionalidades nuevas:**
- **Cálculo automático de horas**: Usa `tier` × `devs_assigned` × `hours_per_person_for_tier`
- **Constraint de fecha ready**: Respeta `ready_to_start_date` como fecha mínima de inicio
- **Prioridad de proyectos**: Ordena asignaciones por `project_priority`
- **Resumen mejorado**: Incluye delays, horas totales, estados más detallados

### 3. Interfaz Actualizada (`app/modules/simulation/simulation.py`)

**Mejoras:**
- **Teams con tier capacities**: Muestra capacidades por tier basadas en datos reales
- **Configuración de tiers**: Permite seleccionar tier por proyecto
- **Visualizaciones mejoradas**: Gantt chart con información de tiers y horas
- **Métricas avanzadas**: Utilización de equipos, delays, etc.

## Estructura de Datos Real Implementada

### Teams
```python
Team(
    id=1,
    name="Arch",
    total_devs=2,
    busy_devs=0,
    tier_capacities={1: 16, 2: 32, 3: 72, 4: 240}  # horas por persona
)
```

### Projects
```python
Project(
    id=1,
    name="Alpha",
    priority=1,
    start_date=date(2025, 6, 16),
    due_date_wo_qa=date(2025, 7, 16),
    due_date_with_qa=date(2025, 7, 21)
)
```

### Assignments
```python
Assignment(
    id=1,
    project_id=1,
    project_name="Alpha",
    project_priority=1,
    team_id=1,
    team_name="Arch",
    tier=2,                           # Determina horas necesarias
    devs_assigned=1.0,
    max_devs=1.0,
    estimated_hours=0,                # Fallback si no hay tier capacity
    ready_to_start_date=date(2025, 6, 16),  # Constraint de fecha
    assignment_start_date=date(2025, 6, 16)
)
```

## Lógica de Cálculo de Horas

El simulador ahora calcula automáticamente las horas necesarias:

```python
def get_hours_needed(self, team: Team) -> int:
    hours_per_person = team.get_hours_per_person_for_tier(self.tier)
    if hours_per_person == 0:
        return self.estimated_hours  # Fallback
    return int(hours_per_person * self.devs_assigned)
```

**Ejemplo:**
- Team "Arch", Tier 2 = 32 horas/persona
- Assignment con 1.0 dev asignado
- Horas necesarias = 32 × 1.0 = 32 horas

## Constraints Implementados

1. **Ready to Start Date**: No puede empezar antes de `ready_to_start_date`
2. **Capacidad de Team**: No puede exceder `total_devs - busy_devs`
3. **Dependencias de Proyecto**: Las asignaciones del mismo proyecto se ejecutan secuencialmente
4. **Prioridad**: Los proyectos con menor número de prioridad se programan primero

## Resultados de Prueba

La prueba exitosa muestra:

```
Alpha-Arch: Tier 2 -> 32h en 4 días (2025-06-16 a 2025-06-19)
Alpha-Model: Tier 2 -> 80h en 14 días (2025-06-20 a 2025-07-03)
Alpha-Devs: Tier 2 -> 40h en 7 días (2025-07-04 a 2025-07-10)
Alpha-Dqa: Tier 2 -> 24h en 5 días (2025-07-11 a 2025-07-15)

Beta-Arch: Tier 1 -> 16h en 2 días (2025-06-16 a 2025-06-17)
Beta-Model: Tier 1 -> 40h en 7 días (2025-06-18 a 2025-06-24)
```

## Archivos Modificados

1. **`app/modules/simulation/models.py`** - Modelos actualizados
2. **`app/modules/simulation/scheduler.py`** - Lógica de scheduling actualizada
3. **`app/modules/simulation/simulation.py`** - Interfaz actualizada
4. **`test_simulation_standalone.py`** - Script de prueba (temporal)

## Estado Actual

✅ **Completado:**
- Modelos actualizados con estructura real de APE
- Scheduler funcionando con tiers y constraints
- Interfaz actualizada con nuevas funcionalidades
- Pruebas exitosas del simulador

✅ **Funciona correctamente:**
- Cálculo automático de horas basado en tiers
- Respeto de constraints de fecha ready
- Scheduling por prioridad de proyectos
- Visualizaciones mejoradas

El simulador ahora refleja fielmente la estructura real de la aplicación APE y está listo para uso en producción.