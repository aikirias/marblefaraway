"""
Tests para la lógica central del scheduler (core)
"""
import pytest
from datetime import date
from app.modules.common.models import Team, Project, Assignment, SimulationInput
from app.modules.simulation.scheduler import ProjectScheduler

class TestSimulationCore:
    """Testea la lógica fundamental de secuenciación y priorización"""

    def test_phase_sequence_within_project(self):
        """Test que las fases DENTRO de un proyecto son secuenciales"""
        teams = {
            1: Team(id=1, name="Arch", total_devs=1, tier_capacities={1: 160}),
            2: Team(id=2, name="Model", total_devs=1, tier_capacities={2: 80}),
            3: Team(id=3, name="Devs", total_devs=1, tier_capacities={3: 80}),
        }
        projects = {1: Project(id=1, name="TestProject", priority=1, start_date=date(2025, 6, 26), due_date_wo_qa=date(2025, 9, 1), due_date_with_qa=date(2025, 9, 15))}
        assignments = [
            Assignment(id=1, project_id=1, project_name="TestProject", project_priority=1, team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=160, ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)),
            Assignment(id=2, project_id=1, project_name="TestProject", project_priority=1, team_id=3, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=1.0, estimated_hours=80, ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)),
            Assignment(id=3, project_id=1, project_name="TestProject", project_priority=1, team_id=2, team_name="Model", tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=80, ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)),
        ]
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 6, 26))
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)

        arch = next(a for a in result.assignments if a.team_name == "Arch")
        devs = next(a for a in result.assignments if a.team_name == "Devs")
        model = next(a for a in result.assignments if a.team_name == "Model")

        assert arch.calculated_start_date == date(2025, 6, 26)
        assert devs.calculated_start_date >= arch.calculated_end_date
        assert model.calculated_start_date >= devs.calculated_end_date

    def test_priority_order_with_sufficient_capacity(self):
        """Test que proyectos se ejecutan en paralelo si hay capacidad"""
        teams = {1: Team(id=1, name="Arch", total_devs=5, tier_capacities={1: 16})}
        projects = {
            1: Project(id=1, name="B", priority=1, start_date=date(2025, 6, 26), due_date_wo_qa=date(2025, 9, 1), due_date_with_qa=date(2025, 9, 15)),
            2: Project(id=2, name="a", priority=2, start_date=date(2025, 6, 26), due_date_wo_qa=date(2025, 9, 1), due_date_with_qa=date(2025, 9, 15)),
        }
        assignments = [
            Assignment(id=1, project_id=1, project_name="B", project_priority=1, team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=16, ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)),
            Assignment(id=2, project_id=2, project_name="a", project_priority=2, team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=16, ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)),
        ]
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 6, 26))
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)

        proj_b = next(a for a in result.assignments if a.project_name == "B")
        proj_a = next(a for a in result.assignments if a.project_name == "a")

        # Con capacidad suficiente, ambos deben empezar el mismo día
        assert proj_b.calculated_start_date == date(2025, 6, 26)
        assert proj_a.calculated_start_date == date(2025, 6, 26)

    def test_priority_order_with_limited_capacity(self):
        """Test que la prioridad se respeta cuando la capacidad es limitada"""
        teams = {1: Team(id=1, name="Arch", total_devs=1, tier_capacities={1: 16})} # Solo 1 dev
        projects = {
            1: Project(id=1, name="B", priority=1, start_date=date(2025, 6, 26), due_date_wo_qa=date(2025, 9, 1), due_date_with_qa=date(2025, 9, 15)),
            2: Project(id=2, name="a", priority=2, start_date=date(2025, 6, 26), due_date_wo_qa=date(2025, 9, 1), due_date_with_qa=date(2025, 9, 15)),
        }
        assignments = [
            Assignment(id=1, project_id=1, project_name="B", project_priority=1, team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=16, ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)),
            Assignment(id=2, project_id=2, project_name="a", project_priority=2, team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=16, ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)),
        ]
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 6, 26))
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)

        proj_b = next(a for a in result.assignments if a.project_name == "B")
        proj_a = next(a for a in result.assignments if a.project_name == "a")

        assert proj_b.calculated_start_date == date(2025, 6, 26)
        assert proj_a.calculated_start_date >= proj_b.calculated_end_date