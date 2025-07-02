"""
Simulador de scheduling actualizado para usar modelos reales de APE
"""

import math
import json
import logging
from datetime import date
from typing import List, Dict
import pandas as pd
from pandas.tseries.offsets import BusinessDay

from ..common.models import Assignment, Team, Project, ScheduleResult, SimulationInput

# Configurar logging para debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar utilidades comunes
from ..common.constants import MIN_DATE, MAX_DATE
from ..common.date_utils import validate_date_range, add_business_days, safe_business_day_calculation


class EnhancedJSONEncoder(json.JSONEncoder):
    """Encoder JSON personalizado para manejar objetos date y dataclasses"""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


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
        today = validate_date_range(simulation_input.simulation_start_date, "simulation_start_date")
        
        # CORRECCIÓN: Incluir TODOS los proyectos (activos y pausados) para mostrar en monitoring
        # La prioridad efectiva se manejará en el ordenamiento
        all_projects = projects
        
        # Incluir assignments de TODOS los proyectos
        all_assignments = assignments
        
        logger.info(f"Simulando {len(all_projects)} proyectos (activos y pausados) con {len(all_assignments)} asignaciones")
        
        # Estructuras de estado
        active_by_team = {tid: [] for tid in teams.keys()}
        project_next_free = {}
        
        # CORRECCIÓN: Implementar prioridad efectiva - activos primero, luego pausados
        # Para APE: Arch (team_id=1) → Devs (team_id=3) → Model (team_id=2) → Dqa (team_id=4)
        def sort_key(assignment):
            # Obtener el proyecto para verificar si está activo
            project = all_projects.get(assignment.project_id)
            if project:
                # Prioridad efectiva: (0, prioridad) para activos, (1, prioridad) para pausados
                if project.is_active():
                    effective_priority = (0, project.priority)  # Activos primero - usar prioridad real del proyecto
                else:
                    effective_priority = (1, project.priority)  # Pausados después - usar prioridad real del proyecto
            else:
                # Fallback si no se encuentra el proyecto
                effective_priority = (1, assignment.project_priority)
            
            # Luego por orden de equipos APE (orden correcto)
            team_order = {2: 1, 1: 2, 3: 3, 4: 4}.get(assignment.team_id, 999)  # Arch → Devs → Model → Dqa
            return (effective_priority, team_order, assignment.id)
        
        sorted_assignments = sorted(all_assignments, key=sort_key)
        
        # Procesar cada asignación
        for assignment in sorted_assignments:
            try:
                self._process_assignment(assignment, teams, active_by_team, 
                                       project_next_free, today, all_projects)
            except Exception as e:
                logger.error(f"Error procesando asignación {assignment.id}: {e}")
                # Asignar fechas por defecto para evitar que falle toda la simulación
                assignment.calculated_start_date = today
                assignment.calculated_end_date = today
                assignment.pending_hours = 0
        
        # Generar resumen por proyecto
        project_summaries = self._generate_project_summaries(sorted_assignments, all_projects, today)
        
        # Crear resultado de la simulación
        result = ScheduleResult(
            assignments=sorted_assignments,
            project_summaries=project_summaries
        )
        
        # Guardar output de la simulación (opcional para debugging)
        try:
            output_json_path = './simulation_output.json'
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, cls=EnhancedJSONEncoder, indent=2, ensure_ascii=False)
            logger.info(f"Resultado guardado en {output_json_path}")
        except Exception as e:
            logger.warning(f"No se pudo guardar el resultado: {e}")
        
        return result
    
    def _process_assignment(self, assignment: Assignment, teams: Dict[int, Team],
                          active_by_team: Dict, project_next_free: Dict, today: date, projects: Dict[int, Project] = None):
        """Procesa una asignación individual"""
        
        team = teams[assignment.team_id]
        
        # Calcular horas necesarias basado en tier y devs asignados
        hours_needed = assignment.get_hours_needed(team)
        
        # Validar que las horas sean razonables
        if hours_needed <= 0:
            logger.warning(f"Asignación {assignment.id} tiene 0 horas. Usando tier capacity como fallback.")
            hours_needed = team.get_hours_per_person_for_tier(assignment.tier) * assignment.devs_assigned
            if hours_needed <= 0:
                hours_needed = 8  # Mínimo 1 día de trabajo
        
        # Fecha mínima de inicio (constraint de ready_to_start_date)
        ready = max(validate_date_range(assignment.ready_to_start_date, f"ready_to_start_date assignment {assignment.id}"), today)
        
        # CORRECCIÓN ROBUSTA: Usar fecha_inicio_real del proyecto si está disponible
        # Verificar si es la primera asignación del proyecto (no está en project_next_free)
        # O si es la asignación de Arch (que siempre debe respetar fecha_inicio_real)
        if projects and assignment.project_id in projects:
            project = projects[assignment.project_id]
            if project.fecha_inicio_real:
                fecha_inicio_real = validate_date_range(project.fecha_inicio_real, f"fecha_inicio_real project {assignment.project_id}")
                
                # Verificar si es la primera asignación o si es Arch (team_id=2)
                is_first_assignment = assignment.project_id not in project_next_free
                is_arch_team = assignment.team_id == 2  # Arch tiene team_id=2
                
                if is_first_assignment or is_arch_team:
                    # Siempre usar fecha_inicio_real para la primera asignación o para Arch
                    logger.info(f"🔍 DEBUG FECHA_INICIO_REAL: Usando fecha_inicio_real {fecha_inicio_real} para proyecto {project.name} (ID: {project.id})")
                    logger.info(f"🔍 DETALLES: Es primera asignación: {is_first_assignment}, Es equipo Arch: {is_arch_team}")
                    logger.info(f"🔍 FECHAS: ready antes={ready}, fecha_inicio_real={fecha_inicio_real}")
                    
                    # CORRECCIÓN CRÍTICA: Para Arch, la fecha de inicio DEBE SER EXACTAMENTE fecha_inicio_real
                    # No usar max() que podría dar una fecha posterior
                    if is_arch_team:
                        ready = fecha_inicio_real
                        logger.info(f"🔍 FORZANDO FECHA EXACTA para Arch: {fecha_inicio_real}")
                    else:
                        # Para otras asignaciones, asegurar que la fecha de inicio sea al menos la fecha_inicio_real
                        ready = max(ready, fecha_inicio_real)
                    
                    logger.info(f"🔍 RESULTADO: ready después={ready}")
        
        # Respetar dependencias del proyecto (asignaciones anteriores)
        if assignment.project_id in project_next_free:
            ready = max(ready, validate_date_range(project_next_free[assignment.project_id], f"project_next_free {assignment.project_id}"))
        
        # Calcular duración en días hábiles
        hours_per_day = assignment.devs_assigned * 8  # 8 horas por dev por día
        days_needed = math.ceil(hours_needed / hours_per_day) if hours_per_day > 0 else 1
        
        # Validar que days_needed sea razonable
        if days_needed > 365:
            logger.warning(f"Asignación {assignment.id} requiere {days_needed} días. Limitando a 365.")
            days_needed = 365
        
        # Encontrar primera fecha donde cabe
        start_date = self._find_available_slot(
            assignment.team_id, assignment.devs_assigned, days_needed,
            ready, teams, active_by_team
        )
        
        # Calcular fecha de fin
        end_date = self._calculate_end_date(start_date, days_needed)
        
        # Validar fechas calculadas
        start_date = validate_date_range(start_date, f"start_date assignment {assignment.id}")
        end_date = validate_date_range(end_date, f"end_date assignment {assignment.id}")
        
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
        project_next_free[assignment.project_id] = validate_date_range(next_free, f"next_free project {assignment.project_id}")
        
        logger.debug(f"Asignación {assignment.id} ({assignment.team_name}): {start_date} a {end_date} ({days_needed} días, {hours_needed} horas)")
    
    def _find_available_slot(self, team_id: int, devs_needed: float, days_needed: int,
                           earliest_start: date, teams: Dict[int, Team], 
                           active_by_team: Dict) -> date:
        """Encuentra la primera fecha donde cabe la asignación con optimizaciones"""
        
        team = teams[team_id]
        
        # Validación temprana de capacidad
        if devs_needed > team.total_devs:
            raise ValueError(f"Equipo {team_id} no tiene capacidad suficiente: "
                           f"necesita {devs_needed} devs, disponible {team.total_devs}")
        
        # Verificar disponibilidad básica
        available_devs = team.total_devs - team.busy_devs
        if available_devs <= 0:
            # Si no hay devs disponibles, buscar la próxima fecha libre
            candidate_start = self._find_next_free_date(team_id, active_by_team, earliest_start)
        else:
            candidate_start = earliest_start
        
        # Límite conservador y búsqueda inteligente
        max_iterations = 180  # 6 meses máximo
        iterations = 0
        
        while not self._fits_in_period(team_id, devs_needed, days_needed, 
                                      candidate_start, teams, active_by_team):
            iterations += 1
            
            # Salto inteligente después de varios intentos
            if iterations > 30:
                next_free = self._find_next_free_date(team_id, active_by_team, candidate_start)
                if next_free > candidate_start:
                    candidate_start = next_free
                    continue
            
            # Protección contra loop infinito
            if iterations > max_iterations:
                logger.error(f"No se pudo encontrar slot para team {team_id} en {max_iterations} días")
                # Retornar fecha límite en lugar de fallar
                return validate_date_range(self._add_business_days(earliest_start, max_iterations), f"fallback team {team_id}")
            
            # Avanzar al siguiente día hábil
            try:
                candidate_start = self._next_business_day(candidate_start)
                candidate_start = validate_date_range(candidate_start, f"candidate_start team {team_id}")
            except Exception as e:
                logger.error(f"Error calculando siguiente día hábil desde {candidate_start}: {e}")
                return validate_date_range(earliest_start, f"error_fallback team {team_id}")
        
        return validate_date_range(candidate_start, f"final_candidate team {team_id}")
    
    def _find_next_free_date(self, team_id: int, active_by_team: Dict, earliest_start: date) -> date:
        """Encuentra la próxima fecha libre para un equipo"""
        if team_id not in active_by_team or not active_by_team[team_id]:
            return earliest_start
        
        # Encontrar la fecha más tardía de finalización
        latest_end = earliest_start
        for active in active_by_team[team_id]:
            if active['end'] > latest_end:
                latest_end = active['end']
        
        # Retornar el siguiente día hábil después de la última finalización
        return self._next_business_day(latest_end)
    
    def _fits_in_period(self, team_id: int, devs_needed: float, days_needed: int,
                       start_date: date, teams: Dict[int, Team], 
                       active_by_team: Dict) -> bool:
        """Verifica si la asignación cabe en el período"""
        
        team = teams[team_id]
        
        # Verificar si el equipo tiene capacidad total suficiente
        if devs_needed > team.total_devs:
            return False
        
        # Verificar si hay capacidad disponible considerando busy_devs
        available_devs = team.total_devs - team.busy_devs
        if available_devs <= 0:
            return False
        
        for i in range(days_needed):
            try:
                check_date = self._add_business_days(start_date, i)
                check_date = validate_date_range(check_date, f"check_date team {team_id}")
            except Exception as e:
                logger.error(f"Error calculando fecha de verificación: {e}")
                return False
            
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
        
        try:
            # Calcular fecha de fin: una tarea de N días termina N-1 días después del inicio
            end_timestamp = pd.Timestamp(start_date) + BusinessDay(days_needed - 1)
            return end_timestamp.date()
        except Exception as e:
            logger.error(f"Error calculando fecha de fin desde {start_date} + {days_needed} días: {e}")
            # Fallback: usar cálculo simple
            return validate_date_range(start_date, "end_date_fallback")
    
    def _add_business_days(self, start_date: date, days: int) -> date:
        """Suma días hábiles a una fecha"""
        if days == 0:
            return start_date
        
        try:
            result_timestamp = pd.Timestamp(start_date) + BusinessDay(days)
            return result_timestamp.date()
        except Exception as e:
            logger.error(f"Error sumando {days} días hábiles a {start_date}: {e}")
            # Fallback: usar cálculo simple (no perfecto pero seguro)
            from datetime import timedelta
            return start_date + timedelta(days=days)
    
    def _next_business_day(self, current_date: date) -> date:
        """Obtiene el siguiente día hábil"""
        try:
            next_timestamp = pd.Timestamp(current_date) + BusinessDay(1)
            return next_timestamp.date()
        except Exception as e:
            logger.error(f"Error calculando siguiente día hábil desde {current_date}: {e}")
            # Fallback: usar cálculo simple
            from datetime import timedelta
            return current_date + timedelta(days=1)
    
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
        try:
            delay_timestamp = pd.Timestamp(actual_end) - pd.Timestamp(planned_end)
            return delay_timestamp.days
        except Exception as e:
            logger.error(f"Error calculando días de retraso: {e}")
            return 0