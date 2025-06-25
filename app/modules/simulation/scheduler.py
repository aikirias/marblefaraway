"""
Simulador de scheduling actualizado para usar modelos reales de APE
"""

import math
from datetime import date
from typing import List, Dict
import pandas as pd
from pandas.tseries.offsets import BusinessDay

from .models import Assignment, Team, Project, ScheduleResult, SimulationInput


class ProjectScheduler:
    """Simulador de cronogramas de proyectos usando estructura real de APE"""
    
    def __init__(self):
        pass
    
    def simulate(self, simulation_input: SimulationInput) -> ScheduleResult:
        """
        Ejecuta la simulación de scheduling
        
        Args:
            simulation_input: Input completo con teams, projects y assignments
        
        Returns:
            ScheduleResult con cronograma calculado
        """
        teams = simulation_input.teams
        projects = simulation_input.projects
        assignments = simulation_input.assignments
        today = simulation_input.simulation_start_date
        
        # Estructuras de estado
        active_by_team = {tid: [] for tid in teams.keys()}
        project_next_free = {}
        
        # Ordenar asignaciones por prioridad del proyecto
        sorted_assignments = sorted(assignments, key=lambda a: a.project_priority)
        
        # Procesar cada asignación
        for assignment in sorted_assignments:
            self._process_assignment(assignment, teams, active_by_team, 
                                   project_next_free, today)
        
        # Generar resumen por proyecto
        project_summaries = self._generate_project_summaries(sorted_assignments, projects, today)
        
        return ScheduleResult(
            assignments=sorted_assignments,
            project_summaries=project_summaries
        )
    
    def _process_assignment(self, assignment: Assignment, teams: Dict[int, Team],
                          active_by_team: Dict, project_next_free: Dict, today: date):
        """Procesa una asignación individual"""
        
        team = teams[assignment.team_id]
        
        # Calcular horas necesarias basado en tier y devs asignados
        hours_needed = assignment.get_hours_needed(team)
        
        # Fecha mínima de inicio (constraint de ready_to_start_date)
        ready = max(assignment.ready_to_start_date, today)
        
        # Respetar dependencias del proyecto (asignaciones anteriores)
        if assignment.project_id in project_next_free:
            ready = max(ready, project_next_free[assignment.project_id])
        
        # Calcular duración en días hábiles
        hours_per_day = assignment.devs_assigned * 8  # 8 horas por dev por día
        days_needed = math.ceil(hours_needed / hours_per_day) if hours_per_day > 0 else 1
        
        # Encontrar primera fecha donde cabe
        start_date = self._find_available_slot(
            assignment.team_id, assignment.devs_assigned, days_needed,
            ready, teams, active_by_team
        )
        
        # Calcular fecha de fin
        end_date = self._calculate_end_date(start_date, days_needed)
        
        # Actualizar asignación con fechas calculadas
        assignment.calculated_start_date = start_date
        assignment.calculated_end_date = end_date
        assignment.pending_hours = hours_needed
        
        # Registrar en estado activo
        active_by_team[assignment.team_id].append({
            'start': start_date,
            'end': end_date,
            'devs': assignment.devs_assigned,
            'assignment_id': assignment.id
        })
        
        # Actualizar próxima fecha libre del proyecto
        next_free = self._next_business_day(end_date)
        project_next_free[assignment.project_id] = next_free
    
    def _find_available_slot(self, team_id: int, devs_needed: float, days_needed: int,
                           earliest_start: date, teams: Dict[int, Team], 
                           active_by_team: Dict) -> date:
        """Encuentra la primera fecha donde cabe la asignación"""
        
        candidate_start = earliest_start
        max_iterations = 365 * 2  # Máximo 2 años en el futuro
        iterations = 0
        
        while not self._fits_in_period(team_id, devs_needed, days_needed, 
                                      candidate_start, teams, active_by_team):
            # Protección contra loop infinito
            iterations += 1
            if iterations > max_iterations:
                raise ValueError(f"No se pudo encontrar slot disponible para team {team_id} "
                               f"después de {max_iterations} iteraciones. "
                               f"Fecha límite alcanzada: {candidate_start}")
            
            # Avanzar al siguiente día hábil
            candidate_start = self._next_business_day(candidate_start)
        
        return candidate_start
    
    def _fits_in_period(self, team_id: int, devs_needed: float, days_needed: int,
                       start_date: date, teams: Dict[int, Team], 
                       active_by_team: Dict) -> bool:
        """Verifica si la asignación cabe en el período"""
        
        team = teams[team_id]
        
        for i in range(days_needed):
            check_date = self._add_business_days(start_date, i)
            
            # Calcular uso actual del equipo en esta fecha
            used_devs = team.busy_devs  # Devs ya ocupados por trabajos en curso
            
            for active in active_by_team[team_id]:
                if active['start'] <= check_date <= active['end']:
                    used_devs += active['devs']
            
            # Verificar si hay capacidad
            if used_devs + devs_needed > team.total_devs:
                return False
        
        return True
    
    def _calculate_end_date(self, start_date: date, days_needed: int) -> date:
        """Calcula fecha de fin considerando días hábiles"""
        if days_needed <= 0:
            return start_date
        
        # Calcular fecha de fin (días_needed - 1 porque el primer día cuenta)
        end_timestamp = pd.Timestamp(start_date) + BusinessDay(days_needed - 1)
        return end_timestamp.date()
    
    def _add_business_days(self, start_date: date, days: int) -> date:
        """Suma días hábiles a una fecha"""
        if days == 0:
            return start_date
        
        result_timestamp = pd.Timestamp(start_date) + BusinessDay(days)
        return result_timestamp.date()
    
    def _next_business_day(self, current_date: date) -> date:
        """Obtiene el siguiente día hábil"""
        next_timestamp = pd.Timestamp(current_date) + BusinessDay(1)
        return next_timestamp.date()
    
    def _generate_project_summaries(self, assignments: List[Assignment], 
                                   projects: Dict[int, Project], today: date) -> List[Dict]:
        """Genera resumen por proyecto"""
        summaries = []
        
        # Agrupar por proyecto
        project_assignments = {}
        for assignment in assignments:
            if assignment.project_id not in project_assignments:
                project_assignments[assignment.project_id] = []
            project_assignments[assignment.project_id].append(assignment)
        
        # Crear resumen para cada proyecto
        for project_id, assignments_list in project_assignments.items():
            project = projects.get(project_id)
            if not project:
                continue
            
            # Calcular fechas del proyecto
            start_dates = [a.calculated_start_date for a in assignments_list 
                          if a.calculated_start_date is not None]
            end_dates = [a.calculated_end_date for a in assignments_list 
                        if a.calculated_end_date is not None]
            
            project_start = min(start_dates) if start_dates else None
            project_end = max(end_dates) if end_dates else None
            
            # Determinar estado
            state = self._determine_project_state(assignments_list, today)
            
            # Calcular total de horas
            total_hours = sum(a.pending_hours for a in assignments_list)
            
            summaries.append({
                'project_id': project_id,
                'project_name': project.name,
                'priority': project.priority,
                'state': state,
                'calculated_start_date': project_start,
                'calculated_end_date': project_end,
                'original_start_date': project.start_date,
                'due_date_wo_qa': project.due_date_wo_qa,
                'due_date_with_qa': project.due_date_with_qa,
                'total_assignments': len(assignments_list),
                'total_hours': total_hours,
                'delay_days': self._calculate_delay_days(project_end, project.due_date_wo_qa) if project_end else 0
            })
        
        # Ordenar por prioridad
        summaries.sort(key=lambda x: x['priority'])
        return summaries
    
    def _determine_project_state(self, project_assignments: List[Assignment], today: date) -> str:
        """Determina el estado actual del proyecto"""
        if not project_assignments:
            return "No assignments"
        
        # Verificar si hay fechas calculadas
        assignments_with_dates = [a for a in project_assignments 
                                 if a.calculated_start_date and a.calculated_end_date]
        
        if not assignments_with_dates:
            return "Not scheduled"
        
        start_dates = [a.calculated_start_date for a in assignments_with_dates]
        end_dates = [a.calculated_end_date for a in assignments_with_dates]
        
        project_start = min(start_dates)
        project_end = max(end_dates)
        
        if today < project_start:
            return "Not started"
        elif today > project_end:
            return "Completed"
        else:
            # Buscar asignación actual
            for assignment in assignments_with_dates:
                if assignment.calculated_start_date <= today <= assignment.calculated_end_date:
                    return f"In progress ({assignment.team_name})"
            return "In progress"
    
    def _calculate_delay_days(self, actual_end: date, planned_end: date) -> int:
        """Calcula días de retraso"""
        if not actual_end or not planned_end:
            return 0
        
        if actual_end <= planned_end:
            return 0
        
        # Calcular días hábiles de diferencia
        delay_timestamp = pd.Timestamp(actual_end) - pd.Timestamp(planned_end)
        return delay_timestamp.days