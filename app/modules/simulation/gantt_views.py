"""
Módulo para manejar las diferentes vistas del cronograma de Gantt
Implementa la lógica de transformación de datos para vista detallada y consolidada
"""

import math
import pandas as pd
from datetime import date
from typing import List, Dict, Optional
from ..common.models import Assignment, ScheduleResult, SimulationInput
from ..common.constants import PHASE_ORDER_MAP


# Esquema de colores para las fases (Vista Consolidada)
PHASE_COLORS = {
    "Arch": "#FF6B6B",      # Rojo coral - Arquitectura
    "Devs": "#4ECDC4",      # Turquesa - Desarrollo  
    "Model": "#45B7D1",     # Azul - Modelado
    "Dqa": "#96CEB4"        # Verde - QA
}

# Colores por proyecto (Vista Detallada) - mantener actual
PROJECT_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']


def get_phase_order(team_name: str) -> int:
    """
    Obtiene el orden numérico de la fase para ordenamiento
    
    Args:
        team_name: Nombre del equipo/fase
        
    Returns:
        int: Orden numérico de la fase
    """
    return PHASE_ORDER_MAP.get(team_name, 999)


def validate_phase_sequence(project_assignments: List[Assignment]) -> bool:
    """
    Valida que las fases sigan el orden correcto: Arch → Model → Devs → Dqa
    
    Args:
        project_assignments: Lista de asignaciones de un proyecto
        
    Returns:
        bool: True si la secuencia es válida
    """
    if not project_assignments:
        return True
    
    # Ordenar por fecha de inicio calculada
    sorted_assignments = sorted(
        [a for a in project_assignments if a.calculated_start_date],
        key=lambda x: x.calculated_start_date
    )
    
    # Verificar que el orden de fases sea correcto
    for i in range(len(sorted_assignments) - 1):
        current_phase_order = get_phase_order(sorted_assignments[i].team_name)
        next_phase_order = get_phase_order(sorted_assignments[i + 1].team_name)
        
        if current_phase_order >= next_phase_order:
            return False
    
    return True


