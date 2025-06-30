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
                phase=project.phase,  # Mantenido para compatibilidad
                start_date=project.start_date,
                due_date_wo_qa=project.due_date_wo_qa,
                due_date_with_qa=project.due_date_with_qa,
                active=project.active,
                horas_trabajadas=project.horas_trabajadas,
                horas_totales_estimadas=project.horas_totales_estimadas,
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
                projects_table.c.phase,
                projects_table.c.start_date,
                projects_table.c.due_date_wo_qa,
                projects_table.c.due_date_with_qa,
                projects_table.c.active,
                projects_table.c.horas_trabajadas,
                projects_table.c.horas_totales_estimadas,
                projects_table.c.fecha_inicio_real
            ).where(projects_table.c.id == project_id)
        ).first()
        
        if not result:
            return None
        
        return Project(
            id=result.id,
            name=result.name,
            priority=result.priority,
            phase=result.phase or "draft",  # Mantenido para compatibilidad
            start_date=result.start_date,
            due_date_wo_qa=result.due_date_wo_qa,
            due_date_with_qa=result.due_date_with_qa,
            active=result.active if result.active is not None else True,
            horas_trabajadas=result.horas_trabajadas or 0,
            horas_totales_estimadas=result.horas_totales_estimadas or 0,
            fecha_inicio_real=result.fecha_inicio_real
        )


def read_all_projects() -> Dict[int, Project]:
    """Leer todos los projects desde DB"""
    with engine.begin() as conn:
        results = conn.execute(
            sa.select(
                projects_table.c.id,
                projects_table.c.name,
                projects_table.c.priority,
                projects_table.c.phase,
                projects_table.c.start_date,
                projects_table.c.due_date_wo_qa,
                projects_table.c.due_date_with_qa,
                projects_table.c.active,
                projects_table.c.horas_trabajadas,
                projects_table.c.horas_totales_estimadas,
                projects_table.c.fecha_inicio_real
            ).order_by(projects_table.c.priority)
        ).fetchall()
        
        projects = {}
        for row in results:
            projects[row.id] = Project(
                id=row.id,
                name=row.name,
                priority=row.priority,
                phase=row.phase or "draft",  # Mantenido para compatibilidad
                start_date=row.start_date,
                due_date_wo_qa=row.due_date_wo_qa,
                due_date_with_qa=row.due_date_with_qa,
                active=row.active if row.active is not None else True,
                horas_trabajadas=row.horas_trabajadas or 0,
                horas_totales_estimadas=row.horas_totales_estimadas or 0,
                fecha_inicio_real=row.fecha_inicio_real
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
                phase=project.phase,
                start_date=project.start_date,
                due_date_wo_qa=project.due_date_wo_qa,
                due_date_with_qa=project.due_date_with_qa,
                active=project.active,
                horas_trabajadas=project.horas_trabajadas,
                horas_totales_estimadas=project.horas_totales_estimadas,
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