"""
Módulo de Proyectos Activos para APE
Identifica y muestra proyectos que están siendo trabajados activamente hoy
"""

import streamlit as st
import pandas as pd
from datetime import date
from typing import List, Dict, Optional
import logging
import math

from ..common.models import Project, Assignment, Team
from ..common.simulation_data_loader import load_simulation_input_from_db
from ..simulation.scheduler import ProjectScheduler
from ..common.date_utils import calculate_business_days

logger = logging.getLogger(__name__)


def render_active_projects():
    """Renderiza la interfaz de proyectos activos"""
    logger.info("🔍 DEBUG: INICIANDO render_active_projects()")
    st.header("🚀 Proyectos Activos")
    st.markdown("Proyectos que están siendo trabajados activamente hoy")
    
    try:
        # Cargar datos de simulación
        logger.info("🔍 DEBUG: Cargando datos de simulación...")
        simulation_input = load_simulation_input_from_db(date.today())
        if not simulation_input:
            logger.error("🚨 ERROR: No se pudieron cargar datos de simulación")
            st.error("Error cargando datos de simulación")
            return
        
        logger.info(f"🔍 DEBUG: Datos cargados - {len(simulation_input.projects)} proyectos, {len(simulation_input.teams)} equipos")
        
        # Ejecutar simulación para obtener asignaciones actuales
        scheduler = ProjectScheduler()
        try:
            with st.spinner("Calculando proyectos activos..."):
                logger.info("🔍 DEBUG: Ejecutando simulación...")
                result = scheduler.simulate(simulation_input)
                logger.info(f"🔍 DEBUG: Simulación completada - {len(result.assignments)} asignaciones")
        except Exception as e:
            logger.error(f"🚨 ERROR ejecutando simulación: {str(e)}")
            st.error(f"Error ejecutando simulación: {str(e)}")
            return
        
        # Identificar proyectos activos
        logger.info("🔍 DEBUG: Identificando proyectos activos...")
        active_projects_data = _identify_active_projects(
            result, simulation_input.projects, simulation_input.teams, date.today()
        )
        
        logger.info(f"🔍 DEBUG: Proyectos activos encontrados: {len(active_projects_data)}")
        
        if not active_projects_data:
            logger.info("🔍 DEBUG: No hay proyectos activos para hoy")
            st.info("No hay proyectos activos para la fecha de hoy")
            return
        
        # Renderizar tabla de proyectos activos
        logger.info("🔍 DEBUG: Renderizando tabla de proyectos activos...")
        _render_active_projects_table(active_projects_data)
        
        # Renderizar métricas adicionales
        logger.info("🔍 DEBUG: Renderizando métricas adicionales...")
        _render_active_projects_metrics(active_projects_data)
        
        logger.info("🔍 DEBUG: render_active_projects() completado exitosamente")
        
    except Exception as e:
        logger.error(f"🚨 ERROR en render_active_projects(): {str(e)}")
        logger.error(f"🚨 ERROR tipo: {type(e).__name__}")
        import traceback
        logger.error(f"🚨 ERROR traceback: {traceback.format_exc()}")
        st.error(f"Error en módulo de proyectos activos: {str(e)}")


