from typing import Optional
from .models import Project
class ProjectStateManager:
    """Gestor de estados y transiciones de proyectos"""
    
    def __init__(self):
        pass
    
    def activate_project(self, project: Project, actual_start_date: Optional[date] = None) -> bool:
        """
        Activa un proyecto desde estado borrador
        
        Args:
            project: Proyecto a activar
            actual_start_date: Fecha real de activación (default: hoy)
        
        Returns:
            bool: True si la activación fue exitosa
        """
        if not project.is_draft():
            raise ValueError(f"Solo se pueden activar proyectos en borrador. Estado actual: {project.phase}")
        
        # Establecer fecha de activación real
        if actual_start_date is None:
            actual_start_date = date.today()
        
        project.phase = 'active'
        project.active = True  # Sincronizar campo booleano
        project.start_date = actual_start_date
        project.actual_start_date = actual_start_date
        
        # Actualizar en base de datos
        update_project(project)
        
        return True
    
    def pause_project(self, project: Project, assignments: List[Assignment], pause_date: Optional[date] = None) -> bool:
        """
        Pausa un proyecto activo preservando el progreso
        
        Args:
            project: Proyecto a pausar
            assignments: Asignaciones del proyecto
            pause_date: Fecha de pausa (default: hoy)
        
        Returns:
            bool: True si la pausa fue exitosa
        """
        if not project.is_active():
            raise ValueError(f"Solo se pueden pausar proyectos activos. Estado actual: {project.phase}")
        
        if pause_date is None:
            pause_date = date.today()
        
        # Cambiar estado del proyecto
        project.phase = 'paused'
        project.active = False  # Sincronizar campo booleano
        update_project(project)
        
        # Pausar todas las asignaciones del proyecto
        for assignment in assignments:
            if assignment.status not in ['Completed', 'Paused']:
                assignment.paused_on = pause_date
                assignment.status = 'Paused'
                update_assignment(assignment)
        
        return True
    
    def reactivate_project(self, project: Project, assignments: List[Assignment]) -> bool:
        """
        Reactiva un proyecto pausado manteniendo el progreso
        
        Args:
            project: Proyecto a reactivar
            assignments: Asignaciones del proyecto
        
        Returns:
            bool: True si la reactivación fue exitosa
        """
        if not project.is_paused():
            raise ValueError(f"Solo se pueden reactivar proyectos pausados. Estado actual: {project.phase}")
        
        # Cambiar estado del proyecto
        project.phase = 'active'
        project.active = True  # Sincronizar campo booleano
        update_project(project)
        
        # Reactivar asignaciones pausadas
        for assignment in assignments:
            if assignment.status == 'Paused' and assignment.paused_on is not None:
                assignment.paused_on = None
                assignment.status = 'In Progress' if assignment.pending_hours > 0 else 'Not Started'
                update_assignment(assignment)
        
        return True