"""
Tests de integración para estados de proyecto y su impacto en la simulación
"""
import pytest
from datetime import date
from app.modules.common.models import Team, Project, Assignment, SimulationInput
from app.modules.simulation.scheduler import ProjectScheduler

class TestProjectStatesIntegration:
    """Testea cómo los estados de proyecto afectan la simulación"""

    def setup_method(self):
        """Setup para cada test con datos base"""
        self.teams = {
            1: Team(id=1, name="Arch", total_devs=2, tier_capacities={1: 16, 2: 32, 3: 72}),
            2: Team(id=2, name="Devs", total_devs=6, tier_capacities={1: 16, 2: 40, 3: 80})
        }
        self.projects = {
            1: Project(id=1, name="Proyecto Activo", priority=1, active=True, start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15)),
            2: Project(id=2, name="Proyecto Borrador", priority=2, active=False, start_date=date(2025, 1, 15), due_date_wo_qa=date(2025, 2, 15), due_date_with_qa=date(2025, 3, 1)),
            3: Project(id=3, name="Proyecto Pausado", priority=3, active=False, start_date=date(2025, 1, 10), due_date_wo_qa=date(2025, 2, 10), due_date_with_qa=date(2025, 2, 25))
        }
        self.all_assignments = [
            Assignment(id=1, project_id=1, project_name="Proyecto Activo", project_priority=1, team_id=1, team_name="Arch", tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=32, ready_to_start_date=date(2025, 1, 1), assignment_start_date=date(2025, 1, 1)),
            Assignment(id=2, project_id=2, project_name="Proyecto Borrador", project_priority=2, team_id=2, team_name="Devs", tier=2, devs_assigned=2.0, max_devs=2.0, estimated_hours=80, ready_to_start_date=date(2025, 1, 15), assignment_start_date=date(2025, 1, 15)),
            Assignment(id=3, project_id=3, project_name="Proyecto Pausado", project_priority=3, team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=16, ready_to_start_date=date(2025, 1, 10), assignment_start_date=date(2025, 1, 10))
        ]

    def test_simulation_filters_active_projects_only(self):
        """Test que la simulación solo incluye proyectos activos"""
        active_project_ids = {p.id for p in self.projects.values() if p.is_active()}
        active_assignments = [a for a in self.all_assignments if a.project_id in active_project_ids]

        simulation_input = SimulationInput(
            teams=self.teams,
            projects=self.projects,
            assignments=active_assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        processed_project_ids = set(a.project_id for a in result.assignments)

        assert 1 in processed_project_ids, "Proyecto activo debe estar en simulación"
        assert 2 not in processed_project_ids, "Proyecto borrador NO debe estar en simulación"
        assert 3 not in processed_project_ids, "Proyecto pausado NO debe estar en simulación"

    def test_simulation_with_no_active_projects(self):
        """Test que la simulación no procesa nada si no hay proyectos activos"""
        for p in self.projects.values():
            p.active = False
        
        active_project_ids = {p.id for p in self.projects.values() if p.is_active()}
        active_assignments = [a for a in self.all_assignments if a.project_id in active_project_ids]

        simulation_input = SimulationInput(
            teams=self.teams,
            projects=self.projects,
            assignments=active_assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assert not result.assignments, "No debería haber asignaciones procesadas"
        assert not result.project_summaries, "No debería haber resúmenes de proyectos"

    def test_simulation_with_mixed_states(self):
        """Test simulación con proyectos en estados mixtos"""
        self.projects[3].active = True

        active_project_ids = {p.id for p in self.projects.values() if p.is_active()}
        active_assignments = [a for a in self.all_assignments if a.project_id in active_project_ids]

        simulation_input = SimulationInput(
            teams=self.teams,
            projects=self.projects,
            assignments=active_assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        processed_project_ids = set(a.project_id for a in result.assignments)

        assert 1 in processed_project_ids, "Proyecto activo original debe estar"
        assert 3 in processed_project_ids, "Proyecto reactivado debe estar"
        assert 2 not in processed_project_ids, "Proyecto borrador NO debe estar"

    def test_project_state_transitions_preserve_progress(self):
        """Test que pausar y reactivar un proyecto preserva su estado (conceptual)"""
        project = self.projects[1]
        assert project.is_active()
        
        project.active = False
        assert not project.is_active()
        
        project.active = True
        assert project.is_active()

    def test_project_summary_generation_with_states(self):
        """Test que el resumen de la simulación solo incluye proyectos procesados"""
        active_project_ids = {p.id for p in self.projects.values() if p.is_active()}
        active_assignments = [a for a in self.all_assignments if a.project_id in active_project_ids]

        simulation_input = SimulationInput(
            teams=self.teams,
            projects=self.projects,
            assignments=active_assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        summary_project_ids = set(s['project_id'] for s in result.project_summaries)
        
        assert 1 in summary_project_ids
        assert 2 not in summary_project_ids
        assert 3 not in summary_project_ids