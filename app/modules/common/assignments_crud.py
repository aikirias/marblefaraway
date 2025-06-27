"""
CRUD básico para Assignment
Sin validaciones, operaciones directas con DB
Maneja el mapeo assignment_start_date <-> start_date
"""

import sqlalchemy as sa
from typing import List, Optional
from .db import engine, project_team_assignments_table, projects_table, teams_table
from .models import Assignment


def create_assignment(assignment: Assignment) -> int:
    """Crear assignment en DB"""
    with engine.begin() as conn:
        result = conn.execute(
            project_team_assignments_table.insert().values(
                project_id=assignment.project_id,
                team_id=assignment.team_id,
                tier=assignment.tier,
                devs_assigned=assignment.devs_assigned,
                max_devs=assignment.max_devs,
                estimated_hours=assignment.estimated_hours,
                start_date=assignment.assignment_start_date,  # Mapeo: assignment_start_date -> start_date
                ready_to_start_date=assignment.ready_to_start_date,
                paused_on=assignment.paused_on,
                pending_hours=assignment.pending_hours,
                status=assignment.status
            ).returning(project_team_assignments_table.c.id)
        )
        return result.scalar()


def read_assignment(assignment_id: int) -> Optional[Assignment]:
    """Leer assignment desde DB con JOINs"""
    with engine.begin() as conn:
        result = conn.execute(
            sa.select(
                project_team_assignments_table.c.id,
                project_team_assignments_table.c.project_id,
                projects_table.c.name.label("project_name"),
                projects_table.c.priority.label("project_priority"),
                project_team_assignments_table.c.team_id,
                teams_table.c.name.label("team_name"),
                project_team_assignments_table.c.tier,
                project_team_assignments_table.c.devs_assigned,
                project_team_assignments_table.c.max_devs,
                project_team_assignments_table.c.estimated_hours,
                project_team_assignments_table.c.ready_to_start_date,
                project_team_assignments_table.c.start_date.label("assignment_start_date"),  # Mapeo: start_date -> assignment_start_date
                project_team_assignments_table.c.status,
                project_team_assignments_table.c.pending_hours,
                project_team_assignments_table.c.paused_on
            )
            .select_from(
                project_team_assignments_table
                .join(projects_table, project_team_assignments_table.c.project_id == projects_table.c.id)
                .join(teams_table, project_team_assignments_table.c.team_id == teams_table.c.id)
            )
            .where(project_team_assignments_table.c.id == assignment_id)
        ).first()
        
        if not result:
            return None
        
        return Assignment(
            id=result.id,
            project_id=result.project_id,
            project_name=result.project_name,
            project_priority=result.project_priority,
            team_id=result.team_id,
            team_name=result.team_name,
            tier=result.tier,
            devs_assigned=float(result.devs_assigned),
            max_devs=float(result.max_devs),
            estimated_hours=result.estimated_hours,
            ready_to_start_date=result.ready_to_start_date,
            assignment_start_date=result.assignment_start_date,
            status=result.status,
            pending_hours=result.pending_hours or 0,
            paused_on=result.paused_on
        )


def read_assignments_by_project(project_id: int) -> List[Assignment]:
    """Leer assignments de un proyecto"""
    with engine.begin() as conn:
        results = conn.execute(
            sa.select(
                project_team_assignments_table.c.id,
                project_team_assignments_table.c.project_id,
                projects_table.c.name.label("project_name"),
                projects_table.c.priority.label("project_priority"),
                project_team_assignments_table.c.team_id,
                teams_table.c.name.label("team_name"),
                project_team_assignments_table.c.tier,
                project_team_assignments_table.c.devs_assigned,
                project_team_assignments_table.c.max_devs,
                project_team_assignments_table.c.estimated_hours,
                project_team_assignments_table.c.ready_to_start_date,
                project_team_assignments_table.c.start_date.label("assignment_start_date"),
                project_team_assignments_table.c.status,
                project_team_assignments_table.c.pending_hours,
                project_team_assignments_table.c.paused_on
            )
            .select_from(
                project_team_assignments_table
                .join(projects_table, project_team_assignments_table.c.project_id == projects_table.c.id)
                .join(teams_table, project_team_assignments_table.c.team_id == teams_table.c.id)
            )
            .where(project_team_assignments_table.c.project_id == project_id)
            .order_by(teams_table.c.name)
        ).fetchall()
        
        assignments = []
        for row in results:
            assignments.append(Assignment(
                id=row.id,
                project_id=row.project_id,
                project_name=row.project_name,
                project_priority=row.project_priority,
                team_id=row.team_id,
                team_name=row.team_name,
                tier=row.tier,
                devs_assigned=float(row.devs_assigned),
                max_devs=float(row.max_devs),
                estimated_hours=row.estimated_hours,
                ready_to_start_date=row.ready_to_start_date,
                assignment_start_date=row.assignment_start_date,
                status=row.status,
                pending_hours=row.pending_hours or 0,
                paused_on=row.paused_on
            ))
        
        return assignments


