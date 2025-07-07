"""
CRUD básico para Project - Versión refactorizada
Operaciones directas con DB optimizadas
"""

import sqlalchemy as sa
from typing import Dict, Optional
from .db import engine, projects_table
from .models import Project


def create_project(project: Project) -> int:
    """Crear project en DB"""
    with engine.begin() as conn:
        result = conn.execute(
            projects_table.insert().values(
                name=project.name,
                priority=project.priority,
                start_date=project.start_date,
                due_date_wo_qa=project.due_date_wo_qa,
                due_date_with_qa=project.due_date_with_qa,
                active=project.active,
                fecha_inicio_real=project.fecha_inicio_real
            ).returning(projects_table.c.id)
        )
        return result.scalar()


def read_project(project_id: int) -> Optional[Project]:
    """Leer project desde DB"""
    with engine.begin() as conn:
        result = conn.execute(
            sa.select(
                projects_table.c.id,
                projects_table.c.name,
                projects_table.c.priority,
                projects_table.c.start_date,
                projects_table.c.due_date_wo_qa,
                projects_table.c.due_date_with_qa,
                projects_table.c.active,
                projects_table.c.fecha_inicio_real
            ).where(projects_table.c.id == project_id)
        ).first()
        
        if not result:
            return None
        
        return Project(
            id=result.id,
            name=result.name,
            priority=result.priority,
            start_date=result.start_date,
            due_date_wo_qa=result.due_date_wo_qa,
            due_date_with_qa=result.due_date_with_qa,
            active=bool(result.active) if result.active is not None else True,
            fecha_inicio_real=result.fecha_inicio_real
        )


def read_all_projects() -> Dict[int, Project]:
    """Leer todos los projects desde DB con assignments para cálculos dinámicos"""
    with engine.begin() as conn:
        results = conn.execute(
            sa.select(
                projects_table.c.id,
                projects_table.c.name,
                projects_table.c.priority,
                projects_table.c.start_date,
                projects_table.c.due_date_wo_qa,
                projects_table.c.due_date_with_qa,
                projects_table.c.active,
                projects_table.c.fecha_inicio_real
            ).order_by(projects_table.c.priority)
        ).fetchall()
        
        projects = {}
        for row in results:
            project = Project(
                id=row.id,
                name=row.name,
                priority=row.priority,
                start_date=row.start_date,
                due_date_wo_qa=row.due_date_wo_qa,
                due_date_with_qa=row.due_date_with_qa,
                active=bool(row.active) if row.active is not None else True,
                fecha_inicio_real=row.fecha_inicio_real
            )
            
            # Cargar assignments para cálculos dinámicos
            _load_project_assignments(project, conn)
            projects[row.id] = project
        
        return projects


def _load_project_assignments(project: Project, conn):
    """Carga los assignments de un proyecto para cálculos dinámicos"""
    from .db import project_team_assignments_table
    
    assignment_results = conn.execute(
        sa.select(
            project_team_assignments_table.c.estimated_hours,
            project_team_assignments_table.c.custom_estimated_hours,
            project_team_assignments_table.c.devs_assigned
        ).where(project_team_assignments_table.c.project_id == project.id)
    ).fetchall()
    
    # Crear objetos Assignment simplificados para cálculos
    from .models import Assignment
    assignments = []
    for row in assignment_results:
        # Usar custom_estimated_hours si está disponible, sino estimated_hours
        effective_hours = row.custom_estimated_hours if row.custom_estimated_hours else row.estimated_hours
        
        assignment = Assignment(
            id=0,  # No necesario para cálculos
            project_id=project.id,
            project_name=project.name,
            project_priority=project.priority,
            team_id=0,  # No necesario para cálculos
            team_name="",
            tier=1,
            devs_assigned=row.devs_assigned,
            max_devs=row.devs_assigned,
            estimated_hours=effective_hours,
            ready_to_start_date=project.start_date,
            assignment_start_date=project.start_date
        )
        assignments.append(assignment)
    
    project.set_assignments(assignments)


def update_project(project: Project):
    """Actualizar project en DB"""
    with engine.begin() as conn:
        conn.execute(
            projects_table.update()
            .where(projects_table.c.id == project.id)
            .values(
                name=project.name,
                priority=project.priority,
                start_date=project.start_date,
                due_date_wo_qa=project.due_date_wo_qa,
                due_date_with_qa=project.due_date_with_qa,
                active=project.active,
                fecha_inicio_real=project.fecha_inicio_real
            )
        )


def delete_project(project_id: int):
    """Borrar project de DB"""
    with engine.begin() as conn:
        conn.execute(
            projects_table.delete()
            .where(projects_table.c.id == project_id)
        )


def delete_project_by_name(project_name: str) -> bool:
    """Borrar project por nombre, incluyendo sus asignaciones"""
    from .assignments_crud import delete_assignments_by_project
    
    with engine.begin() as conn:
        # Primero buscar el proyecto por nombre
        result = conn.execute(
            sa.select(projects_table.c.id)
            .where(projects_table.c.name == project_name)
        ).first()
        
        if not result:
            return False  # Proyecto no encontrado
        
        project_id = result.id
        
        # Borrar todas las asignaciones del proyecto
        delete_assignments_by_project(project_id)
        
        # Borrar el proyecto
        conn.execute(
            projects_table.delete()
            .where(projects_table.c.id == project_id)
        )
        
        return True


def apply_priorities_from_active_plan():
    """
    Aplica las prioridades del plan activo a los proyectos en la base de datos
    
    Returns:
        True si se aplicaron prioridades, False si no hay plan activo
    """
    from .plans_crud import get_active_plan, apply_plan_priorities
    
    active_plan = get_active_plan()
    if not active_plan:
        return False
    
    return apply_plan_priorities(active_plan.id)


def read_all_projects_with_plan_priorities() -> Dict[int, Project]:
    """
    Lee todos los proyectos considerando las prioridades del plan activo
    
    Returns:
        Diccionario de proyectos con prioridades actualizadas desde el plan activo
    """
    from .plans_crud import get_active_plan, get_plan_priorities
    from .priority_utils import apply_plan_priorities_to_projects
    
    # Obtener proyectos normalmente
    projects = read_all_projects()
    
    # Obtener prioridades del plan activo si existe
    active_plan = get_active_plan()
    if active_plan:
        plan_priorities = get_plan_priorities(active_plan.id)
        if plan_priorities:
            projects = apply_plan_priorities_to_projects(projects, plan_priorities)
    
    return projects


def update_project_priority_from_plan(project_id: int, new_priority: int):
    """
    Actualiza la prioridad de un proyecto específico
    
    Args:
        project_id: ID del proyecto
        new_priority: Nueva prioridad
    """
    with engine.begin() as conn:
        conn.execute(
            projects_table.update()
            .where(projects_table.c.id == project_id)
            .values(priority=new_priority)
        )