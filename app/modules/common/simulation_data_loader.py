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
    Incluye TODOS los proyectos (activos y pausados) con prioridad efectiva
    """
    if simulation_start_date is None:
        simulation_start_date = date.today()
    
    # Cargar datos usando CRUDs
    teams = read_all_teams()
    all_projects = read_all_projects()
    all_assignments = read_all_assignments()
    
    # Incluir TODOS los proyectos (activos y pausados)
    # La prioridad efectiva se maneja en el scheduler
    
    return SimulationInput(
        teams=teams,
        projects=all_projects,
        assignments=all_assignments,
        simulation_start_date=simulation_start_date
    )