def _identify_active_projects(result, projects: Dict[int, Project], teams: Dict[int, Team], today: date) -> List[Dict]:
    """
    Identifica proyectos que tienen asignaciones activas para la fecha actual
    
    Args:
        result: Resultado de la simulación con asignaciones calculadas
        projects: Diccionario de proyectos
        teams: Diccionario de equipos
        today: Fecha actual
    
    Returns:
        Lista de diccionarios con información de proyectos activos
    """
    logger.info(f"🔍 DEBUG _identify_active_projects: Fecha de hoy: {today}")
    logger.info(f"🔍 DEBUG _identify_active_projects: Total asignaciones: {len(result.assignments)}")
    
    active_projects = []
    
    # Agrupar asignaciones por proyecto
    project_assignments = {}
    for assignment in result.assignments:
        if assignment.project_id not in project_assignments:
            project_assignments[assignment.project_id] = []
        project_assignments[assignment.project_id].append(assignment)
    
    # Verificar cada proyecto
    for project_id, assignments in project_assignments.items():
        project = projects.get(project_id)
        if not project:
            continue
        
        # Verificar si tiene asignaciones activas hoy
        active_assignments = []
        logger.info(f"🔍 DEBUG: Verificando proyecto {project.name} (ID: {project_id})")
        for assignment in assignments:
            logger.info(f"🔍 DEBUG: Asignación - start: {assignment.calculated_start_date}, end: {assignment.calculated_end_date}, today: {today}")
            if (assignment.calculated_start_date and assignment.calculated_end_date and
                assignment.calculated_start_date <= today <= assignment.calculated_end_date):
                active_assignments.append(assignment)
                logger.info(f"🔍 DEBUG: ✅ Asignación activa encontrada para proyecto {project.name}")
        
        logger.info(f"🔍 DEBUG: Proyecto {project.name} tiene {len(active_assignments)} asignaciones activas")
        
        # Si tiene asignaciones activas, incluir en la lista
        if active_assignments:
            project_data = _calculate_project_data(
                project, assignments, active_assignments, teams, today
            )
            active_projects.append(project_data)
    
    # Ordenar por prioridad
    active_projects.sort(key=lambda x: x['priority'])
    return active_projects


def _calculate_project_data(project: Project, all_assignments: List[Assignment], 
                          active_assignments: List[Assignment], teams: Dict[int, Team], 
                          today: date) -> Dict:
    """
    Calcula datos completos para un proyecto activo
    
    Args:
        project: Proyecto
        all_assignments: Todas las asignaciones del proyecto
        active_assignments: Asignaciones activas hoy
        teams: Diccionario de equipos
        today: Fecha actual
    
    Returns:
        Diccionario con datos del proyecto
    """
    # Calcular fechas del proyecto
    start_dates = [a.calculated_start_date for a in all_assignments 
                  if a.calculated_start_date is not None]
    end_dates = [a.calculated_end_date for a in all_assignments 
                if a.calculated_end_date is not None]
    
    project_start = min(start_dates) if start_dates else None
    project_end = max(end_dates) if end_dates else None
    
    # Calcular horas estimadas por fase
    phase_hours = {}
    for assignment in all_assignments:
        team = teams.get(assignment.team_id)
        if team:
            phase_name = team.name
            hours_needed = assignment.get_hours_needed(team)
            if phase_name not in phase_hours:
                phase_hours[phase_name] = 0
            phase_hours[phase_name] += hours_needed
    
    # Calcular horas trabajadas hasta hoy
    hours_worked = _calculate_hours_worked(project, all_assignments, today)
    
    # Calcular horas trabajadas por fase
    phase_hours_worked = _calculate_hours_worked_by_phase(all_assignments, teams, today)
    
    # Determinar estado de cada fase
    phase_states = _calculate_phase_states(all_assignments, teams, today)
    
    # Calcular total de horas estimadas
    total_estimated_hours = sum(phase_hours.values())
    
    # Equipos trabajando hoy
    active_teams = [teams[a.team_id].name for a in active_assignments if a.team_id in teams]
    
    return {
        'project_id': project.id,
        'project_name': project.name,
        'priority': project.priority,
        'fecha_inicio_real': project.fecha_inicio_real,
        'project_start': project_start,
        'project_end': project_end,
        'due_date_with_qa': project.due_date_with_qa,
        'phase_hours': phase_hours,
        'phase_hours_worked': phase_hours_worked,
        'total_estimated_hours': total_estimated_hours,
        'hours_worked': hours_worked,
        'phase_states': phase_states,
        'active_teams': active_teams,
        'active_assignments_count': len(active_assignments)
    }


