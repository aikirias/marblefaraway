"""
Unit tests para modelos del sistema APE
"""

import pytest
from datetime import date
from app.modules.common.models import Team, Project, Assignment, ScheduleResult, SimulationInput


class TestTeam:
    """Tests para el modelo Team"""
    
    def test_get_available_devs_normal_case(self, sample_team):
        """Test cálculo de devs disponibles - caso normal"""
        assert sample_team.get_available_devs() == 4  # 5 total - 1 busy
    
    def test_get_available_devs_all_busy(self, sample_team):
        """Test cuando todos los devs están ocupados"""
        sample_team.busy_devs = 5
        assert sample_team.get_available_devs() == 0
    
    def test_get_available_devs_over_capacity(self, sample_team):
        """Test cuando busy_devs > total_devs (caso edge)"""
        sample_team.busy_devs = 7
        assert sample_team.get_available_devs() == 0  # No puede ser negativo
    
    def test_get_hours_per_person_for_tier_existing(self, sample_team):
        """Test obtener horas para tier existente"""
        assert sample_team.get_hours_per_person_for_tier(3) == 80
    
    def test_get_hours_per_person_for_tier_missing(self, sample_team):
        """Test obtener horas para tier inexistente"""
        assert sample_team.get_hours_per_person_for_tier(5) == 0
    
    def test_tier_capacities_initialization(self):
        """Test inicialización de tier_capacities"""
        team = Team(id=1, name="Test", total_devs=5)
        assert team.tier_capacities == {}
        
        team_with_tiers = Team(id=2, name="Test2", total_devs=3, 
                              tier_capacities={1: 16, 2: 32})
        assert team_with_tiers.tier_capacities == {1: 16, 2: 32}


class TestProject:
    """Tests para el modelo Project"""
    
    def test_project_creation(self, sample_project):
        """Test creación básica de proyecto"""
        assert sample_project.id == 1
        assert sample_project.name == "Test Project"
        assert sample_project.priority == 1
        assert sample_project.start_date == date(2025, 1, 1)
        assert sample_project.due_date_wo_qa == date(2025, 2, 1)
        assert sample_project.due_date_with_qa == date(2025, 2, 15)
    
    def test_project_dates_order(self, sample_project):
        """Test que las fechas están en orden lógico"""
        assert sample_project.start_date <= sample_project.due_date_wo_qa
        assert sample_project.due_date_wo_qa <= sample_project.due_date_with_qa


class TestAssignment:
    """Tests para el modelo Assignment"""
    
    def test_get_hours_needed_with_tier_capacity(self, sample_assignment, sample_team):
        """Test cálculo de horas usando tier_capacity"""
        hours = sample_assignment.get_hours_needed(sample_team)
        assert hours == 160  # 80 hours_per_person * 2 devs_assigned
    
    def test_get_hours_needed_fallback_to_estimated(self, sample_assignment):
        """Test fallback a estimated_hours cuando tier_capacity es 0"""
        team_no_tier = Team(id=2, name="Test", total_devs=5, tier_capacities={})
        hours = sample_assignment.get_hours_needed(team_no_tier)
        assert hours == 80  # Fallback a estimated_hours
    
    def test_get_hours_needed_missing_tier(self, sample_assignment):
        """Test fallback cuando el tier no existe en team"""
        team_missing_tier = Team(id=3, name="Test", total_devs=5, 
                                tier_capacities={1: 16, 2: 32})  # Sin tier 3
        hours = sample_assignment.get_hours_needed(team_missing_tier)
        assert hours == 80  # Fallback a estimated_hours
    
    def test_can_start_on_valid_date(self, sample_assignment):
        """Test puede empezar en fecha válida"""
        assert sample_assignment.can_start_on(date(2025, 1, 15)) == True
    
    def test_can_start_on_early_date(self, sample_assignment):
        """Test no puede empezar antes de ready_to_start_date"""
        assert sample_assignment.can_start_on(date(2024, 12, 15)) == False
    
    def test_can_start_on_exact_date(self, sample_assignment):
        """Test puede empezar exactamente en ready_to_start_date"""
        assert sample_assignment.can_start_on(date(2025, 1, 1)) == True
    
    def test_assignment_calculated_fields_initialization(self, sample_assignment):
        """Test que campos calculados se inicializan correctamente"""
        assert sample_assignment.calculated_start_date is None
        assert sample_assignment.calculated_end_date is None
        assert sample_assignment.pending_hours == 0
        assert sample_assignment.paused_on is None


