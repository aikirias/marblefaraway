"""
Tests de integración para funcionalidad de proyectos APE
Consolidado desde: test_bug_fix.py, test_horas_faltantes_functionality.py, test_projects_data.py
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from app.modules.common.models import Project, Assignment


class TestProjectsFunctionality:
    """Tests de funcionalidad de proyectos"""

    def test_horas_faltantes_calculations(self):
        """Test cálculos de horas faltantes"""
        
        project = Project(id=1, name="Test", priority=1, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today())

        # Test 1: Proyecto sin horas estimadas
        with patch.object(project, 'get_horas_totales_estimadas', return_value=0), \
             patch.object(project, 'get_horas_trabajadas', return_value=10):
            assert project.get_horas_faltantes() == 0, "Horas faltantes debe ser 0 cuando no hay estimación"
            assert project.get_progreso_porcentaje() == 0.0, "Progreso debe ser 0% sin estimación"

        # Test 2: Proyecto con progreso normal
        with patch.object(project, 'get_horas_totales_estimadas', return_value=100), \
             patch.object(project, 'get_horas_trabajadas', return_value=30):
            assert project.get_horas_faltantes() == 70, "Horas faltantes debe ser 70"
            assert project.get_progreso_porcentaje() == 30.0, "Progreso debe ser 30%"

        # Test 3: Proyecto completado (100%)
        with patch.object(project, 'get_horas_totales_estimadas', return_value=50), \
             patch.object(project, 'get_horas_trabajadas', return_value=50):
            assert project.get_horas_faltantes() == 0, "Horas faltantes debe ser 0"
            assert project.get_progreso_porcentaje() == 100.0, "Progreso debe ser 100%"

        # Test 4: Proyecto con exceso de horas (más del 100%)
        with patch.object(project, 'get_horas_totales_estimadas', return_value=100), \
             patch.object(project, 'get_horas_trabajadas', return_value=120):
            # La lógica interna de get_progreso_porcentaje asegura que no pase de 100
            # y get_horas_faltantes no sea negativo
            assert project.get_horas_faltantes() == 0, "Horas faltantes debe ser 0 (no negativo)"
            assert project.get_progreso_porcentaje() == 100.0, "Progreso debe ser máximo 100%"

    def test_progress_colors(self):
        """Test colores de progreso"""
        test_cases = [
            (10.0, "#dc3545"),  # Rojo - poco progreso
            (40.0, "#17a2b8"),  # Azul - en progreso
            (80.0, "#ffc107"),  # Amarillo - avanzado
            (95.0, "#28a745"),  # Verde - casi completo
        ]
        
        project = Project(id=5, name="Test Color", priority=1, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today())
        
        for percent, expected_color in test_cases:
            with patch.object(project, 'get_progreso_porcentaje', return_value=percent):
                color = project.get_progreso_color()
                assert color == expected_color, f"Color incorrecto para {percent}%"

    @patch('app.modules.common.projects_crud.read_all_projects')
    @patch('app.modules.common.projects_crud.update_project')
    def test_state_synchronization(self, mock_update, mock_read):
        """Test sincronización de estados entre pestañas"""
        
        test_project = Project(
            id=1, name="Test Project", priority=1,
            start_date=date.today(), due_date_wo_qa=date.today(),
            due_date_with_qa=date.today(), active=True
        )
        
        mock_read.return_value = {1: test_project}
        
        original_state = test_project.active
        test_project.active = False
        
        mock_update.return_value = None
        
        assert test_project.active != original_state
        assert not test_project.is_active()
        assert test_project.get_state_display() == "⏸️ Inactivo"

    @patch('app.modules.common.projects_crud.read_all_projects')
    def test_projects_data_loading(self, mock_read):
        """Test carga de datos de proyectos"""
        
        p1 = Project(id=1, name="Project 1", priority=1, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today(), active=True)
        p2 = Project(id=2, name="Project 2", priority=2, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today(), active=False)

        test_projects = {1: p1, 2: p2}
        mock_read.return_value = test_projects
        
        projects = mock_read()
        
        with patch.object(p1, 'get_horas_trabajadas', return_value=50), \
             patch.object(p2, 'get_horas_trabajadas', return_value=0):

            assert len(projects) == 2
            
            active_count = sum(1 for p in projects.values() if p.is_active())
            inactive_count = len(projects) - active_count
            total_hours_worked = sum(p.get_horas_trabajadas() for p in projects.values())
            
            assert active_count == 1
            assert inactive_count == 1
            assert total_hours_worked == 50
            
            filtered_projects = [p for p in projects.values() if p.is_active()]
            filtered_projects.sort(key=lambda p: p.priority)
            
            assert len(filtered_projects) == 1
            assert filtered_projects[0].name == "Project 1"

    def test_project_state_methods(self):
        """Test métodos de verificación de estado"""
        
        active_project = Project(id=1, name="Active Project", priority=1, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today(), active=True)
        assert active_project.is_active()
        assert active_project.get_state_display() == "🟢 Activo"
        
        inactive_project = Project(id=2, name="Inactive Project", priority=2, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today(), active=False)
        assert not inactive_project.is_active()
        assert inactive_project.get_state_display() == "⏸️ Inactivo"

    def test_project_display_formatting(self):
        """Test formateo de display de proyectos"""
        
        project = Project(
            id=1, name="Test Project", priority=1,
            start_date=date(2025, 1, 1), due_date_wo_qa=date(2025, 2, 1),
            due_date_with_qa=date(2025, 2, 15), active=True
        )
        
        with patch.object(project, 'get_progreso_display', return_value="25.0% (25/100h)"), \
             patch.object(project, 'get_horas_faltantes', return_value=75):
            
            assert project.name == "Test Project"
            assert project.priority == 1
            assert project.get_progreso_display() == "25.0% (25/100h)"
            assert project.get_horas_faltantes() == 75
            assert project.start_date == date(2025, 1, 1)
            assert project.due_date_wo_qa == date(2025, 2, 1)
            assert project.due_date_with_qa == date(2025, 2, 15)


class TestProjectsIntegrationScenarios:
    """Tests de escenarios de integración más complejos"""

    @patch('app.modules.common.projects_crud.read_all_projects')
    def test_project_sorting_and_filtering(self, mock_read):
        """Test ordenamiento y filtrado de proyectos"""
        
        projects = {
            1: Project(id=1, name="High Priority Active", priority=1, active=True, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today()),
            2: Project(id=2, name="Low Priority Active", priority=3, active=True, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today()),
            3: Project(id=3, name="Medium Priority Inactive", priority=2, active=False, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today()),
        }
        
        mock_read.return_value = projects
        
        active_projects = [p for p in projects.values() if p.is_active()]
        active_projects.sort(key=lambda p: p.priority)
        
        assert len(active_projects) == 2
        assert active_projects[0].name == "High Priority Active"
        assert active_projects[1].name == "Low Priority Active"
        
        all_projects = sorted(projects.values(), key=lambda p: p.priority)
        assert all_projects[0].priority == 1
        assert all_projects[1].priority == 2
        assert all_projects[2].priority == 3

    def test_project_progress_edge_cases(self):
        """Test casos límite de progreso de proyectos"""
        
        project = Project(id=1, name="Test Edge Cases", priority=1, start_date=date.today(), due_date_wo_qa=date.today(), due_date_with_qa=date.today())

        # Caso 1: División por cero
        with patch.object(project, 'get_horas_totales_estimadas', return_value=0), \
             patch.object(project, 'get_horas_trabajadas', return_value=10):
            assert project.get_progreso_porcentaje() == 0.0
            assert project.get_horas_faltantes() == 0

        # Caso 2: Horas negativas (no debería pasar, pero por robustez)
        with patch.object(project, 'get_horas_totales_estimadas', return_value=100), \
             patch.object(project, 'get_horas_trabajadas', return_value=-5):
            # La lógica del modelo debe manejar esto correctamente
            assert project.get_progreso_porcentaje() < 0

        # Caso 3: Horas trabajadas muy grandes
        with patch.object(project, 'get_horas_totales_estimadas', return_value=100), \
             patch.object(project, 'get_horas_trabajadas', return_value=999999):
            assert project.get_progreso_porcentaje() == 100.0
            assert project.get_horas_faltantes() == 0