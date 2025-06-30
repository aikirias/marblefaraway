"""
Simulación de scheduling APE - Versión refactorizada
Eliminado código DEBUG y simplificadas las funciones complejas
"""

import streamlit as st
import pandas as pd
from datetime import date
from .scheduler import ProjectScheduler
from ..common.models import SimulationInput
from ..common.simulation_data_loader import load_simulation_input_from_db


def render_simulation():
    """Renderiza la interfaz de simulación de scheduling APE"""
    st.header("🔬 Simulador de Scheduling APE")
    st.markdown("Simula cronogramas usando **datos reales** de proyectos y equipos con capacidad de modificar prioridades temporalmente.")
    
    render_real_data_simulation()


def render_real_data_simulation():
    """Renderiza simulación con datos reales de la DB con controles de prioridad"""
    initial_data = _load_initial_data()
    if not initial_data:
        return
    
    if not _validate_data(initial_data):
        return
    
    # Control de prioridades y configuración
    priority_overrides = _render_priority_controls(initial_data)
    sim_start_date, auto_run = _render_simulation_config()
    
    # Determinar si ejecutar simulación
    should_run = _should_run_simulation(priority_overrides, auto_run)
    
    if should_run:
        _execute_simulation(initial_data, priority_overrides, sim_start_date)
    
    # Mostrar resultados si existen
    _render_simulation_results(priority_overrides)
    
    # Información de ayuda
    _render_help_section()


# ============================================================================
# FUNCIONES PRIVADAS DE UTILIDAD
# ============================================================================

def _load_initial_data():
    """Carga datos iniciales desde la base de datos"""
    try:
        with st.spinner("Cargando datos desde la base de datos..."):
            initial_data = load_simulation_input_from_db(date.today())
            
            if initial_data is None:
                st.error("Error: No se pudieron cargar los datos desde la base de datos")
                return None
            
            return initial_data
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return None


def _validate_data(initial_data):
    """Valida que los datos necesarios estén presentes"""
    if not initial_data.teams:
        st.error("No hay equipos en la base de datos. Crea equipos primero en la pestaña Teams.")
        return False
    
    if not initial_data.projects:
        st.error("No hay proyectos en la base de datos. Crea proyectos primero en la pestaña Projects.")
        return False
    
    if not initial_data.assignments:
        st.error("No hay asignaciones en la base de datos. Los proyectos necesitan asignaciones de equipos.")
        return False
    
    return True


def _render_priority_controls(initial_data):
    """Renderiza controles de prioridad para proyectos"""
    st.subheader("🎯 Control de Prioridades (Simulación)")
    st.markdown("**Modifica las prioridades temporalmente para ver el impacto en el cronograma**")
    
    priority_overrides = {}
    projects_list = sorted(initial_data.projects.values(), key=lambda p: p.priority)
    
    cols = st.columns(min(3, len(projects_list)))
    for i, project in enumerate(projects_list):
        with cols[i % len(cols)]:
            new_priority = st.number_input(
                f"🏷️ {project.name}",
                min_value=1,
                max_value=10,
                value=project.priority,
                key=f"priority_{project.id}"
            )
            if new_priority != project.priority:
                priority_overrides[project.id] = new_priority
    
    return priority_overrides


def _render_simulation_config():
    """Renderiza configuración de simulación"""
    col1, col2 = st.columns(2)
    
    with col1:
        sim_start_date = st.date_input(
            "📅 Fecha de inicio de simulación",
            value=date.today(),
            key="real_sim_start"
        )
    
    with col2:
        auto_run = st.checkbox("🔄 Ejecutar automáticamente al cambiar prioridades", value=True)
    
    return sim_start_date, auto_run


def _should_run_simulation(priority_overrides, auto_run):
    """Determina si debe ejecutarse la simulación"""
    manual_run = st.button("🚀 Ejecutar Simulación", key="run_real_sim")
    
    # Detectar cambios en prioridades
    last_overrides = st.session_state.get('last_priority_overrides', {})
    priorities_changed = priority_overrides != last_overrides
    
    # Ejecutar si es manual o automático con cambios
    should_run = manual_run or (auto_run and priorities_changed)
    
    if should_run:
        st.session_state['last_priority_overrides'] = priority_overrides.copy()
    
    return should_run


