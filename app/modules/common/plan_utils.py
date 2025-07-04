"""
Utilidades para el manejo de planes
"""

import logging
from datetime import date
from typing import List, Dict, Any

from .models import Plan, PlanAssignment

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
        if assignment.calculated_start_date <= current_date <= assignment.calculated_end_date:
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