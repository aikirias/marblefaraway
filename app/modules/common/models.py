"""
Modelos de datos unificados para el sistema APE
Versión refactorizada con código limpio y métodos optimizados
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, TYPE_CHECKING
import hashlib
import json

if TYPE_CHECKING:
    from .assignments_crud import Assignment


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
    active: bool = True
    fecha_inicio_real: Optional[date] = None
    
    # Campos calculados dinámicamente (NO van a DB)
    _assignments: List['Assignment'] = field(default_factory=list)
    
    def is_active(self) -> bool:
        """Verifica si el proyecto está activo"""
        return self.active
    
    def get_state_display(self) -> str:
        """Retorna estado legible para UI"""
        return "🟢 Activo" if self.active else "⏸️ Inactivo"
    
    def get_state_color(self) -> str:
        """Retorna color para UI según estado"""
        return "#28a745" if self.active else "#6c757d"
    
    def get_horas_totales_estimadas(self) -> int:
        """Calcula horas totales estimadas desde assignments"""
        if not self._assignments:
            return 0
        return sum(a.estimated_hours for a in self._assignments)
    
    def get_horas_trabajadas(self) -> int:
        """Calcula horas trabajadas desde assignments (simulado)"""
        # Por ahora retornamos 0, se puede implementar lógica de tracking real
        return 0
    
    def get_horas_faltantes(self) -> int:
        """Calcula las horas faltantes del proyecto"""
        total = self.get_horas_totales_estimadas()
        trabajadas = self.get_horas_trabajadas()
        if total <= 0:
            return 0
        return max(0, total - trabajadas)
    
    def get_progreso_porcentaje(self) -> float:
        """Calcula el porcentaje de progreso del proyecto"""
        total = self.get_horas_totales_estimadas()
        trabajadas = self.get_horas_trabajadas()
        if total <= 0:
            return 0.0
        progreso = (trabajadas / total) * 100
        return min(100.0, progreso)
    
    def get_progreso_display(self) -> str:
        """Retorna texto de progreso para mostrar en UI"""
        total = self.get_horas_totales_estimadas()
        trabajadas = self.get_horas_trabajadas()
        if total <= 0:
            return "Sin estimación"
        porcentaje = self.get_progreso_porcentaje()
        return f"{porcentaje:.1f}% ({trabajadas}/{total}h)"
    
    def set_assignments(self, assignments: List['Assignment']):
        """Establece los assignments para cálculos dinámicos"""
        self._assignments = assignments
    
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
    
    def get_hours_needed(self, team: Team) -> int:
        """Calcula horas totales necesarias basado en tier y devs asignados"""
        # Si hay horas estimadas personalizadas, usarlas directamente
        # custom_estimated_hours ya representa el total de horas para esta fase
        if self.custom_estimated_hours is not None:
            return int(self.custom_estimated_hours)
        
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
    
    # Campos para sistema de planes
    checksum: str = ""
    has_changes: bool = True
    
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


@dataclass
class Plan:
    """Plan persistente - snapshot de un resultado de simulación"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    checksum: str = ""
    created_at: Optional[datetime] = None
    is_active: bool = False
    simulation_date: date = None
    total_assignments: int = 0
    total_projects: int = 0
    
    # Assignments del plan (cargados dinámicamente)
    assignments: List['PlanAssignment'] = field(default_factory=list)
    
    def __post_init__(self):
        if self.simulation_date is None:
            self.simulation_date = date.today()
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def calculate_checksum(self, assignments: List[Assignment]) -> str:
        """
        Calcula checksum SHA-256 basado en el contenido de las asignaciones
        Usa assignment_id + fechas calculadas para detectar cambios
        """
        if not assignments:
            return hashlib.sha256("empty".encode()).hexdigest()
        
        # Crear estructura ordenada para hash consistente
        assignment_data = []
        for assignment in sorted(assignments, key=lambda a: a.id):
            data = {
                'assignment_id': assignment.id,
                'project_id': assignment.project_id,
                'team_id': assignment.team_id,
                'calculated_start_date': assignment.calculated_start_date.isoformat() if assignment.calculated_start_date else None,
                'calculated_end_date': assignment.calculated_end_date.isoformat() if assignment.calculated_end_date else None,
                'pending_hours': assignment.pending_hours,
                'devs_assigned': float(assignment.devs_assigned)
            }
            assignment_data.append(data)
        
        # Convertir a JSON ordenado y calcular hash
        json_str = json.dumps(assignment_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    @classmethod
    def from_schedule_result(cls, result: ScheduleResult, name: str = "", description: str = "") -> 'Plan':
        """Crea un Plan desde un ScheduleResult"""
        plan = cls(
            name=name or f"Plan {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=description,
            simulation_date=date.today(),
            total_assignments=len(result.assignments),
            total_projects=len(set(a.project_id for a in result.assignments))
        )
        
        # Calcular checksum
        plan.checksum = plan.calculate_checksum(result.assignments)
        
        return plan


@dataclass
class PlanAssignment:
    """Asignación dentro de un plan - snapshot de Assignment calculado"""
    id: Optional[int] = None
    plan_id: int = 0
    assignment_id: int = 0
    project_id: int = 0
    project_name: str = ""
    project_priority: int = 0
    priority_order: Optional[int] = None  # Prioridad específica del plan
    team_id: int = 0
    team_name: str = ""
    tier: int = 0
    devs_assigned: float = 0.0
    estimated_hours: int = 0
    calculated_start_date: date = None
    calculated_end_date: date = None
    pending_hours: int = 0
    ready_to_start_date: date = None
    
    def __post_init__(self):
        if self.calculated_start_date is None:
            self.calculated_start_date = date.today()
        if self.calculated_end_date is None:
            self.calculated_end_date = date.today()
        if self.ready_to_start_date is None:
            self.ready_to_start_date = date.today()
    
    @classmethod
    def from_assignment(cls, assignment: Assignment, plan_id: int, priority_order: Optional[int] = None) -> 'PlanAssignment':
        """Crea un PlanAssignment desde un Assignment calculado"""
        return cls(
            plan_id=plan_id,
            assignment_id=assignment.id,
            project_id=assignment.project_id,
            project_name=assignment.project_name,
            project_priority=assignment.project_priority,
            priority_order=priority_order or assignment.project_priority,
            team_id=assignment.team_id,
            team_name=assignment.team_name,
            tier=assignment.tier,
            devs_assigned=assignment.devs_assigned,
            estimated_hours=assignment.estimated_hours,
            calculated_start_date=assignment.calculated_start_date,
            calculated_end_date=assignment.calculated_end_date,
            pending_hours=assignment.pending_hours,
            ready_to_start_date=assignment.ready_to_start_date
        )
    
    def get_duration_days(self) -> int:
        """Calcula la duración en días de la asignación"""
        if not self.calculated_start_date or not self.calculated_end_date:
            return 0
        return (self.calculated_end_date - self.calculated_start_date).days + 1