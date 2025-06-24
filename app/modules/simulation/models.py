"""
Modelos simples para la simulación de scheduling
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Optional


@dataclass
class Assignment:
    """Asignación de equipo a proyecto"""
    project_id: int
    project_name: str
    phase: str
    phase_order: int
    team_id: int
    priority: int
    devs_assigned: float
    hours_needed: int
    ready_date: date
    
    # Calculados por la simulación
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@dataclass
class Team:
    """Equipo con capacidad"""
    id: int
    name: str
    total_devs: int
    busy_devs: int = 0


@dataclass
class ScheduleResult:
    """Resultado de la simulación"""
    assignments: List[Assignment]
    project_summaries: List[Dict]
    
    def get_project_end_date(self, project_id: int) -> Optional[date]:
        """Fecha de fin del proyecto"""
        project_assignments = [a for a in self.assignments if a.project_id == project_id]
        if not project_assignments:
            return None
        return max(a.end_date for a in project_assignments if a.end_date)