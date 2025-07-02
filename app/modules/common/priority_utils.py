"""
Utilidades de prioridad efectiva para APE
Elimina duplicación en projects.py y gantt_views.py
"""
from typing import List, Dict, Any, Callable, Optional


def get_effective_priority(project) -> tuple:
    """
    Calcula prioridad efectiva: activos primero, luego pausados
    Returns: (0, priority) para activos, (1, priority) para pausados
    """
    if hasattr(project, 'is_active') and callable(project.is_active):
        if project.is_active():
            return (0, project.priority)  # Activos primero
        else:
            return (1, project.priority)  # Pausados después
    else:
        # Fallback para objetos que no tienen método is_active
        # Asume que son activos si no se especifica lo contrario
        return (0, getattr(project, 'priority', 0))


def sort_by_effective_priority(items: List, key_func: Optional[Callable] = None) -> List:
    """Ordena items por prioridad efectiva"""
    if key_func is None:
        key_func = get_effective_priority
    
    return sorted(items, key=key_func)


def filter_projects_by_status(projects: Dict, status: str) -> List:
    """
    Filtra proyectos por estado
    Args:
        projects: Diccionario de proyectos
        status: "Todos", "Solo Activos", "Solo Inactivos"
    Returns:
        Lista de proyectos filtrados
    """
    all_projects = list(projects.values())
    
    if status == "Solo Activos":
        return [p for p in all_projects if hasattr(p, 'is_active') and p.is_active()]
    elif status == "Solo Inactivos":
        return [p for p in all_projects if hasattr(p, 'is_active') and not p.is_active()]
    else:  # "Todos"
        return all_projects


def get_effective_priority_for_dataframe(row) -> tuple:
    """
    Versión para usar con pandas DataFrame.apply()
    Espera que el row tenga columnas 'Active' y 'Priority'
    """
    if row.get('Active', True):  # Default a True si no existe la columna
        return (0, row.get('Priority', 0))
    else:
        return (1, row.get('Priority', 0))