def _execute_simulation(initial_data, priority_overrides, sim_start_date):
    """Ejecuta la simulación con los parámetros dados"""
    try:
        # Preparar datos de simulación
        simulation_input = load_simulation_input_from_db(sim_start_date)
        
        # Aplicar overrides de prioridad
        _apply_priority_overrides(simulation_input, priority_overrides)
        
        # Ejecutar simulación
        with st.spinner("Ejecutando simulación..."):
            scheduler = ProjectScheduler()
            result = scheduler.simulate(simulation_input)
        
        # Guardar resultados
        st.session_state.simulation_result = result
        st.session_state.simulation_input_data = simulation_input
        
        st.success(f"✅ Simulación completada con {len(result.assignments)} asignaciones")
        
    except Exception as e:
        st.error(f"❌ Error ejecutando simulación: {str(e)}")
        st.session_state.simulation_result = None
        st.session_state.simulation_input_data = None


def _apply_priority_overrides(simulation_input, priority_overrides):
    """Aplica los cambios de prioridad a los datos de simulación"""
    for project_id, new_priority in priority_overrides.items():
        if project_id in simulation_input.projects:
            # Actualizar prioridad en project
            simulation_input.projects[project_id].priority = new_priority
            
            # Actualizar project_priority en assignments
            for assignment in simulation_input.assignments:
                if assignment.project_id == project_id:
                    assignment.project_priority = new_priority


def _render_simulation_results(priority_overrides):
    """Renderiza los resultados de la simulación"""
    if not hasattr(st.session_state, 'simulation_result') or st.session_state.simulation_result is None:
        return
    
    result = st.session_state.simulation_result
    simulation_input = st.session_state.simulation_input_data
    
    _render_metrics(simulation_input, result, priority_overrides)
    _render_gantt_chart(result, simulation_input)
    _render_detailed_results(result, simulation_input)


