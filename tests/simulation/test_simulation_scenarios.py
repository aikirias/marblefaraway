"""
Tests para escenarios de simulación complejos y workflows completos
"""
import pytest
from datetime import date
from app.modules.common.models import Team, Project, Assignment, SimulationInput
from app.modules.simulation.scheduler import ProjectScheduler

class TestSimulationScenarios:
    """Testea flujos de trabajo completos y escenarios complejos"""

    def test_simple_project_sequential_phases(self):
        """Test que las fases de un proyecto simple son secuenciales"""
        teams = {
            2: Team(id=2, name="Arch", total_devs=1),
            1: Team(id=1, name="Devs", total_devs=1),
            3: Team(id=3, name="Model", total_devs=1),
            4: Team(id=4, name="Dqa", total_devs=1)
        }
        projects = {1: Project(id=1, name="Simple Project", priority=1, start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 3, 1), due_date_with_qa=date(2025, 3, 15))}
        assignments = [
            Assignment(id=1, project_id=1, team_id=2, team_name="Arch", estimated_hours=16, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, tier=1, devs_assigned=1, max_devs=1, assignment_start_date=date(2025,1,1)),
            Assignment(id=2, project_id=1, team_id=1, team_name="Devs", estimated_hours=80, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, tier=1, devs_assigned=1, max_devs=1, assignment_start_date=date(2025,1,1)),
            Assignment(id=3, project_id=1, team_id=3, team_name="Model", estimated_hours=80, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, tier=1, devs_assigned=1, max_devs=1, assignment_start_date=date(2025,1,1)),
            Assignment(id=4, project_id=1, team_id=4, team_name="Dqa", estimated_hours=24, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, tier=1, devs_assigned=1, max_devs=1, assignment_start_date=date(2025,1,1)),
        ]
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 1, 1))
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)

        arch = next(a for a in result.assignments if a.team_name == "Arch")
        devs = next(a for a in result.assignments if a.team_name == "Devs")
        model = next(a for a in result.assignments if a.team_name == "Model")
        dqa = next(a for a in result.assignments if a.team_name == "Dqa")

        assert arch.calculated_start_date == date(2025, 1, 1)
        assert devs.calculated_start_date >= arch.calculated_end_date
        assert model.calculated_start_date >= devs.calculated_end_date
        assert dqa.calculated_start_date >= model.calculated_end_date

    def test_multiple_projects_with_shared_teams(self):
        """Test de múltiples proyectos compitiendo por los mismos equipos"""
        teams = {1: Team(id=1, name="Devs", total_devs=2)}
        projects = {
            1: Project(id=1, name="Project A", priority=1, start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15)),
            2: Project(id=2, name="Project B", priority=2, start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15)),
        }
        assignments = [
            Assignment(id=1, project_id=1, team_id=1, team_name="Devs", estimated_hours=80, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, tier=1, devs_assigned=2, max_devs=2, assignment_start_date=date(2025,1,1)), # Usa todo el equipo
            Assignment(id=2, project_id=2, team_id=1, team_name="Devs", estimated_hours=80, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=2, tier=1, devs_assigned=1, max_devs=1, assignment_start_date=date(2025,1,1)),
        ]
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 1, 1))
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)

        proj_a = next(a for a in result.assignments if a.project_id == 1)
        proj_b = next(a for a in result.assignments if a.project_id == 2)

        # Proyecto A (prioridad 1) debe empezar primero y bloquear al equipo
        assert proj_a.calculated_start_date == date(2025, 1, 1)
        # Proyecto B (prioridad 2) debe esperar a que A termine
        assert proj_b.calculated_start_date >= proj_a.calculated_end_date