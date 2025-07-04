"""
Tests simplificados para el sistema de gestión de planes con prioridades persistentes
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock

from app.modules.common.models import Plan, PlanAssignment, ScheduleResult, Assignment, Project
from app.modules.common.priority_utils import (
    apply_plan_priorities_to_projects, get_effective_priority_with_plan,
    sort_by_plan_priority
)


class TestPlanAssignmentModel:
    """Tests para el modelo PlanAssignment con priority_order"""
    
    def test_plan_assignment_creation_with_priority_order(self):
        """Test creación de PlanAssignment con priority_order"""
        assignment = PlanAssignment(
            plan_id=1,
            assignment_id=10,
            project_id=5,
            project_name="Test Project",
            project_priority=3,
            priority_order=1,  # Prioridad específica del plan
            team_id=2,
            team_name="Test Team",
            tier=2,
            devs_assigned=2.0,
            estimated_hours=40
        )
        
        assert assignment.priority_order == 1
        assert assignment.project_priority == 3
    
    def test_plan_assignment_from_assignment_with_priority(self):
        """Test creación desde Assignment con prioridad específica"""
        original_assignment = Assignment(
            id=10,
            project_id=5,
            project_name="Test Project",
            project_priority=3,
            team_id=2,
            team_name="Test Team",
            tier=2,
            devs_assigned=2.0,
            max_devs=3.0,
            estimated_hours=40,
            ready_to_start_date=date.today(),
            assignment_start_date=date.today()
        )
        
        plan_assignment = PlanAssignment.from_assignment(
            original_assignment, 
            plan_id=1, 
            priority_order=1
        )
        
        assert plan_assignment.priority_order == 1
        assert plan_assignment.project_priority == 3
        assert plan_assignment.plan_id == 1


class TestPriorityUtilsWithPlans:
    """Tests para utilidades de prioridad con planes"""
    
    def test_apply_plan_priorities_to_projects(self):
        """Test aplicar prioridades de plan a diccionario de proyectos"""
        # Crear proyectos mock
        project1 = Mock(id=10, priority=2, name="Project A")
        project2 = Mock(id=20, priority=1, name="Project B")
        
        projects = {10: project1, 20: project2}
        
        # Prioridades del plan (invertidas)
        plan_priorities = {10: 1, 20: 3}
        
        # Aplicar prioridades
        updated_projects = apply_plan_priorities_to_projects(projects, plan_priorities)
        
        # Verificar que las prioridades se actualizaron
        assert updated_projects[10].priority == 1
        assert updated_projects[20].priority == 3
    
    def test_get_effective_priority_with_plan(self):
        """Test obtener prioridad efectiva considerando plan"""
        project = Mock(id=10, priority=2)
        project.is_active.return_value = True
        
        # Sin prioridades de plan
        priority = get_effective_priority_with_plan(project)
        assert priority == (0, 2)
        
        # Con prioridades de plan
        plan_priorities = {10: 1}
        priority = get_effective_priority_with_plan(project, plan_priorities)
        assert priority == (0, 1)  # Usa prioridad del plan
    
    def test_sort_by_plan_priority(self):
        """Test ordenar por prioridad considerando plan"""
        project1 = Mock(id=10, priority=3, name="Project A")
        project2 = Mock(id=20, priority=1, name="Project B")
        project3 = Mock(id=30, priority=2, name="Project C")
        
        projects = [project1, project2, project3]
        
        # Configurar is_active para todos
        for p in projects:
            p.is_active.return_value = True
        
        # Prioridades del plan
        plan_priorities = {10: 1, 20: 3, 30: 2}
        
        # Ordenar
        sorted_projects = sort_by_plan_priority(projects, plan_priorities)
        
        # Verificar orden correcto (por prioridad del plan)
        assert sorted_projects[0].id == 10  # prioridad 1
        assert sorted_projects[1].id == 30  # prioridad 2
        assert sorted_projects[2].id == 20  # prioridad 3


class TestPlanModel:
    """Tests para el modelo Plan"""
    
    def test_plan_creation(self):
        """Test creación básica de Plan"""
        plan = Plan(
            name="Test Plan",
            description="Plan de prueba",
            simulation_date=date.today(),
            total_assignments=5,
            total_projects=3
        )
        
        assert plan.name == "Test Plan"
        assert plan.description == "Plan de prueba"
        assert plan.total_assignments == 5
        assert plan.total_projects == 3
        assert plan.is_active is False
    
    def test_plan_from_schedule_result(self):
        """Test creación de Plan desde ScheduleResult"""
        assignments = [
            Assignment(
                id=1, project_id=10, project_name="Project A", project_priority=2,
                team_id=1, team_name="Team 1", tier=1, devs_assigned=1.0, max_devs=2.0,
                estimated_hours=20, ready_to_start_date=date.today(),
                assignment_start_date=date.today()
            ),
            Assignment(
                id=2, project_id=20, project_name="Project B", project_priority=1,
                team_id=1, team_name="Team 1", tier=1, devs_assigned=1.0, max_devs=2.0,
                estimated_hours=30, ready_to_start_date=date.today(),
                assignment_start_date=date.today()
            )
        ]
        
        result = ScheduleResult(assignments=assignments, project_summaries=[])
        
        plan = Plan.from_schedule_result(result, "Test Plan", "Descripción")
        
        assert plan.name == "Test Plan"
        assert plan.description == "Descripción"
        assert plan.total_assignments == 2
        assert plan.total_projects == 2
        assert len(plan.checksum) == 64  # SHA-256 hash


class TestPlanAssignmentMethods:
    """Tests para métodos de PlanAssignment"""
    
    def test_get_duration_days(self):
        """Test cálculo de duración en días"""
        assignment = PlanAssignment(
            calculated_start_date=date(2024, 1, 1),
            calculated_end_date=date(2024, 1, 5)
        )
        
        duration = assignment.get_duration_days()
        assert duration == 5  # 1 al 5 inclusive
    
    def test_get_duration_days_same_date(self):
        """Test duración cuando las fechas son iguales"""
        today = date.today()
        assignment = PlanAssignment(
            calculated_start_date=today,
            calculated_end_date=today
        )
        
        duration = assignment.get_duration_days()
        assert duration == 1  # Mismo día = 1 día de duración


if __name__ == "__main__":
    pytest.main([__file__])