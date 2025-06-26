"""
Cargador de datos reales para simulación
Convierte datos de DB a SimulationInput
"""

from .models import SimulationInput
from .teams_crud import read_all_teams
from .projects_crud import read_all_projects
from .assignments_crud import read_all_assignments
from datetime import date


def load_simulation_input_from_db(simulation_start_date: date = None) -> SimulationInput:
    """
    Carga datos reales desde la DB para usar en simulación
    """
    if simulation_start_date is None:
        simulation_start_date = date.today()
    
    # Cargar datos usando CRUDs
    teams = read_all_teams()
    projects = read_all_projects()
    assignments = read_all_assignments()
    
    return SimulationInput(
        teams=teams,
        projects=projects,
        assignments=assignments,
        simulation_start_date=simulation_start_date
    )