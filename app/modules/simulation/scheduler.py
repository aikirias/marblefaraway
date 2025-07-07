"""
Simulador de scheduling actualizado para usar modelos reales de APE
Versión final con lógica de secuenciación, priorización y paralelismo corregida.
"""

import math
import json
import logging
from datetime import date
from typing import List, Dict
import pandas as pd
from pandas.tseries.offsets import BusinessDay

from ..common.models import Assignment, Team, Project, ScheduleResult, SimulationInput
from ..common.date_utils import validate_date_range

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

class ProjectScheduler:
    """Simulador de cronogramas de proyectos APE con lógica de negocio correcta y determinista."""

    def __init__(self):
        self.team_processing_order = {"Arch": 1, "Devs": 2, "Model": 3, "Dqa": 4}

    def simulate(self, simulation_input: SimulationInput, completed_phases: Dict[int, date] = None) -> ScheduleResult:
        if not simulation_input.teams:
            raise KeyError("El diccionario de equipos no puede estar vacío.")
        for team in simulation_input.teams.values():
            if team.total_devs < 0:
                raise ValueError(f"El equipo {team.name} tiene capacidad negativa.")

        today = simulation_input.simulation_start_date

        active_project_ids = {p.id for p in simulation_input.projects.values() if p.is_active()}
        if not active_project_ids:
            return ScheduleResult(assignments=[], project_summaries=[])

        active_assignments = [a for a in simulation_input.assignments if a.project_id in active_project_ids]
        sorted_projects = sorted([p for p in simulation_input.projects.values() if p.id in active_project_ids], key=lambda p: p.priority)

        team_availability = {
            team_id: [today] * team.total_devs for team_id, team in simulation_input.teams.items() if team.total_devs > 0
        }
        
        processed_assignments = []
        project_end_dates = {}

        for project in sorted_projects:
            project_assignments = [a for a in active_assignments if a.project_id == project.id]
            sorted_project_assignments = sorted(
                project_assignments,
                key=lambda a: self.team_processing_order.get(a.team_name, 99)
            )

            last_phase_end_date = project_end_dates.get(project.id, project.fecha_inicio_real or today)

            for assignment in sorted_project_assignments:
                if completed_phases and assignment.id in completed_phases:
                    # Fase ya completada. Se ancla su fecha de finalización.
                    actual_end_date = completed_phases[assignment.id]
                    
                    # Asumimos que la fecha de inicio es la misma que la de fin si no la tenemos.
                    # Esto es una simplificación; idealmente, también guardaríamos la fecha de inicio real.
                    assignment.calculated_start_date = actual_end_date 
                    assignment.calculated_end_date = actual_end_date
                    
                    # La marcamos como procesada.
                    processed_assignments.append(assignment)
                    
                    # La siguiente fase puede empezar un día hábil después.
                    next_available_date = self._add_business_days(actual_end_date, 1)
                    last_phase_end_date = next_available_date
                    project_end_dates[project.id] = next_available_date
                    
                    # Saltamos el resto de la lógica de scheduling para esta fase.
                    continue
                if assignment.team_id not in simulation_input.teams:
                    raise KeyError(f"La asignación {assignment.id} hace referencia a un team_id inexistente: {assignment.team_id}")

                team = simulation_input.teams[assignment.team_id]
                if team.total_devs == 0:
                    continue

                devs_needed = int(assignment.devs_assigned)

                if devs_needed > team.total_devs:
                    logger.warning(f"Asignación {assignment.id} requiere {devs_needed} devs, pero el equipo {team.name} solo tiene {team.total_devs}. Saltando.")
                    continue

                team_availability[team.id].sort()
                
                dev_free_date = team_availability[team.id][devs_needed - 1]
                
                start_date = max(last_phase_end_date, dev_free_date, assignment.ready_to_start_date, project.fecha_inicio_real or today)

                hours_needed = assignment.get_hours_needed(team)
                hours_per_day = assignment.devs_assigned * 8
                days_needed = math.ceil(hours_needed / hours_per_day) if hours_per_day > 0 else 1
                
                end_date = self._add_business_days(start_date, days_needed - 1)

                assignment.calculated_start_date = start_date
                assignment.calculated_end_date = end_date
                
                next_available_date = self._add_business_days(end_date, 1)
                for i in range(devs_needed):
                    team_availability[team.id][i] = next_available_date

                last_phase_end_date = next_available_date
                project_end_dates[project.id] = last_phase_end_date
                processed_assignments.append(assignment)

        project_summaries = self._generate_project_summaries(processed_assignments, simulation_input.projects)
        
        return ScheduleResult(
            assignments=processed_assignments,
            project_summaries=project_summaries
        )

    def _add_business_days(self, start_date: date, days: int) -> date:
        return (pd.Timestamp(start_date) + BusinessDay(days)).date()

    def _generate_project_summaries(self, assignments: List[Assignment], projects: Dict[int, Project]) -> List[Dict]:
        summaries = []
        project_assignments = {}
        for assignment in assignments:
            pid = assignment.project_id
            if pid not in project_assignments:
                project_assignments[pid] = []
            project_assignments[pid].append(assignment)
        
        for project_id, assignments_list in project_assignments.items():
            project = projects.get(project_id)
            if not project: continue
            
            start_dates = [a.calculated_start_date for a in assignments_list if a.calculated_start_date]
            end_dates = [a.calculated_end_date for a in assignments_list if a.calculated_end_date]
            
            summaries.append({
                'project_id': project_id,
                'project_name': project.name,
                'priority': project.priority,
                'calculated_start_date': min(start_dates) if start_dates else None,
                'calculated_end_date': max(end_dates) if end_dates else None,
            })
        
        summaries.sort(key=lambda x: x['priority'])
        return summaries