def _calculate_hours_worked(project: Project, assignments: List[Assignment], today: date) -> int:
    """
    Calcula horas trabajadas desde fecha_inicio_real hasta hoy, considerando múltiples desarrolladores
    
    Args:
        project: Proyecto
        assignments: Asignaciones del proyecto
        today: Fecha actual
    
    Returns:
        Horas trabajadas (estimadas basadas en días hábiles y desarrolladores asignados)
    """
    if not project.fecha_inicio_real:
        return 0
    
    # Si el proyecto no ha empezado aún
    if project.fecha_inicio_real > today:
        return 0
    
    # Calcular días hábiles trabajados
    business_days_worked = calculate_business_days(project.fecha_inicio_real, today)
    
    # Estimar horas trabajadas basándose en asignaciones que ya deberían haber empezado
    hours_worked = 0
    for assignment in assignments:
        if (assignment.calculated_start_date and 
            assignment.calculated_start_date <= today):
            
            # Obtener número de desarrolladores asignados (mínimo 1)
            devs_assigned = max(1, assignment.devs_assigned or 1)
            
            # Si la asignación ya terminó, contar todas las horas multiplicadas por desarrolladores
            if (assignment.calculated_end_date and 
                assignment.calculated_end_date <= today):
                assignment_hours = (assignment.pending_hours or 0) * devs_assigned
                hours_worked += assignment_hours
                logger.debug(f"Asignación completada - Proyecto: {assignment.project_name}, Equipo: {assignment.team_name}, "
                           f"Horas base: {assignment.pending_hours}, Devs: {devs_assigned}, Horas totales: {assignment_hours}")
            else:
                # Si está en progreso, calcular proporcionalmente y multiplicar por desarrolladores
                if assignment.calculated_end_date:
                    total_days = calculate_business_days(
                        assignment.calculated_start_date, 
                        assignment.calculated_end_date
                    )
                    days_worked = calculate_business_days(
                        assignment.calculated_start_date, 
                        today
                    )
                    if total_days > 0:
                        proportion = min(1.0, days_worked / total_days)
                        assignment_hours = (assignment.pending_hours or 0) * proportion * devs_assigned
                        hours_worked += int(assignment_hours)
    
    return hours_worked


def _calculate_phase_states(assignments: List[Assignment], teams: Dict[int, Team], today: date) -> Dict[str, str]:
    """
    Calcula el estado actual de cada fase
    
    Args:
        assignments: Asignaciones del proyecto
        teams: Diccionario de equipos
        today: Fecha actual
    
    Returns:
        Diccionario con estado de cada fase
    """
    phase_states = {}
    
    for assignment in assignments:
        team = teams.get(assignment.team_id)
        if not team:
            continue
        
        phase_name = team.name
        
        if not assignment.calculated_start_date or not assignment.calculated_end_date:
            phase_states[phase_name] = "⏳ Pendiente"
        elif today < assignment.calculated_start_date:
            phase_states[phase_name] = "⏳ Pendiente"
        elif today > assignment.calculated_end_date:
            phase_states[phase_name] = "✅ Completada"
        else:
            phase_states[phase_name] = "🔄 En Progreso"
    
    return phase_states


