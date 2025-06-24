# Módulo de Simulación APE

Módulo simple para simular cronogramas de proyectos y hacer análisis what-if.

## Archivos

- `models.py` - Modelos de datos básicos
- `scheduler.py` - Simulador principal
- `integration.py` - Integración con la base de datos APE
- `demo.py` - Demo del caso Alpha-Beta
- `test_scheduler.py` - Tests y ejemplos what-if

## Uso Básico

```python
from modules.simulation import ProjectScheduler, Assignment, Team
from datetime import date

# Crear equipos
teams = {
    2: Team(id=2, name="Arch", total_devs=2, busy_devs=0),
    3: Team(id=3, name="Model", total_devs=4, busy_devs=0)
}

# Crear asignaciones
assignments = [
    Assignment(
        project_id=1, project_name="Alpha", phase="Arch", phase_order=0,
        team_id=2, priority=1, devs_assigned=1, hours_needed=16,
        ready_date=date(2025, 6, 16)
    )
]

# Simular
scheduler = ProjectScheduler()
result = scheduler.simulate(assignments, teams)

# Ver resultados
for assignment in result.assignments:
    print(f"{assignment.project_name} - {assignment.phase}: "
          f"{assignment.start_date} → {assignment.end_date}")
```

## Ejecutar Demo

```bash
cd app
python -m modules.simulation.demo
```

## Casos de Test

```bash
cd app
python -m modules.simulation.test_scheduler
```

## Integración con APE

```python
from modules.simulation.integration import run_simulation_from_db, format_for_streamlit

# Simular usando datos de la DB
result = run_simulation_from_db()

# Formatear para Streamlit
schedule_df, summary_df = format_for_streamlit(result)
```

## Análisis What-If

El módulo permite fácilmente cambiar parámetros y comparar escenarios:

- Cambiar prioridades de proyectos
- Modificar capacidad de equipos
- Ajustar asignación de desarrolladores
- Cambiar fechas de inicio

Ver `test_scheduler.py` para ejemplos completos.