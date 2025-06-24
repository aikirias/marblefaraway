"""
Simulador de scheduling simple pero completo
"""

import math
from datetime import date
from typing import List, Dict
import pandas as pd
from pandas.tseries.offsets import BusinessDay

from .models import Assignment, Team, ScheduleResult


class ProjectScheduler:
    """Simulador de cronogramas de proyectos"""
    
    def __init__(self, phase_order: List[str] = None):
        self.phase_order = phase_order or ["Arch", "Model", "Devs", "Dqa"]
    
    def simulate(self, assignments: List[Assignment], teams: Dict[int, Team], 
                 today: date = None) -> ScheduleResult:
        """
        Ejecuta la simulación de scheduling
        
        Args:
            assignments: Lista de asignaciones a simular
            teams: Diccionario de equipos {team_id: Team}
            today: Fecha de inicio de simulación (default: hoy)
        
        Returns:
            ScheduleResult con cronograma calculado
        """
        if today is None:
            today = date.today()
        
        # Estructuras de estado
        active_by_team = {tid: [] for tid in teams.keys()}
        project_next_free = {}
        
        # Ordenar asignaciones por prioridad y orden de fase
        sorted_assignments = sorted(assignments, key=lambda a: (a.priority, a.phase_order))
        
        # Procesar cada asignación
        for assignment in sorted_assignments:
            self._process_assignment(assignment, teams, active_by_team, 
                                   project_next_free, today)
        
        # Generar resumen por proyecto
        project_summaries = self._generate_project_summaries(sorted_assignments, today)
        
        return ScheduleResult(
            assignments=sorted_assignments,
            project_summaries=project_summaries
        )
    
    def _process_assignment(self, assignment: Assignment, teams: Dict[int, Team],
                          active_by_team: Dict, project_next_free: Dict, today: date):
        """Procesa una asignación individual"""
        
        # Fecha mínima de inicio
        ready = max(assignment.ready_date, today)
        
        # Respetar dependencias del proyecto
        if assignment.project_id in project_next_free:
            ready = max(ready, project_next_free[assignment.project_id])
        
        # Calcular duración
        hours_per_day = assignment.devs_assigned * 8
        days_needed = math.ceil(assignment.hours_needed / hours_per_day)
        
        # Encontrar primera fecha donde cabe
        start_date = self._find_available_slot(
            assignment.team_id, assignment.devs_assigned, days_needed,
            ready, teams, active_by_team
        )
        
        # Calcular fecha de fin
        end_date = self._calculate_end_date(start_date, days_needed)
        
        # Actualizar asignación
        assignment.start_date = start_date
        assignment.end_date = end_date
        
        # Registrar en estado activo
        active_by_team[assignment.team_id].append({
            'start': start_date,
            'end': end_date,
            'devs': assignment.devs_assigned
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
            used_devs = team.busy_devs
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
        
        # Si empieza hoy, termina al día siguiente (o días_needed después)
        end_timestamp = pd.Timestamp(start_date) + BusinessDay(days_needed)
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
    
    def _generate_project_summaries(self, assignments: List[Assignment], today: date) -> List[Dict]:
        """Genera resumen por proyecto"""
        summaries = []
        
        # Agrupar por proyecto
        projects = {}
        for assignment in assignments:
            if assignment.project_id not in projects:
                projects[assignment.project_id] = []
            projects[assignment.project_id].append(assignment)
        
        # Crear resumen para cada proyecto
        for project_id, project_assignments in projects.items():
            # Ordenar por fase
            sorted_phases = sorted(project_assignments, key=lambda a: a.phase_order)
            
            first_phase = sorted_phases[0]
            last_phase = sorted_phases[-1]
            
            start_date = first_phase.start_date
            end_date = last_phase.end_date
            
            # Determinar estado
            state = self._determine_project_state(project_assignments, today)
            
            summaries.append({
                'project_id': project_id,
                'project_name': first_phase.project_name,
                'state': state,
                'start_date': start_date,
                'end_date': end_date,
                'total_phases': len(project_assignments)
            })
        
        return summaries
    
    def _determine_project_state(self, project_assignments: List[Assignment], today: date) -> str:
        """Determina el estado actual del proyecto"""
        sorted_phases = sorted(project_assignments, key=lambda a: a.phase_order)
        
        start_date = sorted_phases[0].start_date
        end_date = sorted_phases[-1].end_date
        
        if today < start_date:
            return "Not started"
        elif today > end_date:
            return "Done"
        else:
            # Buscar fase actual
            for assignment in sorted_phases:
                if assignment.start_date <= today <= assignment.end_date:
                    return assignment.phase
            return "Waiting"