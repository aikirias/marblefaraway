"""
Test del módulo de simulación con el caso de ejemplo
"""

from datetime import date
from .scheduler import ProjectScheduler
from .models import Assignment, Team


def test_alpha_beta_case():
    """Test case Alpha-Beta que validó tu jefe"""
    
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
        ),
        Assignment(
            project_id=1, project_name="Alpha", phase="Model", phase_order=1,
            team_id=3, priority=1, devs_assigned=1, hours_needed=40,
            ready_date=date(2025, 6, 16)
        ),
        Assignment(
            project_id=2, project_name="Beta", phase="Arch", phase_order=0,
            team_id=2, priority=2, devs_assigned=1, hours_needed=16,
            ready_date=date(2025, 6, 16)
        )
    ]
    
    # Ejecutar simulación
    scheduler = ProjectScheduler()
    result = scheduler.simulate(assignments, teams, today=date(2025, 6, 16))
    
    return result


def print_results(result):
    """Imprime los resultados de forma legible"""
    print("=== CRONOGRAMA DETALLADO ===")
    for assignment in result.assignments:
        print(f"{assignment.project_name} - {assignment.phase}: "
              f"{assignment.start_date} → {assignment.end_date} "
              f"({assignment.devs_assigned} devs)")
    
    print("\n=== RESUMEN POR PROYECTO ===")
    for summary in result.project_summaries:
        print(f"{summary['project_name']}: {summary['state']} "
              f"({summary['start_date']} → {summary['end_date']})")


def test_what_if_scenarios():
    """Ejemplos de análisis what-if"""
    
    # Escenario base
    print("ESCENARIO BASE:")
    result_base = test_alpha_beta_case()
    print_results(result_base)
    
    print("\n" + "="*50)
    
    # What-if: ¿Qué pasa si Beta tiene prioridad 1?
    print("WHAT-IF: Beta con prioridad 1")
    
    teams = {
        2: Team(id=2, name="Arch", total_devs=2, busy_devs=0),
        3: Team(id=3, name="Model", total_devs=4, busy_devs=0)
    }
    
    assignments_whatif = [
        Assignment(
            project_id=1, project_name="Alpha", phase="Arch", phase_order=0,
            team_id=2, priority=2, devs_assigned=1, hours_needed=16,  # Prioridad cambiada
            ready_date=date(2025, 6, 16)
        ),
        Assignment(
            project_id=1, project_name="Alpha", phase="Model", phase_order=1,
            team_id=3, priority=2, devs_assigned=1, hours_needed=40,  # Prioridad cambiada
            ready_date=date(2025, 6, 16)
        ),
        Assignment(
            project_id=2, project_name="Beta", phase="Arch", phase_order=0,
            team_id=2, priority=1, devs_assigned=1, hours_needed=16,  # Prioridad cambiada
            ready_date=date(2025, 6, 16)
        )
    ]
    
    scheduler = ProjectScheduler()
    result_whatif = scheduler.simulate(assignments_whatif, teams, today=date(2025, 6, 16))
    print_results(result_whatif)
    
    print("\n" + "="*50)
    
    # What-if: ¿Qué pasa si contratamos 1 dev más en Arch?
    print("WHAT-IF: +1 dev en equipo Arch")
    
    teams_more_devs = {
        2: Team(id=2, name="Arch", total_devs=3, busy_devs=0),  # +1 dev
        3: Team(id=3, name="Model", total_devs=4, busy_devs=0)
    }
    
    # Usar asignaciones originales
    assignments_original = [
        Assignment(
            project_id=1, project_name="Alpha", phase="Arch", phase_order=0,
            team_id=2, priority=1, devs_assigned=1, hours_needed=16,
            ready_date=date(2025, 6, 16)
        ),
        Assignment(
            project_id=1, project_name="Alpha", phase="Model", phase_order=1,
            team_id=3, priority=1, devs_assigned=1, hours_needed=40,
            ready_date=date(2025, 6, 16)
        ),
        Assignment(
            project_id=2, project_name="Beta", phase="Arch", phase_order=0,
            team_id=2, priority=2, devs_assigned=1, hours_needed=16,
            ready_date=date(2025, 6, 16)
        )
    ]
    
    result_more_devs = scheduler.simulate(assignments_original, teams_more_devs, today=date(2025, 6, 16))
    print_results(result_more_devs)


if __name__ == "__main__":
    # Ejecutar tests
    test_what_if_scenarios()