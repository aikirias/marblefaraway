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
    Filtra solo proyectos activos para la simulación
    """
    if simulation_start_date is None:
        simulation_start_date = date.today()
    
    # Cargar datos usando CRUDs
    teams = read_all_teams()
    all_projects = read_all_projects()
    all_assignments = read_all_assignments()
    
    # Filtrar solo proyectos activos
    active_projects = {pid: project for pid, project in all_projects.items() if project.is_active()}
    active_project_ids = set(active_projects.keys())
    
    # Filtrar asignaciones solo de proyectos activos
    active_assignments = [a for a in all_assignments if a.project_id in active_project_ids]
    
    return SimulationInput(
        teams=teams,
        projects=active_projects,
        assignments=active_assignments,
        simulation_start_date=simulation_start_date
    )