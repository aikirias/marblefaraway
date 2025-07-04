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


def apply_plan_priorities_to_projects(projects: Dict, plan_priorities: Dict[int, int]) -> Dict:
    """
    Aplica prioridades de un plan a un diccionario de proyectos
    
    Args:
        projects: Diccionario de proyectos {id: Project}
        plan_priorities: Diccionario de prioridades del plan {project_id: priority}
    
    Returns:
        Diccionario de proyectos con prioridades actualizadas
    """
    updated_projects = projects.copy()
    
    for project_id, priority in plan_priorities.items():
        if project_id in updated_projects:
            # Crear una copia del proyecto con la nueva prioridad
            project = updated_projects[project_id]
            project.priority = priority
    
    return updated_projects


def get_effective_priority_with_plan(project, plan_priorities: Dict[int, int] = None) -> tuple:
    """
    Calcula prioridad efectiva considerando prioridades de plan activo
    
    Args:
        project: Objeto proyecto
        plan_priorities: Diccionario opcional de prioridades del plan {project_id: priority}
    
    Returns:
        (0, priority) para activos, (1, priority) para pausados
    """
    # Obtener prioridad del plan si está disponible
    priority = project.priority
    if plan_priorities and hasattr(project, 'id') and project.id in plan_priorities:
        priority = plan_priorities[project.id]
    
    if hasattr(project, 'is_active') and callable(project.is_active):
        if project.is_active():
            return (0, priority)  # Activos primero
        else:
            return (1, priority)  # Pausados después
    else:
        # Fallback para objetos que no tienen método is_active
        return (0, priority)


def sort_by_plan_priority(items: List, plan_priorities: Dict[int, int] = None) -> List:
    """
    Ordena items por prioridad considerando prioridades de plan activo
    
    Args:
        items: Lista de items a ordenar
        plan_priorities: Diccionario opcional de prioridades del plan
    
    Returns:
        Lista ordenada por prioridad efectiva
    """
    def key_func(item):
        return get_effective_priority_with_plan(item, plan_priorities)
    
    return sorted(items, key=key_func)