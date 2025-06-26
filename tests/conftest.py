"""
Configuración pytest y fixtures para el sistema APE
"""

import os
import sys
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock

# Configurar variable de entorno para testing antes de importar modelos
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

# Mock completo del módulo db para evitar problemas de reflection
mock_db = MagicMock()
mock_db.engine = MagicMock()
mock_db.projects_table = MagicMock()
mock_db.teams_table = MagicMock()
mock_db.project_team_assignments_table = MagicMock()
mock_db.tier_capacity_table = MagicMock()
sys.modules['app.modules.common.db'] = mock_db

from app.modules.common.models import Team, Project, Assignment, SimulationInput


@pytest.fixture
def mock_db_engine():
    """Mock del engine de SQLAlchemy"""
    return MagicMock()


@pytest.fixture
def sample_team():
    """Team de ejemplo para tests"""
    return Team(
        id=1,
        name="Devs",
        total_devs=5,
        busy_devs=1,
        tier_capacities={1: 16, 2: 40, 3: 80, 4: 120}
    )


@pytest.fixture
def sample_project():
    """Project de ejemplo para tests"""
    return Project(
        id=1,
        name="Test Project",
        priority=1,
        start_date=date(2025, 1, 1),
        due_date_wo_qa=date(2025, 2, 1),
        due_date_with_qa=date(2025, 2, 15)
    )


@pytest.fixture
def sample_assignment(sample_team, sample_project):
    """Assignment de ejemplo para tests"""
    return Assignment(
        id=1,
        project_id=sample_project.id,
        project_name=sample_project.name,
        project_priority=sample_project.priority,
        team_id=sample_team.id,
        team_name=sample_team.name,
        tier=3,
        devs_assigned=2.0,
        max_devs=3.0,
        estimated_hours=80,
        ready_to_start_date=date(2025, 1, 1),
        assignment_start_date=date(2025, 1, 1)
    )


@pytest.fixture
def ape_teams():
    """Equipos especializados según arquitectura APE"""
    return {
        1: Team(id=1, name="Arch", total_devs=2, tier_capacities={1: 16, 2: 32, 3: 72, 4: 240}),
        2: Team(id=2, name="Model", total_devs=4, tier_capacities={1: 40, 2: 80, 3: 120, 4: 160}),
        3: Team(id=3, name="Devs", total_devs=6, tier_capacities={1: 16, 2: 40, 3: 80, 4: 120}),
        4: Team(id=4, name="Dqa", total_devs=3, tier_capacities={1: 8, 2: 24, 3: 40})  # Sin Tier 4
    }


@pytest.fixture
def sample_simulation_input(ape_teams, sample_project):
    """SimulationInput completo para tests de simulación"""
    projects = {sample_project.id: sample_project}
    
    # Asignaciones típicas APE: Arch → Model → Devs → Dqa
    assignments = [
        Assignment(id=1, project_id=1, project_name="Test Project", project_priority=1,
                  team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=2.0,
                  estimated_hours=16, ready_to_start_date=date(2025, 1, 1),
                  assignment_start_date=date(2025, 1, 1)),
        Assignment(id=2, project_id=1, project_name="Test Project", project_priority=1,
                  team_id=2, team_name="Model", tier=2, devs_assigned=1.0, max_devs=4.0,
                  estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                  assignment_start_date=date(2025, 1, 1)),
        Assignment(id=3, project_id=1, project_name="Test Project", project_priority=1,
                  team_id=3, team_name="Devs", tier=3, devs_assigned=2.0, max_devs=6.0,
                  estimated_hours=160, ready_to_start_date=date(2025, 1, 1),
                  assignment_start_date=date(2025, 1, 1)),
        Assignment(id=4, project_id=1, project_name="Test Project", project_priority=1,
                  team_id=4, team_name="Dqa", tier=2, devs_assigned=1.0, max_devs=3.0,
                  estimated_hours=24, ready_to_start_date=date(2025, 1, 1),
                  assignment_start_date=date(2025, 1, 1))
    ]
    
    return SimulationInput(
        teams=ape_teams,
        projects=projects,
        assignments=assignments,
        simulation_start_date=date(2025, 1, 1)
    )


@pytest.fixture
def mock_connection():
    """Mock de conexión a DB para tests de integración"""
    conn = MagicMock()
    return conn