def _calculate_hours_worked_by_phase(assignments: List[Assignment], teams: Dict[int, Team], today: date) -> Dict[str, int]:
    """
    Calcula horas trabajadas por fase individual, considerando múltiples desarrolladores y redondeando hacia arriba en múltiplos de 8
    
    Args:
        assignments: Asignaciones del proyecto
        teams: Diccionario de equipos
        today: Fecha actual
    
    Returns:
        Diccionario con horas trabajadas por fase
    """
    phase_hours_worked = {}
    
    for assignment in assignments:
        team = teams.get(assignment.team_id)
        if not team:
            continue
        
        phase_name = team.name
        
        if phase_name not in phase_hours_worked:
            phase_hours_worked[phase_name] = 0
        
        # Calcular horas trabajadas para esta asignación específica
        hours_worked = 0
        
        if (assignment.calculated_start_date and 
            assignment.calculated_start_date <= today):
            
            # Obtener número de desarrolladores asignados (mínimo 1)
            devs_assigned = max(1, assignment.devs_assigned or 1)
            
            # Si la asignación ya terminó, contar todas las horas multiplicadas por desarrolladores
            if (assignment.calculated_end_date and 
                assignment.calculated_end_date <= today):
                hours_worked = (assignment.pending_hours or 0) * devs_assigned
            else:
                # Si está en progreso, calcular proporcionalmente y multiplicar por desarrolladores
                if assignment.calculated_end_date:
                    total_days = calculate_business_days(
                        assignment.calculated_start_date, 
                        assignment.calculated_end_date
                    )
                    days_worked = calculate_business_days(
                        assignment.calculated_start_date, 
                        today
                    )
                    if total_days > 0:
                        proportion = min(1.0, days_worked / total_days)
                        hours_worked = (assignment.pending_hours or 0) * proportion * devs_assigned
        
        # Redondear hacia arriba en múltiplos de 8
        if hours_worked > 0:
            hours_worked_rounded = math.ceil(hours_worked / 8) * 8
            phase_hours_worked[phase_name] += hours_worked_rounded
    
    return phase_hours_worked


def _render_active_projects_table(active_projects_data: List[Dict]):
    """Renderiza tabla de proyectos activos"""
    st.subheader("📊 Proyectos Activos Hoy")
    
    # Preparar datos para la tabla
    table_data = []
    for project_data in active_projects_data:
        # Formatear equipos activos
        active_teams_str = ", ".join(project_data['active_teams'])
        
        # Formatear fechas
        fecha_inicio_real = project_data['fecha_inicio_real'].strftime("%Y-%m-%d") if project_data['fecha_inicio_real'] else "No definida"
        project_start = project_data['project_start'].strftime("%Y-%m-%d") if project_data['project_start'] else "No calculado"
        project_end = project_data['project_end'].strftime("%Y-%m-%d") if project_data['project_end'] else "No calculado"
        due_date = project_data['due_date_with_qa'].strftime("%Y-%m-%d") if project_data['due_date_with_qa'] else "No definida"
        
        # Calcular progreso
        total_hours = project_data['total_estimated_hours']
        worked_hours = project_data['hours_worked']
        progress_pct = (worked_hours / total_hours * 100) if total_hours > 0 else 0
        
        table_data.append({
            "Proyecto": project_data['project_name'],
            "Prioridad": project_data['priority'],
            "Fecha Inicio Real": fecha_inicio_real,
            "Inicio Calculado": project_start,
            "Fin Estimado": project_end,
            "Fecha Límite": due_date,
            "Horas Estimadas": total_hours,
            "Horas Trabajadas": worked_hours,
            "Progreso": f"{progress_pct:.1f}%",
            "Equipos Activos": active_teams_str
        })
    
    # Mostrar tabla
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)
    
    # Mostrar detalles de fases para cada proyecto
    st.subheader("🔍 Estado Detallado por Fases")
    
    logger.info(f"🔍 DEBUG: Número de proyectos activos: {len(active_projects_data)}")
    
    for project_data in active_projects_data:
        logger.info(f"🔍 DEBUG: Procesando proyecto {project_data['project_name']}")
        with st.expander(f"📋 {project_data['project_name']} (Prioridad {project_data['priority']})"):
            _render_project_phase_details(project_data)


