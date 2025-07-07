"""
Utilidades para el manejo de planes
"""

import logging
from datetime import date
from typing import List, Dict, Any

from .models import Plan, PlanAssignment
from .plans_crud import get_active_plan

logger = logging.getLogger(__name__)


def get_active_assignments(plan: Plan, current_date: date) -> List[Dict[str, Any]]:
    """
    Obtiene las asignaciones activas de un plan en una fecha determinada y calcula su progreso.

    Args:
        plan: El plan a analizar.
        current_date: La fecha actual para determinar qué asignaciones están activas.

    Returns:
        Una lista de diccionarios, donde cada diccionario representa una asignación activa
        y contiene información sobre su progreso.
    """
    if not plan or not plan.assignments:
        return []

    active_assignments_with_progress = []
    for assignment in plan.assignments:
        if assignment.calculated_start_date and assignment.calculated_end_date and \
           assignment.calculated_start_date <= current_date <= assignment.calculated_end_date:
            
            days_elapsed = (current_date - assignment.calculated_start_date).days
            total_days = (assignment.calculated_end_date - assignment.calculated_start_date).days + 1
            
            # Calcular horas trabajadas y restantes
            # Asumimos 8 horas por dev por día
            hours_per_day = assignment.devs_assigned * 8
            worked_hours = days_elapsed * hours_per_day
            remaining_hours = assignment.estimated_hours - worked_hours

            progress_info = {
                "assignment": assignment,
                "days_elapsed": days_elapsed,
                "total_days": total_days,
                "worked_hours": worked_hours,
                "remaining_hours": remaining_hours,
                "progress_percentage": (worked_hours / assignment.estimated_hours) * 100 if assignment.estimated_hours > 0 else 0
            }
            active_assignments_with_progress.append(progress_info)

    return active_assignments_with_progress


def get_completed_phases() -> Dict[int, date]:
    """
    Recupera las fases que se consideran completadas basándose en el plan activo.
    Una fase se considera "completada" si su fecha de finalización calculada en el plan activo
    es anterior a la fecha actual.

    Returns:
        Un diccionario que mapea el ID de la asignación a su fecha de finalización.
    """
    completed_phases = {}
    active_plan = get_active_plan()
    
    if not active_plan:
        logger.info("No hay un plan activo. No se anclarán fases completadas.")
        return completed_phases

    today = date.today()
    logger.info(f"Buscando fases completadas en el plan activo '{active_plan.name}' (ID: {active_plan.id}) con fecha de hoy: {today}")

    for assignment in active_plan.assignments:
        if assignment.calculated_end_date and assignment.calculated_end_date < today:
            completed_phases[assignment.assignment_id] = assignment.calculated_end_date
    
    if completed_phases:
        logger.info(f"Se encontraron {len(completed_phases)} fases consideradas completadas según el plan activo.")
    else:
        logger.info("No se encontraron fases completadas en el plan activo para la fecha actual.")
        
    return completed_phases