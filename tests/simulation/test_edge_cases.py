"""
Tests para casos límite y validaciones del scheduler
"""
import pytest
from datetime import date
from app.modules.common.models import Team, Project, Assignment, SimulationInput
from app.modules.simulation.scheduler import ProjectScheduler

class TestEdgeCases:
    """Testea el comportamiento del scheduler en situaciones límite"""

    def test_empty_teams_dict(self):
        """Test con diccionario de equipos vacío, debe lanzar KeyError."""
        simulation_input = SimulationInput(
            teams={},
            projects={1: Project(id=1, name="p", priority=1, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today())},
            assignments=[Assignment(id=1, project_id=1, team_id=1, team_name="Missing", project_name="p", project_priority=1, tier=1, devs_assigned=1, max_devs=1, estimated_hours=1, ready_to_start_date=date.today(), assignment_start_date=date.today())],
            simulation_start_date=date(2025, 1, 1)
        )
        scheduler = ProjectScheduler()
        with pytest.raises(KeyError):
            scheduler.simulate(simulation_input)

    def test_zero_capacity_team_is_skipped(self):
        """Test que un equipo con 0 devs es ignorado, no lanza error."""
        teams = {1: Team(id=1, name="No Devs Team", total_devs=0)}
        projects = {1: Project(id=1, name="Test", priority=1, start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, team_id=1, team_name="No Devs Team", tier=3, devs_assigned=1.0, estimated_hours=40, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, max_devs=1, assignment_start_date=date.today())]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 1, 1))
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        assert len(result.assignments) == 0

    def test_negative_capacity_team_raises_error(self):
        """Test que un equipo con capacidad negativa lanza ValueError."""
        teams = {1: Team(id=1, name="Negative Devs", total_devs=-1)}
        projects = {1: Project(id=1, name="Test", priority=1, start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, team_id=1, team_name="Negative Devs", tier=3, devs_assigned=1.0, estimated_hours=40, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, max_devs=1, assignment_start_date=date.today())]

        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 1, 1))
        scheduler = ProjectScheduler()
        with pytest.raises(ValueError, match="tiene capacidad negativa"):
            scheduler.simulate(simulation_input)

    def test_assignment_requires_more_devs_than_team_has(self):
        """Test que una asignación que requiere más devs de los que el equipo tiene es ignorada."""
        teams = {1: Team(id=1, name="Small Team", total_devs=1)}
        projects = {1: Project(id=1, name="Impossible", priority=1, start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, team_id=1, team_name="Small Team", tier=3, devs_assigned=5.0, estimated_hours=40, ready_to_start_date=date(2025, 1, 1), project_name="p", project_priority=1, max_devs=5, assignment_start_date=date.today())]

        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments, simulation_start_date=date(2025, 1, 1))
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        assert len(result.assignments) == 0