def _render_project_phase_details(project_data: Dict):
    """Renderiza detalles de fases para un proyecto con información mejorada"""
    logger.info(f"🔍 DEBUG: INICIANDO _render_project_phase_details para {project_data['project_name']}")
    st.markdown("**📊 Progreso Detallado por Fases:**")
    
    # Debug: Verificar que tenemos los datos necesarios
    logger.info(f"🔍 DEBUG project_data keys: {project_data.keys()}")
    logger.info(f"🔍 DEBUG phase_hours: {project_data.get('phase_hours', {})}")
    logger.info(f"🔍 DEBUG phase_hours_worked: {project_data.get('phase_hours_worked', {})}")
    logger.info(f"🔍 DEBUG phase_states: {project_data.get('phase_states', {})}")
    
    # Obtener todas las fases del proyecto
    all_phases = set(project_data['phase_hours'].keys()) | set(project_data['phase_states'].keys())
    
    for phase in sorted(all_phases):
        estimated_hours = project_data['phase_hours'].get(phase, 0)
        worked_hours = project_data['phase_hours_worked'].get(phase, 0)
        state = project_data['phase_states'].get(phase, "⏳ Pendiente")
        
        # Calcular progreso y horas faltantes
        remaining_hours = max(0, estimated_hours - worked_hours)
        progress_pct = (worked_hours / estimated_hours * 100) if estimated_hours > 0 else 0
        
        # Generar texto según el estado
        if "Completada" in state:
            phase_text = f"• {phase}: ✅ Completada ({worked_hours}/{estimated_hours} horas)"
        elif "En Progreso" in state:
            phase_text = f"• {phase}: 🔄 En Progreso ({worked_hours}/{estimated_hours} horas - {progress_pct:.1f}%) - Faltan {remaining_hours} horas"
        else:  # Pendiente
            phase_text = f"• {phase}: ⏳ Pendiente ({worked_hours}/{estimated_hours} horas) - Faltan {remaining_hours} horas"
        
        st.write(phase_text)
        logger.info(f"🔍 DEBUG: Fase {phase}: {phase_text}")
    
    # Mostrar resumen adicional
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        total_estimated = sum(project_data['phase_hours'].values())
        total_worked = sum(project_data['phase_hours_worked'].values())
        st.metric("Total Estimado", f"{total_estimated:,} horas")
    
    with col2:
        overall_progress = (total_worked / total_estimated * 100) if total_estimated > 0 else 0
        st.metric("Progreso General", f"{overall_progress:.1f}%")
    
    logger.info(f"🔍 DEBUG: _render_project_phase_details completado para {project_data['project_name']}")


def _render_active_projects_metrics(active_projects_data: List[Dict]):
    """Renderiza métricas adicionales de proyectos activos"""
    st.subheader("📈 Métricas de Proyectos Activos")
    
    # Calcular métricas
    total_projects = len(active_projects_data)
    total_estimated_hours = sum(p['total_estimated_hours'] for p in active_projects_data)
    total_worked_hours = sum(p['hours_worked'] for p in active_projects_data)
    
    # Contar fases en progreso
    phases_in_progress = 0
    phases_completed = 0
    phases_pending = 0
    
    for project_data in active_projects_data:
        for state in project_data['phase_states'].values():
            if "En Progreso" in state:
                phases_in_progress += 1
            elif "Completada" in state:
                phases_completed += 1
            elif "Pendiente" in state:
                phases_pending += 1
    
    # Mostrar métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🚀 Proyectos Activos", total_projects)
    
    with col2:
        st.metric("⏱️ Horas Estimadas", f"{total_estimated_hours:,}")
    
    with col3:
        st.metric("✅ Horas Trabajadas", f"{total_worked_hours:,}")
    
    with col4:
        progress_pct = (total_worked_hours / total_estimated_hours * 100) if total_estimated_hours > 0 else 0
        st.metric("📊 Progreso General", f"{progress_pct:.1f}%")
    
    with col5:
        st.metric("🔄 Fases en Progreso", phases_in_progress)
    
    # Gráfico de distribución de estados de fases
    if phases_in_progress + phases_completed + phases_pending > 0:
        st.markdown("---")
        st.subheader("📊 Distribución de Estados de Fases")
        
        phase_distribution = {
            "En Progreso": phases_in_progress,
            "Completadas": phases_completed,
            "Pendientes": phases_pending
        }
        
        # Crear DataFrame para el gráfico
        df_phases = pd.DataFrame(list(phase_distribution.items()), columns=['Estado', 'Cantidad'])
        
        # Mostrar como gráfico de barras
        st.bar_chart(df_phases.set_index('Estado'))