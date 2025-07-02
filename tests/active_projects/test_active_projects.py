"""
Tests para el módulo de proyectos activos
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from app.modules.active_projects.active_projects import (
    _identify_active_projects,
    _calculate_project_data,
    _calculate_hours_worked,
    _calculate_phase_states
)
from app.modules.common.models import Project, Assignment, Team, ScheduleResult


class TestActiveProjects:
    """Tests para funcionalidad de proyectos activos"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.today = date.today()
        
        # Crear equipos de prueba
        self.teams = {
            1: Team(id=1, name="Arch", total_devs=2, tier_capacities={1: 40, 2: 80}),
            2: Team(id=2, name="Devs", total_devs=4, tier_capacities={1: 20, 2: 40}),
            3: Team(id=3, name="Model", total_devs=2, tier_capacities={1: 30, 2: 60}),
            4: Team(id=4, name="Dqa", total_devs=2, tier_capacities={1: 16, 2: 32})
        }
        
        # Crear proyectos de prueba
        self.projects = {
            1: Project(
                id=1,
                name="Proyecto Activo 1",
                priority=1,
                start_date=self.today - timedelta(days=10),
                due_date_wo_qa=self.today + timedelta(days=20),
                due_date_with_qa=self.today + timedelta(days=25),
                active=True,
                fecha_inicio_real=self.today - timedelta(days=5)
            ),
            2: Project(
                id=2,
                name="Proyecto Futuro",
                priority=2,
                start_date=self.today + timedelta(days=5),
                due_date_wo_qa=self.today + timedelta(days=30),
                due_date_with_qa=self.today + timedelta(days=35),
                active=True,
                fecha_inicio_real=self.today + timedelta(days=5)
            )
        }
    
    def test_identify_active_projects_with_active_assignment(self):
        """Test identificación de proyectos con asignaciones activas"""
        # Crear asignaciones - una activa hoy, otra futura
        assignments = [
            Assignment(
                id=1,
                project_id=1,
                project_name="Proyecto Activo 1",
                project_priority=1,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,
                ready_to_start_date=self.today - timedelta(days=5),
                assignment_start_date=self.today - timedelta(days=5),
                calculated_start_date=self.today - timedelta(days=2),
                calculated_end_date=self.today + timedelta(days=3),
                pending_hours=40
            ),
            Assignment(
                id=2,
                project_id=2,
                project_name="Proyecto Futuro",
                project_priority=2,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,
                ready_to_start_date=self.today + timedelta(days=5),
                assignment_start_date=self.today + timedelta(days=5),
                calculated_start_date=self.today + timedelta(days=5),
                calculated_end_date=self.today + timedelta(days=10),
                pending_hours=40
            )
        ]
        
        result = ScheduleResult(assignments=assignments, project_summaries=[])
        
        active_projects = _identify_active_projects(
            result, self.projects, self.teams, self.today
        )
        
        # Solo debe identificar el proyecto 1 como activo
        assert len(active_projects) == 1
        assert active_projects[0]['project_id'] == 1
        assert active_projects[0]['project_name'] == "Proyecto Activo 1"
        assert len(active_projects[0]['active_teams']) == 1
        assert "Arch" in active_projects[0]['active_teams']
    
    def test_identify_active_projects_no_active_assignments(self):
        """Test cuando no hay asignaciones activas"""
        # Crear asignaciones futuras
        assignments = [
            Assignment(
                id=1,
                project_id=2,
                project_name="Proyecto Futuro",
                project_priority=2,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,
                ready_to_start_date=self.today + timedelta(days=5),
                assignment_start_date=self.today + timedelta(days=5),
                calculated_start_date=self.today + timedelta(days=5),
                calculated_end_date=self.today + timedelta(days=10),
                pending_hours=40
            )
        ]
        
        result = ScheduleResult(assignments=assignments, project_summaries=[])
        
        active_projects = _identify_active_projects(
            result, self.projects, self.teams, self.today
        )
        
        # No debe haber proyectos activos
        assert len(active_projects) == 0
    
    def test_calculate_hours_worked_with_fecha_inicio_real(self):
        """Test cálculo de horas trabajadas desde fecha_inicio_real"""
        project = self.projects[1]  # Proyecto con fecha_inicio_real hace 5 días
        
        # Crear asignación que ya empezó
        assignments = [
            Assignment(
                id=1,
                project_id=1,
                project_name="Proyecto Activo 1",
                project_priority=1,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,
                ready_to_start_date=self.today - timedelta(days=5),
                assignment_start_date=self.today - timedelta(days=5),
                calculated_start_date=self.today - timedelta(days=3),
                calculated_end_date=self.today + timedelta(days=2),
                pending_hours=40
            )
        ]
        
        hours_worked = _calculate_hours_worked(project, assignments, self.today)
        
        # Debe haber calculado algunas horas trabajadas
        assert hours_worked > 0
        assert hours_worked <= 40  # No puede ser más que el total estimado
    
    def test_calculate_hours_worked_no_fecha_inicio_real(self):
        """Test cálculo de horas trabajadas sin fecha_inicio_real"""
        project = Project(
            id=3,
            name="Proyecto Sin Fecha",
            priority=3,
            start_date=self.today,
            due_date_wo_qa=self.today + timedelta(days=20),
            due_date_with_qa=self.today + timedelta(days=25),
            active=True,
            fecha_inicio_real=None
        )
        
        assignments = [
            Assignment(
                id=1,
                project_id=3,
                project_name="Proyecto Sin Fecha",
                project_priority=3,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,
                ready_to_start_date=self.today,
                assignment_start_date=self.today,
                calculated_start_date=self.today,
                calculated_end_date=self.today + timedelta(days=5),
                pending_hours=40
            )
        ]
        
        hours_worked = _calculate_hours_worked(project, assignments, self.today)
        
        # Sin fecha_inicio_real, debe retornar 0
        assert hours_worked == 0
    
    def test_calculate_phase_states(self):
        """Test cálculo de estados de fases"""
        assignments = [
            # Fase completada
            Assignment(
                id=1,
                project_id=1,
                project_name="Proyecto Test",
                project_priority=1,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,
                ready_to_start_date=self.today - timedelta(days=10),
                assignment_start_date=self.today - timedelta(days=10),
                calculated_start_date=self.today - timedelta(days=8),
                calculated_end_date=self.today - timedelta(days=3),
                pending_hours=40
            ),
            # Fase en progreso
            Assignment(
                id=2,
                project_id=1,
                project_name="Proyecto Test",
                project_priority=1,
                team_id=2,
                team_name="Devs",
                tier=1,
                devs_assigned=2.0,
                max_devs=4.0,
                estimated_hours=80,
                ready_to_start_date=self.today - timedelta(days=3),
                assignment_start_date=self.today - timedelta(days=3),
                calculated_start_date=self.today - timedelta(days=2),
                calculated_end_date=self.today + timedelta(days=5),
                pending_hours=80
            ),
            # Fase pendiente
            Assignment(
                id=3,
                project_id=1,
                project_name="Proyecto Test",
                project_priority=1,
                team_id=4,
                team_name="Dqa",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=32,
                ready_to_start_date=self.today + timedelta(days=5),
                assignment_start_date=self.today + timedelta(days=5),
                calculated_start_date=self.today + timedelta(days=6),
                calculated_end_date=self.today + timedelta(days=10),
                pending_hours=32
            )
        ]
        
        phase_states = _calculate_phase_states(assignments, self.teams, self.today)
        
        assert "✅ Completada" in phase_states["Arch"]
        assert "🔄 En Progreso" in phase_states["Devs"]
        assert "⏳ Pendiente" in phase_states["Dqa"]
    
    def test_calculate_project_data_complete(self):
        """Test cálculo completo de datos de proyecto"""
        project = self.projects[1]
        
        assignments = [
            Assignment(
                id=1,
                project_id=1,
                project_name="Proyecto Activo 1",
                project_priority=1,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,
                ready_to_start_date=self.today - timedelta(days=5),
                assignment_start_date=self.today - timedelta(days=5),
                calculated_start_date=self.today - timedelta(days=2),
                calculated_end_date=self.today + timedelta(days=3),
                pending_hours=40
            ),
            Assignment(
                id=2,
                project_id=1,
                project_name="Proyecto Activo 1",
                project_priority=1,
                team_id=2,
                team_name="Devs",
                tier=1,
                devs_assigned=2.0,
                max_devs=4.0,
                estimated_hours=80,
                ready_to_start_date=self.today + timedelta(days=3),
                assignment_start_date=self.today + timedelta(days=3),
                calculated_start_date=self.today + timedelta(days=4),
                calculated_end_date=self.today + timedelta(days=8),
                pending_hours=80
            )
        ]
        
        active_assignments = [assignments[0]]  # Solo la primera está activa
        
        project_data = _calculate_project_data(
            project, assignments, active_assignments, self.teams, self.today
        )
        
        assert project_data['project_id'] == 1
        assert project_data['project_name'] == "Proyecto Activo 1"
        assert project_data['priority'] == 1
        assert project_data['total_estimated_hours'] == 80  # 40 (Arch) + 40 (Devs calculado)
        assert len(project_data['phase_hours']) == 2
        assert "Arch" in project_data['phase_hours']
        assert "Devs" in project_data['phase_hours']
        assert project_data['phase_hours']['Arch'] == 40
        assert project_data['phase_hours']['Devs'] == 40  # get_hours_needed() usa tier_capacity * devs_assigned
        assert len(project_data['active_teams']) == 1
        assert "Arch" in project_data['active_teams']
        assert project_data['active_assignments_count'] == 1
    
    def test_calculate_project_data_with_custom_hours(self):
        """Test cálculo de datos de proyecto con custom_estimated_hours (overrides)"""
        project = self.projects[1]
        
        assignments = [
            Assignment(
                id=1,
                project_id=1,
                project_name="Proyecto Activo 1",
                project_priority=1,
                team_id=1,
                team_name="Arch",
                tier=1,
                devs_assigned=1.0,
                max_devs=2.0,
                estimated_hours=40,  # Valor original
                custom_estimated_hours=240,  # Override personalizado
                ready_to_start_date=self.today - timedelta(days=5),
                assignment_start_date=self.today - timedelta(days=5),
                calculated_start_date=self.today - timedelta(days=2),
                calculated_end_date=self.today + timedelta(days=3),
                pending_hours=240
            ),
            Assignment(
                id=2,
                project_id=1,
                project_name="Proyecto Activo 1",
                project_priority=1,
                team_id=2,
                team_name="Devs",
                tier=1,
                devs_assigned=2.0,
                max_devs=4.0,
                estimated_hours=80,  # Sin override, debe usar tier
                custom_estimated_hours=None,
                ready_to_start_date=self.today + timedelta(days=3),
                assignment_start_date=self.today + timedelta(days=3),
                calculated_start_date=self.today + timedelta(days=4),
                calculated_end_date=self.today + timedelta(days=8),
                pending_hours=40
            )
        ]
        
        active_assignments = [assignments[0]]  # Solo la primera está activa
        
        project_data = _calculate_project_data(
            project, assignments, active_assignments, self.teams, self.today
        )
        
        # Verificar que se usen los overrides correctamente
        assert project_data['project_id'] == 1
        assert project_data['project_name'] == "Proyecto Activo 1"
        assert project_data['priority'] == 1
        assert project_data['total_estimated_hours'] == 280  # 240 (Arch custom) + 40 (Devs tier)
        assert len(project_data['phase_hours']) == 2
        assert "Arch" in project_data['phase_hours']
        assert "Devs" in project_data['phase_hours']
        assert project_data['phase_hours']['Arch'] == 240  # Debe usar custom_estimated_hours
        assert project_data['phase_hours']['Devs'] == 40   # Debe usar tier_capacity * devs_assigned
        assert len(project_data['active_teams']) == 1
        assert "Arch" in project_data['active_teams']
        assert project_data['active_assignments_count'] == 1


if __name__ == "__main__":
    pytest.main([__file__])