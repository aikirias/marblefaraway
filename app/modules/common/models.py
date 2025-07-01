"""
Modelos de datos unificados para el sistema APE
Versión refactorizada con código limpio y métodos optimizados
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Optional


@dataclass
class Team:
    """Equipo con capacidad real de la aplicación APE"""
    id: int
    name: str
    total_devs: int
    busy_devs: int = 0
    tier_capacities: Dict[int, int] = None
    
    def __post_init__(self):
        if self.tier_capacities is None:
            self.tier_capacities = {}
    
    def get_available_devs(self) -> int:
        """Devs disponibles para asignación"""
        return max(0, self.total_devs - self.busy_devs)
    
    def get_hours_per_person_for_tier(self, tier: int) -> int:
        """Horas por persona para un tier específico"""
        return self.tier_capacities.get(tier, 0)


@dataclass
class Project:
    """Proyecto con estructura simplificada APE"""
    id: int
    name: str
    priority: int
    start_date: date
    due_date_wo_qa: date
    due_date_with_qa: date
    phase: str = "draft"
    active: bool = True
    horas_trabajadas: int = 0
    horas_totales_estimadas: int = 0
    fecha_inicio_real: Optional[date] = None
    
    # Campo calculado (NO va a DB)
    total_hours_remaining: int = 0
    
    def is_active(self) -> bool:
        """Verifica si el proyecto está activo"""
        return self.active
    
    def get_state_display(self) -> str:
        """Retorna estado legible para UI"""
        return "🟢 Activo" if self.active else "⏸️ Inactivo"
    
    def get_state_color(self) -> str:
        """Retorna color para UI según estado"""
        return "#28a745" if self.active else "#6c757d"
    
    def get_horas_faltantes(self) -> int:
        """Calcula las horas faltantes del proyecto"""
        if self.horas_totales_estimadas <= 0:
            return 0
        return max(0, self.horas_totales_estimadas - self.horas_trabajadas)
    
    def get_progreso_porcentaje(self) -> float:
        """Calcula el porcentaje de progreso del proyecto"""
        if self.horas_totales_estimadas <= 0:
            return 0.0
        progreso = (self.horas_trabajadas / self.horas_totales_estimadas) * 100
        return min(100.0, progreso)
    
    def get_progreso_display(self) -> str:
        """Retorna texto de progreso para mostrar en UI"""
        if self.horas_totales_estimadas <= 0:
            return "Sin estimación"
        porcentaje = self.get_progreso_porcentaje()
        return f"{porcentaje:.1f}% ({self.horas_trabajadas}/{self.horas_totales_estimadas}h)"
    
    def get_progreso_color(self) -> str:
        """Retorna color para barra de progreso según porcentaje"""
        porcentaje = self.get_progreso_porcentaje()
        if porcentaje >= 90:
            return "#28a745"  # Verde - casi completo
        elif porcentaje >= 70:
            return "#ffc107"  # Amarillo - en progreso avanzado
        elif porcentaje >= 30:
            return "#17a2b8"  # Azul - en progreso
        else:
            return "#dc3545"  # Rojo - poco progreso


@dataclass
class Assignment:
    """Asignación real de equipo a proyecto"""
    id: int
    project_id: int
    project_name: str
    project_priority: int
    team_id: int
    team_name: str
    tier: int
    devs_assigned: float
    max_devs: float
    estimated_hours: int
    ready_to_start_date: date
    assignment_start_date: date
    status: str = "Not Started"
    custom_estimated_hours: Optional[int] = None
    
    # Campos calculados por la simulación (NO van a DB)
    calculated_start_date: Optional[date] = None
    calculated_end_date: Optional[date] = None
    pending_hours: int = 0
    paused_on: Optional[date] = None
    
    def get_hours_needed(self, team: Team) -> int:
        """Calcula horas totales necesarias basado en tier y devs asignados"""
        # Si hay horas estimadas personalizadas, usarlas
        if self.custom_estimated_hours is not None:
            return int(self.custom_estimated_hours * self.devs_assigned)
        
        # Sino, usar el tier para calcular
        hours_per_person = team.get_hours_per_person_for_tier(self.tier)
        if hours_per_person == 0:
            return self.estimated_hours
        return int(hours_per_person * self.devs_assigned)
    
    def can_start_on(self, target_date: date) -> bool:
        """Verifica si puede empezar en la fecha objetivo"""
        return target_date >= self.ready_to_start_date


@dataclass
class ScheduleResult:
    """Resultado de la simulación"""
    assignments: List[Assignment]
    project_summaries: List[Dict]
    
    def get_project_end_date(self, project_id: int) -> Optional[date]:
        """Fecha de fin del proyecto (última asignación)"""
        project_assignments = [a for a in self.assignments if a.project_id == project_id]
        if not project_assignments:
            return None
        
        end_dates = [a.calculated_end_date for a in project_assignments 
                    if a.calculated_end_date is not None]
        return max(end_dates) if end_dates else None
    
    def get_project_start_date(self, project_id: int) -> Optional[date]:
        """Fecha de inicio del proyecto (primera asignación)"""
        project_assignments = [a for a in self.assignments if a.project_id == project_id]
        if not project_assignments:
            return None
        
        start_dates = [a.calculated_start_date for a in project_assignments 
                      if a.calculated_start_date is not None]
        return min(start_dates) if start_dates else None
    
    def get_assignments_by_team(self, team_id: int) -> List[Assignment]:
        """Asignaciones de un equipo específico"""
        return [a for a in self.assignments if a.team_id == team_id]
    
    def get_assignments_by_project(self, project_id: int) -> List[Assignment]:
        """Asignaciones de un proyecto específico"""
        return [a for a in self.assignments if a.project_id == project_id]


@dataclass
class SimulationInput:
    """Input completo para la simulación"""
    teams: Dict[int, Team]
    projects: Dict[int, Project]
    assignments: List[Assignment]
    simulation_start_date: date = None
    
    def __post_init__(self):
        if self.simulation_start_date is None:
            self.simulation_start_date = date.today()