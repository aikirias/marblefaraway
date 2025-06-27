"""
CRUD básico para Project
Sin validaciones, operaciones directas con DB
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
                phase="",  # Campo requerido en DB, usar vacío por defecto
                start_date=project.start_date,
                due_date_wo_qa=project.due_date_wo_qa,
                due_date_with_qa=project.due_date_with_qa
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
                projects_table.c.due_date_with_qa
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
            due_date_with_qa=result.due_date_with_qa
        )


def read_all_projects() -> Dict[int, Project]:
    """Leer todos los projects desde DB"""
    with engine.begin() as conn:
        results = conn.execute(
            sa.select(
                projects_table.c.id,
                projects_table.c.name,
                projects_table.c.priority,
                projects_table.c.start_date,
                projects_table.c.due_date_wo_qa,
                projects_table.c.due_date_with_qa
            ).order_by(projects_table.c.priority)
        ).fetchall()
        
        projects = {}
        for row in results:
            projects[row.id] = Project(
                id=row.id,
                name=row.name,
                priority=row.priority,
                start_date=row.start_date,
                due_date_wo_qa=row.due_date_wo_qa,
                due_date_with_qa=row.due_date_with_qa
            )
        
        return projects


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
                due_date_with_qa=project.due_date_with_qa
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