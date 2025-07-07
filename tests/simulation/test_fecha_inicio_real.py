"""
Tests para verificar el uso de `fecha_inicio_real` en la simulación
"""
import pytest
from datetime import date, timedelta
from app.modules.common.models import Team, Project, Assignment, SimulationInput
from app.modules.simulation.scheduler import ProjectScheduler

class TestFechaInicioReal:
    """Testea que el scheduler respete la fecha_inicio_real"""

    def test_scheduler_usa_fecha_inicio_real(self):
        """
        Test que la simulación usa `fecha_inicio_real` si está presente,
        ignorando `ready_to_start_date` si es anterior.
        """
        teams = {1: Team(id=1, name="Arch", total_devs=2)}
        
        # fecha_inicio_real es posterior a ready_to_start_date
        fecha_inicio = date(2025, 6, 29)
        
        projects = {
            1: Project(
                id=1, name="Test Project", priority=1,
                start_date=date(2025, 6, 1),
                due_date_wo_qa=date(2025, 7, 1),
                due_date_with_qa=date(2025, 7, 15),
                fecha_inicio_real=fecha_inicio
            )
        }
        
        assignments = [
            Assignment(
                id=1, project_id=1, team_id=1, team_name="Arch",
                estimated_hours=16,
                ready_to_start_date=date(2025, 6, 25), # Esta fecha debe ser ignorada
                project_name="p", project_priority=1, tier=1, 
                devs_assigned=1, max_devs=1, assignment_start_date=date(2025,6,1)
            )
        ]

        simulation_input = SimulationInput(
            teams=teams,
            projects=projects,
            assignments=assignments,
            simulation_start_date=date(2025, 6, 25)
        )

        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)

        assert len(result.assignments) == 1
        first_assignment = result.assignments[0]

        # La fecha de inicio calculada debe ser la fecha_inicio_real, no la ready_to_start_date
        assert first_assignment.calculated_start_date == fecha_inicio, \
            f"La asignación de Arch debería comenzar en la fecha_inicio_real ({fecha_inicio}), pero comienza en {first_assignment.calculated_start_date}"

    def test_scheduler_usa_ready_date_si_es_posterior(self):
        """
        Test que la simulación usa `ready_to_start_date` si es posterior
        a `fecha_inicio_real`.
        """
        teams = {1: Team(id=1, name="Arch", total_devs=2)}
        
        # ready_to_start_date es posterior a fecha_inicio_real
        fecha_ready = date(2025, 7, 5)
        
        projects = {
            1: Project(
                id=1, name="Test Project", priority=1,
                start_date=date(2025, 6, 1),
                due_date_wo_qa=date(2025, 8, 1),
                due_date_with_qa=date(2025, 8, 15),
                fecha_inicio_real=date(2025, 7, 1) # Esta fecha debe ser ignorada
            )
        }
        
        assignments = [
            Assignment(
                id=1, project_id=1, team_id=1, team_name="Arch",
                estimated_hours=16,
                ready_to_start_date=fecha_ready,
                project_name="p", project_priority=1, tier=1, 
                devs_assigned=1, max_devs=1, assignment_start_date=date(2025,6,1)
            )
        ]

        simulation_input = SimulationInput(
            teams=teams,
            projects=projects,
            assignments=assignments,
            simulation_start_date=date(2025, 6, 25)
        )

        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)

        assert len(result.assignments) == 1
        first_assignment = result.assignments[0]

        # La fecha de inicio calculada debe ser la fecha_ready, que es la restricción más tardía
        assert first_assignment.calculated_start_date == fecha_ready, \
            f"La asignación debería comenzar en la fecha_ready ({fecha_ready}), pero comienza en {first_assignment.calculated_start_date}"