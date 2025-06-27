import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from .scheduler import ProjectScheduler
from ..common.models import Team, Project, Assignment, SimulationInput
from ..common.simulation_data_loader import load_simulation_input_from_db

def render_simulation():
    """Renderiza la interfaz de simulación de scheduling APE"""
    
    st.header("🔬 Simulador de Scheduling APE")
    st.markdown("Simula cronogramas usando **datos reales** de proyectos y equipos con capacidad de modificar prioridades temporalmente.")
    
    render_real_data_simulation()


def render_real_data_simulation():
    """Renderiza simulación con datos reales de la DB con controles de prioridad"""
    
    # 🚀 OPTIMIZACIÓN: Cache de datos iniciales para evitar cargas repetidas
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def load_cached_initial_data():
        return load_simulation_input_from_db(date.today())
    
    # Cargar datos iniciales con cache
    try:
        with st.spinner("Cargando datos desde la base de datos..."):
            initial_data = load_cached_initial_data()
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return
    
    # Verificar que hay datos
    if not initial_data.teams:
        st.error("No hay equipos en la base de datos. Crea equipos primero en la pestaña Teams.")
        return
    
    if not initial_data.projects:
        st.error("No hay proyectos en la base de datos. Crea proyectos primero en la pestaña Projects.")
        return
    
    if not initial_data.assignments:
        st.error("No hay asignaciones en la base de datos. Los proyectos necesitan asignaciones de equipos.")
        return
    
    # Control de prioridades (en memoria)
    st.subheader("🎯 Control de Prioridades (Simulación)")
    st.markdown("**Modifica las prioridades temporalmente para ver el impacto en el cronograma**")
    
    # Crear controles de prioridad
    priority_overrides = {}
    projects_list = list(initial_data.projects.values())
    projects_list.sort(key=lambda p: p.priority)
    
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
    
    # Configuración de simulación
    col1, col2 = st.columns(2)
    with col1:
        sim_start_date = st.date_input(
            "📅 Fecha de inicio de simulación",
            value=date.today(),
            key="real_sim_start"
        )
    
    with col2:
        auto_run = st.checkbox("🔄 Ejecutar automáticamente al cambiar prioridades", value=True)
    
    # 🚀 OPTIMIZACIÓN: Control más inteligente de ejecución automática
    manual_run = st.button("🚀 Ejecutar Simulación", key="run_real_sim")
    
    # Solo ejecutar automáticamente si hay cambios significativos y auto_run está habilitado
    auto_should_run = (auto_run and priority_overrides and 
                      st.session_state.get('last_priority_overrides') != priority_overrides)
    
    run_simulation = manual_run or auto_should_run
    
    # Guardar estado de prioridades para evitar re-ejecuciones innecesarias
    if run_simulation:
        st.session_state['last_priority_overrides'] = priority_overrides.copy()
    
    # Inicializar session state para mantener resultados
    if 'simulation_result' not in st.session_state:
        st.session_state.simulation_result = None
    if 'simulation_input_data' not in st.session_state:
        st.session_state.simulation_input_data = None
    
    if run_simulation:
        try:
            # Aplicar overrides de prioridad
            simulation_input = load_simulation_input_from_db(sim_start_date)
            for project_id, new_priority in priority_overrides.items():
                if project_id in simulation_input.projects:
                    simulation_input.projects[project_id].priority = new_priority
            
            # Ejecutar simulación
            with st.spinner("Ejecutando simulación..."):
                scheduler = ProjectScheduler()
                result = scheduler.simulate(simulation_input)
            
            # Guardar resultados en session state
            st.session_state.simulation_result = result
            st.session_state.simulation_input_data = simulation_input
            
            # Mostrar resultados
            st.success(f"✅ Simulación completada con {len(result.assignments)} asignaciones")
            
        except Exception as e:
            st.error(f"❌ Error ejecutando simulación: {str(e)}")
            st.exception(e)
            st.session_state.simulation_result = None
            st.session_state.simulation_input_data = None
    
    # Mostrar resultados si existen (ya sea de una nueva simulación o de session state)
    if st.session_state.simulation_result is not None and st.session_state.simulation_input_data is not None:
        result = st.session_state.simulation_result
        simulation_input = st.session_state.simulation_input_data
        
        # Métricas generales
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
        
        # Gráfico Gantt mejorado con vistas duales
        st.subheader("📅 Cronograma de Proyectos")
        
        # Control de switch de vista (fuera del bloque de simulación)
        view_type = st.radio(
            "📊 Tipo de Vista",
            options=["detailed", "consolidated"],
            format_func=lambda x: "🔍 Vista Detallada" if x == "detailed" else "📈 Vista Consolidada",
            horizontal=True,
            key="gantt_view_type",
            help="Vista Detallada: Una línea por proyecto-fase | Vista Consolidada: Timeline continuo por proyecto"
        )
        
        # Preparar datos según el tipo de vista seleccionado
        from .gantt_views import prepare_gantt_data, get_project_colors_map, get_gantt_metrics
        from .gantt_config import get_gantt_figure
        
        try:
            # Preparar datos para la vista seleccionada
            gantt_df = prepare_gantt_data(result, view_type, simulation_input)
            
            if not gantt_df.empty:
                # Generar colores apropiados
                project_colors = get_project_colors_map(simulation_input.projects)
                
                # Crear figura del Gantt
                fig = get_gantt_figure(
                    gantt_df, 
                    view_type, 
                    project_colors=project_colors,
                    add_markers=True
                )
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar métricas específicas de la vista
                    metrics = get_gantt_metrics(gantt_df, view_type)
                    if metrics:
                        st.markdown("---")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if view_type == "detailed":
                                st.metric("📋 Tareas Totales", metrics.get("total_tasks", 0))
                            else:
                                st.metric("📋 Proyectos", metrics.get("unique_projects", 0))
                        
                        with col2:
                            if view_type == "detailed":
                                st.metric("👥 Equipos Activos", metrics.get("unique_teams", 0))
                            else:
                                st.metric("🔄 Fases Totales", metrics.get("total_phases", 0))
                        
                        with col3:
                            if view_type == "detailed":
                                st.metric("⏱️ Horas Totales", f"{metrics.get('total_hours', 0):,.0f}")
                            else:
                                avg_duration = metrics.get("avg_project_duration", 0)
                                st.metric("📅 Duración Promedio", f"{avg_duration:.1f} días")
                        
                        with col4:
                            if view_type == "detailed":
                                avg_devs = metrics.get("avg_devs_per_task", 0)
                                st.metric("👨‍💻 Devs Promedio/Tarea", f"{avg_devs:.1f}")
                            else:
                                avg_phases = metrics.get("avg_phases_per_project", 0)
                                st.metric("🔢 Fases Promedio/Proyecto", f"{avg_phases:.1f}")
                else:
                    st.warning("⚠️ No se pudo generar el gráfico Gantt")
            else:
                st.warning("⚠️ No hay datos suficientes para mostrar el cronograma")
                
        except Exception as e:
            st.error(f"❌ Error generando el cronograma: {str(e)}")
            st.exception(e)
        
        # Resultado detallado proyecto por proyecto
        st.subheader("📋 Resultado Detallado por Proyecto")
        
        for project_id, project in sorted(simulation_input.projects.items(), key=lambda x: x[1].priority):
            project_assignments = result.get_assignments_by_project(project_id)
            if not project_assignments:
                continue
            
            with st.expander(f"🏷️ {project.name} (Prioridad {project.priority})", expanded=True):
                # Información del proyecto
                col1, col2, col3 = st.columns(3)
                with col1:
                    project_start = result.get_project_start_date(project_id)
                    if project_start:
                        st.metric("📅 Inicio", project_start.strftime("%Y-%m-%d"))
                    else:
                        st.metric("📅 Inicio", "No calculado")
                
                with col2:
                    project_end = result.get_project_end_date(project_id)
                    if project_end:
                        st.metric("🏁 Fin", project_end.strftime("%Y-%m-%d"))
                    else:
                        st.metric("🏁 Fin", "No calculado")
                
                with col3:
                    if project_start and project_end:
                        duration = (project_end - project_start).days
                        st.metric("⏱️ Duración", f"{duration} días")
                    else:
                        st.metric("⏱️ Duración", "No calculado")
                
                # Estado del proyecto
                if project_end and project.due_date_with_qa:
                    if project_end <= project.due_date_with_qa:
                        st.success(f"✅ A tiempo - Termina {(project.due_date_with_qa - project_end).days} días antes")
                    else:
                        delay_days = (project_end - project.due_date_with_qa).days
                        st.error(f"⚠️ Con retraso - {delay_days} días de retraso")
                
                # Tabla de asignaciones del proyecto
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
    
    # Información sobre la simulación
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