def read_all_assignments() -> List[Assignment]:
    """Leer todos los assignments"""
    with engine.begin() as conn:
        results = conn.execute(
            sa.select(
                project_team_assignments_table.c.id,
                project_team_assignments_table.c.project_id,
                projects_table.c.name.label("project_name"),
                projects_table.c.priority.label("project_priority"),
                project_team_assignments_table.c.team_id,
                teams_table.c.name.label("team_name"),
                project_team_assignments_table.c.tier,
                project_team_assignments_table.c.devs_assigned,
                project_team_assignments_table.c.max_devs,
                project_team_assignments_table.c.estimated_hours,
                project_team_assignments_table.c.ready_to_start_date,
                project_team_assignments_table.c.start_date.label("assignment_start_date"),
                project_team_assignments_table.c.status,
                project_team_assignments_table.c.pending_hours,
                project_team_assignments_table.c.paused_on
            )
            .select_from(
                project_team_assignments_table
                .join(projects_table, project_team_assignments_table.c.project_id == projects_table.c.id)
                .join(teams_table, project_team_assignments_table.c.team_id == teams_table.c.id)
            )
            .order_by(projects_table.c.priority, teams_table.c.name)
        ).fetchall()
        
        assignments = []
        for row in results:
            assignments.append(Assignment(
                id=row.id,
                project_id=row.project_id,
                project_name=row.project_name,
                project_priority=row.project_priority,
                team_id=row.team_id,
                team_name=row.team_name,
                tier=row.tier,
                devs_assigned=float(row.devs_assigned),
                max_devs=float(row.max_devs),
                estimated_hours=row.estimated_hours,
                ready_to_start_date=row.ready_to_start_date,
                assignment_start_date=row.assignment_start_date,
                status=row.status,
                pending_hours=row.pending_hours or 0,
                paused_on=row.paused_on
            ))
        
        return assignments


def update_assignment(assignment: Assignment):
    """Actualizar assignment en DB"""
    with engine.begin() as conn:
        conn.execute(
            project_team_assignments_table.update()
            .where(project_team_assignments_table.c.id == assignment.id)
            .values(
                project_id=assignment.project_id,
                team_id=assignment.team_id,
                tier=assignment.tier,
                devs_assigned=assignment.devs_assigned,
                max_devs=assignment.max_devs,
                estimated_hours=assignment.estimated_hours,
                start_date=assignment.assignment_start_date,  # Mapeo: assignment_start_date -> start_date
                ready_to_start_date=assignment.ready_to_start_date,
                paused_on=assignment.paused_on,
                pending_hours=assignment.pending_hours,
                status=assignment.status
                # NOTA: campos calculados NO se guardan en DB
            )
        )


def delete_assignment(assignment_id: int):
    """Borrar assignment de DB"""
    with engine.begin() as conn:
        conn.execute(
            project_team_assignments_table.delete()
            .where(project_team_assignments_table.c.id == assignment_id)
        )


def delete_assignments_by_project(project_id: int):
    """Borrar todas las asignaciones de un proyecto"""
    with engine.begin() as conn:
        conn.execute(
            project_team_assignments_table.delete()
            .where(project_team_assignments_table.c.project_id == project_id)
        )