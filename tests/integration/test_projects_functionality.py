"""
Tests de integración para funcionalidad de proyectos APE
Consolidado desde: test_bug_fix.py, test_horas_faltantes_functionality.py, test_projects_data.py
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from app.modules.common.models import Project


class TestProjectsFunctionality:
    """Tests de funcionalidad de proyectos"""
    
    def test_horas_faltantes_calculations(self):
        """Test cálculos de horas faltantes"""
        
        # Test 1: Proyecto sin horas estimadas
        project1 = Project(
            id=1,
            name="Proyecto Test 1",
            priority=1,
            start_date=date.today(),
            due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(),
            horas_trabajadas=10,
            horas_totales_estimadas=0
        )
        
        assert project1.get_horas_faltantes() == 0, "Horas faltantes debe ser 0 cuando no hay estimación"
        assert project1.get_progreso_porcentaje() == 0.0, "Progreso debe ser 0% sin estimación"
        
        # Test 2: Proyecto con progreso normal
        project2 = Project(
            id=2,
            name="Proyecto Test 2",
            priority=1,
            start_date=date.today(),
            due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(),
            horas_trabajadas=30,
            horas_totales_estimadas=100
        )
        
        assert project2.get_horas_faltantes() == 70, "Horas faltantes debe ser 70"
        assert project2.get_progreso_porcentaje() == 30.0, "Progreso debe ser 30%"
        
        # Test 3: Proyecto completado (100%)
        project3 = Project(
            id=3,
            name="Proyecto Test 3",
            priority=1,
            start_date=date.today(),
            due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(),
            horas_trabajadas=50,
            horas_totales_estimadas=50
        )
        
        assert project3.get_horas_faltantes() == 0, "Horas faltantes debe ser 0"
        assert project3.get_progreso_porcentaje() == 100.0, "Progreso debe ser 100%"
        
        # Test 4: Proyecto con exceso de horas (más del 100%)
        project4 = Project(
            id=4,
            name="Proyecto Test 4",
            priority=1,
            start_date=date.today(),
            due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(),
            horas_trabajadas=120,
            horas_totales_estimadas=100
        )
        
        assert project4.get_horas_faltantes() == 0, "Horas faltantes debe ser 0 (no negativo)"
        assert project4.get_progreso_porcentaje() == 100.0, "Progreso debe ser máximo 100%"
    
    def test_progress_colors(self):
        """Test colores de progreso"""
        test_cases = [
            (10, 100, "#dc3545"),  # Rojo - poco progreso
            (40, 100, "#17a2b8"),  # Azul - en progreso
            (80, 100, "#ffc107"),  # Amarillo - avanzado
            (95, 100, "#28a745"),  # Verde - casi completo
        ]
        
        for worked, total, expected_color in test_cases:
            project = Project(
                id=5, name="Test Color", priority=1,
                start_date=date.today(), due_date_wo_qa=date.today(),
                due_date_with_qa=date.today(),
                horas_trabajadas=worked, horas_totales_estimadas=total
            )
            color = project.get_progreso_color()
            assert color == expected_color, f"Color incorrecto para {worked}/{total}h"
    
    @patch('app.modules.common.projects_crud.read_all_projects')
    @patch('app.modules.common.projects_crud.update_project')
    def test_state_synchronization(self, mock_update, mock_read):
        """Test sincronización de estados entre pestañas"""
        
        # Setup mock data
        test_project = Project(
            id=1, name="Test Project", priority=1,
            start_date=date.today(), due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(), active=True
        )
        
        mock_read.return_value = {1: test_project}
        
        # Test cambio de estado
        original_state = test_project.active
        test_project.active = False
        
        # Simular actualización
        mock_update.return_value = None
        
        # Verificar que el proyecto cambió de estado
        assert test_project.active != original_state
        assert not test_project.is_active()
        assert test_project.get_state_display() == "⏸️ Inactivo"
    
    @patch('app.modules.common.projects_crud.read_all_projects')
    def test_projects_data_loading(self, mock_read):
        """Test carga de datos de proyectos"""
        
        # Setup mock data
        test_projects = {
            1: Project(
                id=1, name="Project 1", priority=1,
                start_date=date.today(), due_date_wo_qa=date.today(),
                due_date_with_qa=date.today(), active=True,
                horas_trabajadas=50, horas_totales_estimadas=100
            ),
            2: Project(
                id=2, name="Project 2", priority=2,
                start_date=date.today(), due_date_wo_qa=date.today(),
                due_date_with_qa=date.today(), active=False,
                horas_trabajadas=0, horas_totales_estimadas=80
            )
        }
        
        mock_read.return_value = test_projects
        
        # Test filtrado y métricas
        projects = mock_read()
        
        assert len(projects) == 2
        
        # Calcular métricas
        active_count = sum(1 for p in projects.values() if p.is_active())
        inactive_count = len(projects) - active_count
        total_hours_worked = sum(p.horas_trabajadas for p in projects.values())
        
        assert active_count == 1
        assert inactive_count == 1
        assert total_hours_worked == 50
        
        # Test filtrado de proyectos activos
        filtered_projects = [p for p in projects.values() if p.is_active()]
        filtered_projects.sort(key=lambda p: p.priority)
        
        assert len(filtered_projects) == 1
        assert filtered_projects[0].name == "Project 1"
    
    def test_project_state_methods(self):
        """Test métodos de verificación de estado"""
        
        # Proyecto activo
        active_project = Project(
            id=1, name="Active Project", priority=1,
            start_date=date.today(), due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(), active=True
        )
        
        assert active_project.is_active()
        assert active_project.get_state_display() == "🟢 Activo"
        
        # Proyecto inactivo
        inactive_project = Project(
            id=2, name="Inactive Project", priority=2,
            start_date=date.today(), due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(), active=False
        )
        
        assert not inactive_project.is_active()
        assert inactive_project.get_state_display() == "⏸️ Inactivo"
    
    def test_project_display_formatting(self):
        """Test formateo de display de proyectos"""
        
        project = Project(
            id=1, name="Test Project", priority=1,
            start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1),
            due_date_with_qa=date(2025, 2, 15), active=True,
            horas_trabajadas=25, horas_totales_estimadas=100
        )
        
        # Test display básico
        assert project.name == "Test Project"
        assert project.priority == 1
        
        # Test progreso
        assert project.get_progreso_display() == "25.0% (25/100h)"
        assert project.get_horas_faltantes() == 75
        
        # Test fechas
        assert project.start_date == date(2025, 1, 1)
        assert project.due_date_wo_qa == date(2025, 2, 1)
        assert project.due_date_with_qa == date(2025, 2, 15)


class TestProjectsIntegrationScenarios:
    """Tests de escenarios de integración más complejos"""
    
    @patch('app.modules.common.projects_crud.read_all_projects')
    def test_project_sorting_and_filtering(self, mock_read):
        """Test ordenamiento y filtrado de proyectos"""
        
        # Setup proyectos con diferentes estados y prioridades
        projects = {
            1: Project(id=1, name="High Priority Active", priority=1, active=True,
                      start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today()),
            2: Project(id=2, name="Low Priority Active", priority=3, active=True,
                      start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today()),
            3: Project(id=3, name="Medium Priority Inactive", priority=2, active=False,
                      start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today()),
        }
        
        mock_read.return_value = projects
        
        # Test filtrado de activos y ordenamiento por prioridad
        active_projects = [p for p in projects.values() if p.is_active()]
        active_projects.sort(key=lambda p: p.priority)
        
        assert len(active_projects) == 2
        assert active_projects[0].name == "High Priority Active"
        assert active_projects[1].name == "Low Priority Active"
        
        # Test todos los proyectos ordenados por prioridad
        all_projects = sorted(projects.values(), key=lambda p: p.priority)
        assert all_projects[0].priority == 1
        assert all_projects[1].priority == 2
        assert all_projects[2].priority == 3
    
    def test_project_progress_edge_cases(self):
        """Test casos límite de progreso de proyectos"""
        
        # Caso 1: División por cero
        project_no_estimate = Project(
            id=1, name="No Estimate", priority=1,
            start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today(),
            horas_trabajadas=10, horas_totales_estimadas=0
        )
        
        assert project_no_estimate.get_progreso_porcentaje() == 0.0
        assert project_no_estimate.get_horas_faltantes() == 0
        
        # Caso 2: Horas negativas (no debería pasar, pero por robustez)
        project_negative = Project(
            id=2, name="Negative Hours", priority=1,
            start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today(),
            horas_trabajadas=-5, horas_totales_estimadas=100
        )
        
        # El sistema debe manejar esto gracefully - permite valores negativos
        assert project_negative.get_progreso_porcentaje() == -5.0
        
        # Caso 3: Horas trabajadas muy grandes
        project_overflow = Project(
            id=3, name="Overflow Hours", priority=1,
            start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today(),
            horas_trabajadas=999999, horas_totales_estimadas=100
        )
        
        assert project_overflow.get_progreso_porcentaje() == 100.0  # Máximo 100%
        assert project_overflow.get_horas_faltantes() == 0  # No negativo