def transform_to_detailed_view(assignments: List[Assignment], projects: Dict = None) -> pd.DataFrame:
    """
    Transforma assignments a formato de vista detallada
    
    Args:
        assignments: Lista de asignaciones de la simulación
        
    Returns:
        pd.DataFrame: Datos formateados para vista detallada
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Agregar logs para verificar fechas calculadas
    logger.info("🔍 DEBUG FECHAS CALCULADAS EN ASSIGNMENTS (VISTA DETALLADA):")
    for assignment in assignments:
        if assignment.team_name == "Arch":  # Solo mostrar logs para Arch
            logger.info(f"  - Proyecto {assignment.project_name} (ID: {assignment.project_id}), Equipo {assignment.team_name}:")
            logger.info(f"    * calculated_start_date = {assignment.calculated_start_date}")
            logger.info(f"    * calculated_end_date = {assignment.calculated_end_date}")
    
    gantt_data = []
    
    for assignment in assignments:
        if assignment.calculated_start_date and assignment.calculated_end_date:
            # Obtener la prioridad correcta y el estado del proyecto
            correct_priority = assignment.project_priority  # Fallback
            project_active = True  # Por defecto activo
            
            if projects:
                for proj_id, proj_data in projects.items():
                    if hasattr(proj_data, 'name') and proj_data.name == assignment.project_name:
                        correct_priority = proj_data.priority
                        project_active = proj_data.active if hasattr(proj_data, 'active') else True
                        break
                    elif isinstance(proj_data, dict) and proj_data.get('name') == assignment.project_name:
                        correct_priority = proj_data.get('priority', assignment.project_priority)
                        project_active = proj_data.get('active', True)
                        break
            
            from datetime import timedelta

            start_date = assignment.calculated_start_date
            end_date = assignment.calculated_end_date
            # Display end date + 1 calendar day in hover (cosmetic change)
            end_date_display = end_date + timedelta(days=1)

            hover_text = (
                f"<b>{assignment.project_name} - {assignment.team_name}</b><br>"
                f"Start: {start_date.strftime('%d/%m/%Y')}<br>"
                f"End: {end_date_display.strftime('%d/%m/%Y')}<br>"
                f"Hours: {assignment.estimated_hours}h<br>"
                f"Devs: {assignment.devs_assigned}<br>"
                f"Tier: {assignment.tier}"
            )

            # For Plotly timeline visualization, Finish needs +1 day because it's treated as exclusive
            # This ensures the bar visually spans the entire end_date day
            gantt_data.append({
                "Task": f"{assignment.project_name} - {assignment.team_name}",
                "Start": pd.Timestamp(assignment.calculated_start_date),
                "Finish": pd.Timestamp(assignment.calculated_end_date) + pd.Timedelta(days=1),
                "Project": assignment.project_name,
                "Team": assignment.team_name,
                "Phase": assignment.team_name,  # Para consistencia
                "Priority": correct_priority,  # Usar la prioridad correcta
                "Active": project_active,  # Estado del proyecto
                "Tier": assignment.tier,
                "Devs": assignment.devs_assigned,
                "Hours": assignment.estimated_hours,
                "Resource": f"Tier {assignment.tier} ({assignment.devs_assigned} devs, {assignment.estimated_hours}h)",
                "PhaseOrder": get_phase_order(assignment.team_name),
                "HoverText": hover_text
            })
    
    if not gantt_data:
        return pd.DataFrame()
    
    gantt_df = pd.DataFrame(gantt_data)
    
    # Importar utilidades comunes para prioridad efectiva
    from ..common.priority_utils import get_effective_priority_for_dataframe
    
    # Aplicar lógica de prioridad efectiva: activos primero, luego pausados
    gantt_df['EffectivePriority'] = gantt_df.apply(get_effective_priority_for_dataframe, axis=1)
    
    # Ordenar por prioridad efectiva y luego por orden correcto de fases
    gantt_df = gantt_df.sort_values(['EffectivePriority', 'Project', 'PhaseOrder'])
    
    # Eliminar la columna temporal
    gantt_df = gantt_df.drop('EffectivePriority', axis=1)
    
    return gantt_df


def transform_to_consolidated_view(assignments: List[Assignment], projects: Dict) -> pd.DataFrame:
    """
    Transforma assignments a formato de vista consolidada con timeline continuo
    Una línea por proyecto con fases apiladas en la misma fila
    
    Args:
        assignments: Lista de asignaciones de la simulación
        projects: Diccionario de proyectos
        
    Returns:
        pd.DataFrame: Datos formateados para vista consolidada
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Debug de fechas calculadas en vista consolidada
    logger.info("🔍 DEBUG FECHAS CALCULADAS EN VISTA CONSOLIDADA:")
    for project_id, project in projects.items():
        logger.info(f"  - Proyecto {project.name} (ID: {project_id}) procesado")
    
    gantt_data = []
    
    # Agrupar asignaciones por proyecto
    projects_assignments = {}
    for assignment in assignments:
        if assignment.calculated_start_date and assignment.calculated_end_date:
            project_id = assignment.project_id
            if project_id not in projects_assignments:
                projects_assignments[project_id] = []
            projects_assignments[project_id].append(assignment)
    
    # Procesar cada proyecto
    for project_id, project_assignments in projects_assignments.items():
        # Ordenar fases por orden correcto
        project_assignments.sort(key=lambda x: get_phase_order(x.team_name))
        
        # Validar secuencia de fases
        if not validate_phase_sequence(project_assignments):
            # Secuencia de fases incorrecta detectada
            pass
        
        # Calcular información del proyecto completo
        project_start = min(a.calculated_start_date for a in project_assignments)
        project_end = max(a.calculated_end_date for a in project_assignments)
        # Calculate duration as inclusive calendar days (end - start + 1)
        project_duration = (project_end - project_start).days + 1
        project_name = project_assignments[0].project_name
        project_priority = project_assignments[0].project_priority
        
        # Crear UNA entrada por proyecto con información de todas las fases
        phases_info = []
        total_hours = 0
        total_devs = 0
        
        for assignment in project_assignments:
            # Calculate duration as work days (hours / hours_per_day)
            hours_per_day = assignment.devs_assigned * 8
            phase_duration = math.ceil(assignment.estimated_hours / hours_per_day) if hours_per_day > 0 else 1
            # Calculate calendar days (inclusive)
            phase_calendar_days = (assignment.calculated_end_date - assignment.calculated_start_date).days
            phases_info.append({
                'name': assignment.team_name,
                'start': assignment.calculated_start_date,
                'end': assignment.calculated_end_date,
                'duration': float(phase_duration),
                'calendar_days': float(phase_calendar_days),
                'hours': float(assignment.estimated_hours),
                'devs': float(assignment.devs_assigned),
                'tier': assignment.tier
            })
            total_hours += assignment.estimated_hours
            total_devs += assignment.devs_assigned
        
        # Obtener la prioridad correcta y el estado del diccionario de proyectos
        # Esto corrige la inconsistencia entre assignment.project_priority y projects[].priority
        correct_priority = None
        project_active = True  # Por defecto activo
        for proj_id, proj_data in projects.items():
            if hasattr(proj_data, 'name') and proj_data.name == project_name:
                correct_priority = proj_data.priority
                project_active = proj_data.active if hasattr(proj_data, 'active') else True
                break
            elif isinstance(proj_data, dict) and proj_data.get('name') == project_name:
                correct_priority = proj_data.get('priority')
                project_active = proj_data.get('active', True)
                break
        
        # Si no encontramos la prioridad correcta, usar la de assignment como fallback
        final_priority = correct_priority if correct_priority is not None else project_priority
        
        # Crear texto de hover para vista consolidada
        from datetime import timedelta

        # Display end dates + 1 calendar day (cosmetic change)
        project_end_display = project_end + timedelta(days=1)

        phases_summary = []
        for phase in phases_info:
            phase_end_display = phase['end'] + timedelta(days=1)
            phases_summary.append(
                f"  {phase['name']}: {phase['start'].strftime('%d/%m/%Y')} - {phase_end_display.strftime('%d/%m/%Y')}"
            )

        hover_text = (
            f"<b>📋 {project_name}</b><br>"
            f"Start: {project_start.strftime('%d/%m/%Y')}<br>"
            f"End: {project_end_display.strftime('%d/%m/%Y')}<br>"
            f"Total Hours: {total_hours}h<br>"
            f"Total Devs: {total_devs}<br>"
            f"Phases ({len(project_assignments)}):<br>"
            + "<br>".join(phases_summary)
        )
        
        # Crear entrada consolidada para el proyecto
        # For consolidated view, Finish is used for the dataframe but actual drawing is done in gantt_config.py
        gantt_data.append({
            "Task": f"📋 {project_name}",  # Nombre claro del proyecto
            "Start": pd.Timestamp(project_start),
            "Finish": pd.Timestamp(project_end) + pd.Timedelta(days=1),  # +1 for timeline markers
            "Project": project_name,
            "Priority": final_priority,  # Usar la prioridad correcta
            "Active": project_active,  # Estado del proyecto (activo/pausado)
            "ProjectDuration": project_duration,
            "TotalPhases": len(project_assignments),
            "TotalHours": total_hours,
            "TotalDevs": total_devs,
            "PhasesInfo": phases_info,  # Información detallada de fases
            # Para compatibilidad con el hover
            "Phase": f"{len(project_assignments)} phases",
            "PhaseDuration": project_duration,
            "PhaseHours": total_hours,
            "PhaseDevs": total_devs,
            "HoverText": hover_text
        })
    
    if not gantt_data:
        return pd.DataFrame()
    
    gantt_df = pd.DataFrame(gantt_data)
    
    # Importar utilidades comunes para prioridad efectiva
    from ..common.priority_utils import get_effective_priority_for_dataframe
    
    # Aplicar lógica de prioridad efectiva: activos primero, luego pausados
    gantt_df['EffectivePriority'] = gantt_df.apply(get_effective_priority_for_dataframe, axis=1)
    
    # Ordenar por prioridad efectiva
    gantt_df = gantt_df.sort_values(['EffectivePriority', 'Project'])
    
    # Eliminar la columna temporal
    gantt_df = gantt_df.drop('EffectivePriority', axis=1)
    
    return gantt_df