class TestScheduleResult:
    """Tests para el modelo ScheduleResult"""
    
    def test_get_project_end_date_with_assignments(self, sample_assignment):
        """Test obtener fecha de fin de proyecto con asignaciones"""
        # Setup asignaciones con fechas calculadas
        assignment1 = Assignment(
            id=1, project_id=1, project_name="Test", project_priority=1,
            team_id=1, team_name="Team1", tier=1, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=40, ready_to_start_date=date(2025, 1, 1),
            assignment_start_date=date(2025, 1, 1),
            calculated_start_date=date(2025, 1, 1),
            calculated_end_date=date(2025, 1, 10)
        )
        assignment2 = Assignment(
            id=2, project_id=1, project_name="Test", project_priority=1,
            team_id=2, team_name="Team2", tier=2, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=80, ready_to_start_date=date(2025, 1, 11),
            assignment_start_date=date(2025, 1, 11),
            calculated_start_date=date(2025, 1, 11),
            calculated_end_date=date(2025, 1, 20)
        )
        
        result = ScheduleResult(assignments=[assignment1, assignment2], project_summaries=[])
        
        # La fecha de fin del proyecto debe ser la máxima
        assert result.get_project_end_date(1) == date(2025, 1, 20)
    
    def test_get_project_end_date_no_assignments(self):
        """Test obtener fecha de fin cuando no hay asignaciones"""
        result = ScheduleResult(assignments=[], project_summaries=[])
        assert result.get_project_end_date(1) is None
    
    def test_get_project_start_date_with_assignments(self):
        """Test obtener fecha de inicio de proyecto con asignaciones"""
        assignment1 = Assignment(
            id=1, project_id=1, project_name="Test", project_priority=1,
            team_id=1, team_name="Team1", tier=1, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=40, ready_to_start_date=date(2025, 1, 5),
            assignment_start_date=date(2025, 1, 5),
            calculated_start_date=date(2025, 1, 5),
            calculated_end_date=date(2025, 1, 10)
        )
        assignment2 = Assignment(
            id=2, project_id=1, project_name="Test", project_priority=1,
            team_id=2, team_name="Team2", tier=2, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
            assignment_start_date=date(2025, 1, 1),
            calculated_start_date=date(2025, 1, 1),
            calculated_end_date=date(2025, 1, 4)
        )
        
        result = ScheduleResult(assignments=[assignment1, assignment2], project_summaries=[])
        
        # La fecha de inicio del proyecto debe ser la mínima
        assert result.get_project_start_date(1) == date(2025, 1, 1)
    
    def test_get_assignments_by_team(self):
        """Test filtrar asignaciones por equipo"""
        assignment1 = Assignment(
            id=1, project_id=1, project_name="Test", project_priority=1,
            team_id=1, team_name="Team1", tier=1, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=40, ready_to_start_date=date(2025, 1, 1),
            assignment_start_date=date(2025, 1, 1)
        )
        assignment2 = Assignment(
            id=2, project_id=1, project_name="Test", project_priority=1,
            team_id=2, team_name="Team2", tier=2, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
            assignment_start_date=date(2025, 1, 1)
        )
        
        result = ScheduleResult(assignments=[assignment1, assignment2], project_summaries=[])
        
        team1_assignments = result.get_assignments_by_team(1)
        assert len(team1_assignments) == 1
        assert team1_assignments[0].team_id == 1
        
        team2_assignments = result.get_assignments_by_team(2)
        assert len(team2_assignments) == 1
        assert team2_assignments[0].team_id == 2
    
    def test_get_assignments_by_project(self):
        """Test filtrar asignaciones por proyecto"""
        assignment1 = Assignment(
            id=1, project_id=1, project_name="Project1", project_priority=1,
            team_id=1, team_name="Team1", tier=1, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=40, ready_to_start_date=date(2025, 1, 1),
            assignment_start_date=date(2025, 1, 1)
        )
        assignment2 = Assignment(
            id=2, project_id=2, project_name="Project2", project_priority=2,
            team_id=1, team_name="Team1", tier=2, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
            assignment_start_date=date(2025, 1, 1)
        )
        
        result = ScheduleResult(assignments=[assignment1, assignment2], project_summaries=[])
        
        project1_assignments = result.get_assignments_by_project(1)
        assert len(project1_assignments) == 1
        assert project1_assignments[0].project_id == 1
        
        project2_assignments = result.get_assignments_by_project(2)
        assert len(project2_assignments) == 1
        assert project2_assignments[0].project_id == 2


class TestSimulationInput:
    """Tests para el modelo SimulationInput"""
    
    def test_simulation_input_creation(self, sample_simulation_input):
        """Test creación de SimulationInput"""
        assert len(sample_simulation_input.teams) == 4
        assert len(sample_simulation_input.projects) == 1
        assert len(sample_simulation_input.assignments) == 4
        assert sample_simulation_input.simulation_start_date == date(2025, 1, 1)
    
    def test_simulation_input_default_date(self, ape_teams, sample_project):
        """Test que simulation_start_date se inicializa con fecha actual por defecto"""
        from datetime import date
        
        projects = {sample_project.id: sample_project}
        assignments = []
        
        sim_input = SimulationInput(teams=ape_teams, projects=projects, assignments=assignments)
        
        # Debería usar la fecha de hoy por defecto
        assert sim_input.simulation_start_date == date.today()