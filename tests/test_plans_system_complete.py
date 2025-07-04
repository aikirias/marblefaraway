"""
Tests completos para el sistema de gestión de planes con prioridades persistentes
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch

from app.modules.common.models import Plan, PlanAssignment, ScheduleResult, Assignment, Project
from app.modules.common.plans_crud import (
    save_plan, get_active_plan, activate_plan, deactivate_plan,
    apply_plan_priorities, get_plan_priorities
)
from app.modules.common.priority_utils import (
    apply_plan_priorities_to_projects, get_effective_priority_with_plan,
    sort_by_plan_priority
)
from app.modules.common.projects_crud import (
    apply_priorities_from_active_plan, read_all_projects_with_plan_priorities
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


class TestPlansCRUDWithPriorities:
    """Tests para CRUD de planes con manejo de prioridades"""
    
    @patch('app.modules.common.plans_crud.get_db_connection')
    def test_save_plan_with_priorities(self, mock_db):
        """Test guardar plan con prioridades específicas"""
        # Mock de la conexión a DB
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.fetchone.return_value = {'id': 1, 'created_at': datetime.now()}
        
        # Crear resultado de simulación
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
        
        # Prioridades específicas del plan
        current_priorities = {10: 1, 20: 3}  # Invertir prioridades
        
        # Guardar plan
        plan = save_plan(
            result, 
            name="Test Plan", 
            description="Plan de prueba",
            current_priorities=current_priorities
        )
        
        # Verificar que se llamó a executemany con priority_order
        mock_cursor.executemany.assert_called_once()
        call_args = mock_cursor.executemany.call_args
        
        # Verificar que la query incluye priority_order
        assert "priority_order" in call_args[0][0]
        
        # Verificar que los datos incluyen las prioridades correctas
        data_tuples = call_args[0][1]
        assert len(data_tuples) == 2
        
        # Verificar prioridades específicas
        for data_tuple in data_tuples:
            if data_tuple[2] == 10:  # project_id 10
                assert data_tuple[5] == 1  # priority_order
            elif data_tuple[2] == 20:  # project_id 20
                assert data_tuple[5] == 3  # priority_order
    
    @patch('app.modules.common.plans_crud.get_db_connection')
    def test_apply_plan_priorities(self, mock_db):
        """Test aplicar prioridades de un plan a proyectos"""
        # Mock de la conexión a DB
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock del plan con asignaciones
        plan_assignments = [
            PlanAssignment(
                project_id=10, project_name="Project A", 
                project_priority=2, priority_order=1
            ),
            PlanAssignment(
                project_id=20, project_name="Project B", 
                project_priority=1, priority_order=3
            )
        ]
        
        with patch('app.modules.common.plans_crud.get_plan_by_id') as mock_get_plan:
            mock_plan = Mock()
            mock_plan.assignments = plan_assignments
            mock_get_plan.return_value = mock_plan
            
            # Aplicar prioridades
            result = apply_plan_priorities(1)
            
            assert result is True
            
            # Verificar que se actualizaron las prioridades
            assert mock_cursor.execute.call_count == 2
            
            # Verificar las llamadas de actualización
            calls = mock_cursor.execute.call_args_list
            for call in calls:
                query, params = call[0]
                assert "UPDATE projects SET priority = %s WHERE id = %s AND active = true" in query
                
                # Verificar parámetros correctos
                if params[1] == 10:  # project_id 10
                    assert params[0] == 1  # nueva prioridad
                elif params[1] == 20:  # project_id 20
                    assert params[0] == 3  # nueva prioridad


class TestPriorityUtilsWithPlans:
    """Tests para utilidades de prioridad con planes"""
    
    def test_apply_plan_priorities_to_projects(self):
        """Test aplicar prioridades de plan a diccionario de proyectos"""
        # Crear proyectos mock
        projects = {
            10: Mock(id=10, priority=2, name="Project A"),
            20: Mock(id=20, priority=1, name="Project B")
        }
        
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
        projects = [
            Mock(id=10, priority=3, name="Project A"),
            Mock(id=20, priority=1, name="Project B"),
            Mock(id=30, priority=2, name="Project C")
        ]
        
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


class TestProjectsCRUDIntegration:
    """Tests para integración con projects_crud"""
    
    @patch('app.modules.common.projects_crud.get_active_plan')
    @patch('app.modules.common.projects_crud.apply_plan_priorities')
    def test_apply_priorities_from_active_plan(self, mock_apply, mock_get_active):
        """Test aplicar prioridades desde plan activo"""
        # Mock plan activo
        mock_plan = Mock(id=1)
        mock_get_active.return_value = mock_plan
        mock_apply.return_value = True
        
        result = apply_priorities_from_active_plan()
        
        assert result is True
        mock_apply.assert_called_once_with(1)
    
    @patch('app.modules.common.projects_crud.read_all_projects')
    @patch('app.modules.common.projects_crud.get_active_plan')
    @patch('app.modules.common.projects_crud.get_plan_priorities')
    def test_read_all_projects_with_plan_priorities(self, mock_get_priorities, 
                                                   mock_get_active, mock_read_projects):
        """Test leer proyectos con prioridades de plan"""
        # Mock proyectos
        projects = {
            10: Mock(id=10, priority=2),
            20: Mock(id=20, priority=1)
        }
        mock_read_projects.return_value = projects
        
        # Mock plan activo
        mock_plan = Mock(id=1)
        mock_get_active.return_value = mock_plan
        
        # Mock prioridades del plan
        plan_priorities = {10: 1, 20: 3}
        mock_get_priorities.return_value = plan_priorities
        
        # Leer proyectos
        result = read_all_projects_with_plan_priorities()
        
        # Verificar que se aplicaron las prioridades
        assert result[10].priority == 1
        assert result[20].priority == 3


class TestPlanActivationWorkflow:
    """Tests para el flujo completo de activación de planes"""
    
    @patch('app.modules.common.plans_crud.set_active_plan')
    @patch('app.modules.common.plans_crud.apply_plan_priorities')
    def test_activate_plan_complete_workflow(self, mock_apply_priorities, mock_set_active):
        """Test flujo completo de activación de plan"""
        mock_set_active.return_value = True
        mock_apply_priorities.return_value = True
        
        result = activate_plan(1)
        
        assert result is True
        mock_set_active.assert_called_once_with(1)
        mock_apply_priorities.assert_called_once_with(1)
    
    @patch('app.modules.common.plans_crud.get_db_connection')
    def test_deactivate_plan(self, mock_db):
        """Test desactivar plan"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_db.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 1
        
        result = deactivate_plan(1)
        
        assert result is True
        mock_cursor.execute.assert_called_once_with(
            "UPDATE plans SET is_active = false WHERE id = %s", (1,)
        )


if __name__ == "__main__":
    pytest.main([__file__])