def prepare_gantt_data(result: ScheduleResult, view_type: str, simulation_input: SimulationInput) -> pd.DataFrame:
    """
    Prepara datos para ambas vistas del Gantt
    
    Args:
        result: Resultado de la simulación
        view_type: "detailed" | "consolidated" 
        simulation_input: Input de la simulación
    
    Returns:
        pd.DataFrame: Datos formateados para Plotly
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Debug básico de proyectos a procesar
    logger.info("🔍 DEBUG PROYECTOS PARA GANTT:")
    for project_id, project in simulation_input.projects.items():
        logger.info(f"  - Procesando proyecto {project.name} (ID: {project_id})")
    
    if view_type == "detailed":
        return transform_to_detailed_view(result.assignments, simulation_input.projects)
    elif view_type == "consolidated":
        return transform_to_consolidated_view(result.assignments, simulation_input.projects)
    else:
        raise ValueError(f"Tipo de vista no válido: {view_type}")


def get_project_colors_map(projects: Dict, color_palette: List[str] = None) -> Dict[str, str]:
    """
    Genera un mapa de colores para proyectos
    
    Args:
        projects: Diccionario de proyectos
        color_palette: Paleta de colores opcional
        
    Returns:
        Dict[str, str]: Mapa de proyecto -> color
    """
    if color_palette is None:
        color_palette = PROJECT_COLORS
    
    project_colors = {}
    for i, (project_id, project) in enumerate(projects.items()):
        project_colors[project.name] = color_palette[i % len(color_palette)]
    
    return project_colors


def get_gantt_metrics(gantt_df: pd.DataFrame, view_type: str) -> Dict[str, any]:
    """
    Calcula métricas específicas para cada vista
    
    Args:
        gantt_df: DataFrame con datos del Gantt
        view_type: Tipo de vista
        
    Returns:
        Dict: Métricas calculadas
    """
    if gantt_df.empty:
        return {}
    
    base_metrics = {
        "total_tasks": len(gantt_df),
        "date_range": {
            "start": gantt_df['Start'].min(),
            "end": gantt_df['Finish'].max()
        }
    }
    
    if view_type == "detailed":
        base_metrics.update({
            "unique_projects": gantt_df['Project'].nunique(),
            "unique_teams": gantt_df['Team'].nunique(),
            "total_hours": gantt_df['Hours'].sum(),
            "avg_devs_per_task": gantt_df['Devs'].mean()
        })
    elif view_type == "consolidated":
        base_metrics.update({
            "unique_projects": gantt_df['Project'].nunique(),
            "avg_project_duration": gantt_df['ProjectDuration'].mean() if 'ProjectDuration' in gantt_df.columns else 0,
            "total_phases": len(gantt_df),
            "avg_phases_per_project": gantt_df['TotalPhases'].mean() if 'TotalPhases' in gantt_df.columns else 0
        })
    
    return base_metrics