def _render_metrics(simulation_input, result, priority_overrides):
    """Renderiza métricas generales de la simulación"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Proyectos", len(simulation_input.projects))
    with col2:
        st.metric("👥 Equipos", len(simulation_input.teams))
    with col3:
        st.metric("🎯 Asignaciones", len(result.assignments))
    with col4:
        changes = len(priority_overrides)
        st.metric("🔄 Cambios de Prioridad", changes, delta=changes if changes > 0 else None)


def _render_gantt_chart(result, simulation_input):
    """Renderiza el gráfico Gantt con vistas duales"""
    st.subheader("📅 Cronograma de Proyectos")
    
    # Control de vista
    view_type = st.radio(
        "📊 Tipo de Vista",
        options=["detailed", "consolidated"],
        format_func=lambda x: "🔍 Vista Detallada" if x == "detailed" else "📈 Vista Consolidada",
        horizontal=True,
        key="gantt_view_type",
        help="Vista Detallada: Una línea por proyecto-fase | Vista Consolidada: Timeline continuo por proyecto"
    )
    
    try:
        from .gantt_views import prepare_gantt_data, get_project_colors_map, get_gantt_metrics
        from .gantt_config import get_gantt_figure
        
        # Preparar y mostrar datos
        gantt_df = prepare_gantt_data(result, view_type, simulation_input)
        
        if not gantt_df.empty:
            project_colors = get_project_colors_map(simulation_input.projects)
            fig = get_gantt_figure(gantt_df, view_type, project_colors=project_colors, add_markers=True)
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                _render_gantt_metrics(gantt_df, view_type)
            else:
                st.warning("⚠️ No se pudo generar el gráfico Gantt")
        else:
            st.warning("⚠️ No hay datos suficientes para mostrar el cronograma")
            
    except Exception as e:
        st.error(f"❌ Error generando el cronograma: {str(e)}")


def _render_gantt_metrics(gantt_df, view_type):
    """Renderiza métricas específicas del Gantt"""
    from .gantt_views import get_gantt_metrics
    
    metrics = get_gantt_metrics(gantt_df, view_type)
    if not metrics:
        return
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    if view_type == "detailed":
        with col1:
            st.metric("📋 Tareas Totales", metrics.get("total_tasks", 0))
        with col2:
            st.metric("👥 Equipos Activos", metrics.get("unique_teams", 0))
        with col3:
            st.metric("⏱️ Horas Totales", f"{metrics.get('total_hours', 0):,.0f}")
        with col4:
            avg_devs = metrics.get("avg_devs_per_task", 0)
            st.metric("👨‍💻 Devs Promedio/Tarea", f"{avg_devs:.1f}")
    else:
        with col1:
            st.metric("📋 Proyectos", metrics.get("unique_projects", 0))
        with col2:
            st.metric("🔄 Fases Totales", metrics.get("total_phases", 0))
        with col3:
            avg_duration = metrics.get("avg_project_duration", 0)
            st.metric("📅 Duración Promedio", f"{avg_duration:.1f} días")
        with col4:
            avg_phases = metrics.get("avg_phases_per_project", 0)
            st.metric("🔢 Fases Promedio/Proyecto", f"{avg_phases:.1f}")


def _render_detailed_results(result, simulation_input):
    """Renderiza resultados detallados por proyecto"""
    st.subheader("📋 Resultado Detallado por Proyecto")
    
    for project_id, project in sorted(simulation_input.projects.items(), key=lambda x: x[1].priority):
        project_assignments = result.get_assignments_by_project(project_id)
        if not project_assignments:
            continue
        
        with st.expander(f"🏷️ {project.name} (Prioridad {project.priority})", expanded=True):
            _render_project_details(result, project, project_id, project_assignments)


def _render_project_details(result, project, project_id, project_assignments):
    """Renderiza detalles de un proyecto específico"""
    # Métricas del proyecto
    col1, col2, col3 = st.columns(3)
    
    project_start = result.get_project_start_date(project_id)
    project_end = result.get_project_end_date(project_id)
    
    with col1:
        start_text = project_start.strftime("%Y-%m-%d") if project_start else "No calculado"
        st.metric("📅 Inicio", start_text)
    
    with col2:
        end_text = project_end.strftime("%Y-%m-%d") if project_end else "No calculado"
        st.metric("🏁 Fin", end_text)
    
    with col3:
        if project_start and project_end:
            duration = (project_end - project_start).days
            st.metric("⏱️ Duración", f"{duration} días")
        else:
            st.metric("⏱️ Duración", "No calculado")
    
    # Estado del proyecto
    if project_end and project.due_date_with_qa:
        if project_end <= project.due_date_with_qa:
            days_early = (project.due_date_with_qa - project_end).days
            st.success(f"✅ A tiempo - Termina {days_early} días antes")
        else:
            delay_days = (project_end - project.due_date_with_qa).days
            st.error(f"⚠️ Con retraso - {delay_days} días de retraso")
    
    # Tabla de asignaciones
    assignment_data = []
    for assignment in sorted(project_assignments, key=lambda x: x.calculated_start_date or date.min):
        assignment_data.append({
            "Equipo": assignment.team_name,
            "Inicio": assignment.calculated_start_date.strftime("%Y-%m-%d") if assignment.calculated_start_date else "No calculado",
            "Fin": assignment.calculated_end_date.strftime("%Y-%m-%d") if assignment.calculated_end_date else "No calculado",
            "Devs": assignment.devs_assigned,
            "Horas": assignment.estimated_hours,
            "Tier": assignment.tier
        })
    
    if assignment_data:
        st.dataframe(pd.DataFrame(assignment_data), use_container_width=True)


def _render_help_section():
    """Renderiza sección de ayuda"""
    with st.expander("ℹ️ Cómo usar la Simulación"):
        st.markdown("""
        **🎯 Control de Prioridades:**
        - Modifica las prioridades de los proyectos usando los controles numéricos
        - Los cambios son temporales y solo afectan la simulación
        - Prioridad 1 = Más alta, Prioridad 10 = Más baja
        
        **📅 Cronograma de Gantt:**
        - **Vista Detallada**: Muestra una línea por cada proyecto-fase
        - **Vista Consolidada**: Muestra un timeline continuo por proyecto con fases en colores
        - Usa el switch para alternar entre vistas
        - Los resultados se mantienen al cambiar de vista
        
        **🔄 Ejecución Automática:**
        - Si está habilitada, la simulación se ejecuta automáticamente al cambiar prioridades
        - Si está deshabilitada, usa el botón "Ejecutar Simulación" manualmente
        
        **📊 Métricas:**
        - Las métricas cambian según la vista seleccionada
        - Vista detallada: enfoque en tareas y equipos
        - Vista consolidada: enfoque en proyectos y fases
        """)