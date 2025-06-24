"""
Integración del simulador con el sistema APE existente
"""

import pandas as pd
from datetime import date
from modules.common.db import engine, projects_table, teams_table, project_team_assignments_table, tier_capacity_table
import sqlalchemy as sa

from .scheduler import ProjectScheduler
from .models import Assignment, Team


def load_data_from_db():
    """Carga datos desde la base de datos APE"""
    
    # Cargar equipos
    teams_df = pd.read_sql(
        sa.select(teams_table.c.id, teams_table.c.name, teams_table.c.total_devs, teams_table.c.busy_devs),
        engine
    )
    
    teams = {}
    for _, row in teams_df.iterrows():
        teams[row.id] = Team(
            id=row.id,
            name=row.name,
            total_devs=row.total_devs,
            busy_devs=row.busy_devs
        )
    
    # Cargar asignaciones con tier capacity
    assignments_query = (
        sa.select(
            project_team_assignments_table.c.project_id,
            projects_table.c.name.label("project_name"),
            projects_table.c.priority,
            teams_table.c.name.label("phase"),
            project_team_assignments_table.c.team_id,
            project_team_assignments_table.c.tier,
            project_team_assignments_table.c.devs_assigned,
            project_team_assignments_table.c.estimated_hours,
            project_team_assignments_table.c.ready_to_start_date,
            tier_capacity_table.c.hours_per_person
        )
        .select_from(
            project_team_assignments_table
            .join(projects_table, project_team_assignments_table.c.project_id == projects_table.c.id)
            .join(teams_table, project_team_assignments_table.c.team_id == teams_table.c.id)
            .join(tier_capacity_table, 
                  sa.and_(
                      project_team_assignments_table.c.team_id == tier_capacity_table.c.team_id,
                      project_team_assignments_table.c.tier == tier_capacity_table.c.tier
                  ))
        )
        .order_by(projects_table.c.priority)
    )
    
    assignments_df = pd.read_sql(assignments_query, engine)
    
    # Mapear fases a orden
    phase_order_map = {"Arch": 0, "Model": 1, "Devs": 2, "Dqa": 3}
    
    assignments = []
    for _, row in assignments_df.iterrows():
        # Calcular horas necesarias
        if row.estimated_hours and row.estimated_hours > 0:
            hours_needed = row.estimated_hours
        else:
            hours_needed = row.hours_per_person * row.devs_assigned
        
        assignment = Assignment(
            project_id=row.project_id,
            project_name=row.project_name,
            phase=row.phase,
            phase_order=phase_order_map.get(row.phase, 0),
            team_id=row.team_id,
            priority=row.priority,
            devs_assigned=row.devs_assigned,
            hours_needed=int(hours_needed),
            ready_date=row.ready_to_start_date or date.today()
        )
        assignments.append(assignment)
    
    return assignments, teams


def run_simulation_from_db(today=None):
    """Ejecuta simulación usando datos de la base de datos"""
    
    assignments, teams = load_data_from_db()
    
    scheduler = ProjectScheduler()
    result = scheduler.simulate(assignments, teams, today)
    
    return result


def format_for_streamlit(result):
    """Formatea el resultado para mostrar en Streamlit"""
    
    # Tabla de cronograma detallado
    schedule_data = []
    for assignment in result.assignments:
        schedule_data.append({
            'Project': assignment.project_name,
            'Phase': assignment.phase,
            'Team': f"Team {assignment.team_id}",
            'Devs': assignment.devs_assigned,
            'Start': assignment.start_date,
            'End': assignment.end_date,
            'Duration': (assignment.end_date - assignment.start_date).days + 1 if assignment.start_date and assignment.end_date else 0
        })
    
    schedule_df = pd.DataFrame(schedule_data)
    
    # Tabla de resumen por proyecto
    summary_data = []
    for summary in result.project_summaries:
        summary_data.append({
            'Project': summary['project_name'],
            'State': summary['state'],
            'Start': summary['start_date'],
            'End': summary['end_date'],
            'Total Duration': (summary['end_date'] - summary['start_date']).days + 1 if summary['start_date'] and summary['end_date'] else 0
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    return schedule_df, summary_df