"""
Tests de casos límite y manejo de errores en simulación APE
Tests limpios para casos edge y validación de robustez del scheduler
"""

import pytest
from datetime import date
from app.modules.common.models import Team, Project, Assignment, SimulationInput
from app.modules.simulation.scheduler import ProjectScheduler


class TestEdgeCases:
    """Tests para casos límite del algoritmo de scheduling"""
    
    def test_zero_capacity_team(self):
        """Test equipo sin capacidad disponible - debería fallar"""
        teams = {1: Team(id=1, name="Busy Team", total_devs=2, busy_devs=2)}  # Sin capacidad
        projects = {1: Project(id=1, name="Test", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Test", project_priority=1,
                                 team_id=1, team_name="Busy Team", tier=3, devs_assigned=1.0,
                                 max_devs=2.0, estimated_hours=40, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        
        # Debería lanzar excepción por falta de capacidad permanente
        with pytest.raises(ValueError, match="No se pudo encontrar slot disponible"):
            result = scheduler.simulate(simulation_input)
    
    def test_infinite_loop_protection(self):
        """Test protección contra loops infinitos en búsqueda de slots"""
        # Crear escenario imposible: más devs requeridos que capacidad total
        teams = {1: Team(id=1, name="Small Team", total_devs=1, tier_capacities={3: 40})}
        projects = {1: Project(id=1, name="Impossible", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Impossible", project_priority=1,
                                 team_id=1, team_name="Small Team", tier=3, devs_assigned=5.0,  # Imposible
                                 max_devs=5.0, estimated_hours=40, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        
        # Debería lanzar ValueError por protección contra loop infinito
        with pytest.raises(ValueError, match="No se pudo encontrar slot disponible"):
            scheduler.simulate(simulation_input)
    
    def test_empty_assignments_list(self):
        """Test simulación con lista vacía de asignaciones"""
        teams = {1: Team(id=1, name="Devs", total_devs=5, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Empty", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = []  # Lista vacía
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Debería manejar gracefully
        assert len(result.assignments) == 0
        assert len(result.project_summaries) == 0
    
    def test_empty_teams_dict(self):
        """Test simulación sin equipos"""
        teams = {}  # Sin equipos
        projects = {1: Project(id=1, name="No Teams", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="No Teams", project_priority=1,
                                 team_id=1, team_name="Missing Team", tier=3, devs_assigned=1.0,
                                 max_devs=2.0, estimated_hours=40, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        
        # Debería lanzar KeyError por team inexistente
        with pytest.raises(KeyError):
            scheduler.simulate(simulation_input)
    
    def test_zero_hours_assignment(self):
        """Test asignación con 0 horas estimadas"""
        teams = {1: Team(id=1, name="Devs", total_devs=3, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Zero Hours", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Zero Hours", project_priority=1,
                                 team_id=1, team_name="Devs", tier=3, devs_assigned=1.0,
                                 max_devs=3.0, estimated_hours=0, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assignment = result.assignments[0]
        
        # Debería manejar el caso y asignar al menos 1 día
        assert assignment.calculated_start_date is not None
        assert assignment.calculated_end_date is not None
        assert assignment.calculated_start_date <= assignment.calculated_end_date
    
    def test_zero_devs_assigned(self):
        """Test asignación con 0 devs asignados"""
        teams = {1: Team(id=1, name="Devs", total_devs=3, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Zero Devs", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Zero Devs", project_priority=1,
                                 team_id=1, team_name="Devs", tier=3, devs_assigned=0.0,  # 0 devs
                                 max_devs=3.0, estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assignment = result.assignments[0]
        
        # Debería manejar el caso (probablemente asignar 1 día por defecto)
        assert assignment.calculated_start_date is not None
        assert assignment.calculated_end_date is not None
    
    def test_missing_tier_capacity(self):
        """Test cuando el tier no existe en las capacidades del equipo"""
        teams = {1: Team(id=1, name="Limited Team", total_devs=3, tier_capacities={1: 16, 2: 32})}  # Sin tier 3
        projects = {1: Project(id=1, name="Missing Tier", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Missing Tier", project_priority=1,
                                 team_id=1, team_name="Limited Team", tier=3, devs_assigned=1.0,  # Tier 3 no existe
                                 max_devs=3.0, estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assignment = result.assignments[0]
        
        # Debería usar estimated_hours como fallback
        assert assignment.calculated_start_date is not None
        assert assignment.calculated_end_date is not None
        # Verificar que usó estimated_hours: 80h / (1 dev * 8h/día) = 10 días
        expected_duration = 10  # días hábiles
        actual_duration = (assignment.calculated_end_date - assignment.calculated_start_date).days + 1
        # Permitir cierta flexibilidad por días hábiles vs calendario
        assert 8 <= actual_duration <= 15  # Ajustado para incluir fines de semana
    
    def test_very_old_ready_to_start_date(self):
        """Test con fecha ready_to_start muy antigua"""
        teams = {1: Team(id=1, name="Devs", total_devs=3, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Old Date", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Old Date", project_priority=1,
                                 team_id=1, team_name="Devs", tier=3, devs_assigned=1.0,
                                 max_devs=3.0, estimated_hours=80, ready_to_start_date=date(2020, 1, 1),  # Muy antigua
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assignment = result.assignments[0]
        
        # Debería usar la fecha de simulación como mínimo
        assert assignment.calculated_start_date >= date(2025, 1, 1)
    
    def test_very_future_ready_to_start_date(self):
        """Test con fecha ready_to_start muy futura"""
        teams = {1: Team(id=1, name="Devs", total_devs=3, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Future Date", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Future Date", project_priority=1,
                                 team_id=1, team_name="Devs", tier=3, devs_assigned=1.0,
                                 max_devs=3.0, estimated_hours=80, ready_to_start_date=date(2030, 1, 1),  # Muy futura
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assignment = result.assignments[0]
        
        # Debería respetar la fecha futura
        assert assignment.calculated_start_date >= date(2030, 1, 1)
    
    def test_single_assignment_project(self):
        """Test proyecto con una sola asignación"""
        teams = {1: Team(id=1, name="Devs", total_devs=3, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Single Assignment", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Single Assignment", project_priority=1,
                                 team_id=1, team_name="Devs", tier=3, devs_assigned=1.0,
                                 max_devs=3.0, estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Verificar que funciona correctamente
        assert len(result.assignments) == 1
        assert len(result.project_summaries) == 1
        
        assignment = result.assignments[0]
        assert assignment.calculated_start_date == date(2025, 1, 1)
        assert assignment.calculated_end_date is not None
        
        # Verificar resumen del proyecto
        summary = result.project_summaries[0]
        assert summary['project_id'] == 1
        assert summary['total_assignments'] == 1
    
    def test_fractional_devs_assigned(self):
        """Test con asignación fraccionaria de devs (ej: 1.5 devs)"""
        teams = {1: Team(id=1, name="Devs", total_devs=5, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Fractional", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Fractional", project_priority=1,
                                 team_id=1, team_name="Devs", tier=3, devs_assigned=1.5,  # Fraccionario
                                 max_devs=5.0, estimated_hours=120, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assignment = result.assignments[0]
        
        # Debería manejar correctamente los devs fraccionarios
        assert assignment.calculated_start_date is not None
        assert assignment.calculated_end_date is not None
        
        # Verificar cálculo: 120h / (1.5 devs * 8h/día) = 10 días
        expected_duration = 10
        actual_duration = (assignment.calculated_end_date - assignment.calculated_start_date).days + 1
        assert 8 <= actual_duration <= 15  # Flexibilidad por días hábiles y fines de semana