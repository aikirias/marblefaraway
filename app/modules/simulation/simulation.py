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
    
    # Cargar datos iniciales
    try:
        with st.spinner("Cargando datos desde la base de datos..."):
            initial_data = load_simulation_input_from_db(date.today())
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
    
    # Ejecutar simulación
    run_simulation = st.button("🚀 Ejecutar Simulación", key="run_real_sim") or (auto_run and priority_overrides)
    
    if run_simulation:
        try:
            # Aplicar overrides de prioridad
            simulation_input = load_simulation_input_from_db(sim_start_date)
            st.write(simulation_input)
            for project_id, new_priority in priority_overrides.items():
                if project_id in simulation_input.projects:
                    simulation_input.projects[project_id].priority = new_priority
            
            # Ejecutar simulación
            with st.spinner("Ejecutando simulación..."):
                scheduler = ProjectScheduler()
                result = scheduler.simulate(simulation_input)
            
            # Mostrar resultados
            st.success(f"✅ Simulación completada con {len(result.assignments)} asignaciones")
            
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
            
            # Gráfico Gantt mejorado
            st.subheader("📅 Cronograma de Proyectos")
            
            # Preparar datos para Gantt con mejor organización
            gantt_data = []
            project_colors = {}
            color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
            
            for i, (project_id, project) in enumerate(simulation_input.projects.items()):
                project_colors[project.name] = color_palette[i % len(color_palette)]
            
            for assignment in result.assignments:
                if assignment.calculated_start_date and assignment.calculated_end_date:
                    gantt_data.append({
                        "Task": f"{assignment.project_name} - {assignment.team_name}",
                        "Start": pd.Timestamp(assignment.calculated_start_date),
                        "Finish": pd.Timestamp(assignment.calculated_end_date),
                        "Project": assignment.project_name,
                        "Team": assignment.team_name,
                        "Priority": assignment.project_priority,
                        "Tier": assignment.tier,
                        "Devs": assignment.devs_assigned,
                        "Hours": assignment.estimated_hours,
                        "Resource": f"Tier {assignment.tier} ({assignment.devs_assigned} devs, {assignment.estimated_hours}h)"
                    })
            
            if gantt_data:
                gantt_df = pd.DataFrame(gantt_data)
                
                # Ordenar por prioridad y luego por orden correcto de fases: Arch → Devs → Model → Dqa
                def get_phase_order(team_name):
                    phase_order = {"Arch": 1, "Devs": 2, "Model": 3, "Dqa": 4}
                    return phase_order.get(team_name, 999)
                
                gantt_df['PhaseOrder'] = gantt_df['Team'].apply(get_phase_order)
                gantt_df = gantt_df.sort_values(['Priority', 'Project', 'PhaseOrder'])
                
                fig = px.timeline(
                    gantt_df,
                    x_start="Start",
                    x_end="Finish",
                    y="Task",
                    color="Project",
                    title="📅 Cronograma de Proyectos - Orden: Arch → Devs → Model → Dqa",
                    hover_data=["Team", "Priority", "Tier", "Devs", "Hours"],
                    height=max(500, len(gantt_data) * 35),
                    color_discrete_map=project_colors
                )
                
                # Mejorar el diseño del Gantt
                fig.update_yaxes(autorange="reversed", title="Proyectos y Fases")
                fig.update_xaxes(title="Cronograma", showgrid=True)
                fig.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=250, r=50, t=100, b=50),
                    plot_bgcolor='white'
                )
                
                # Agregar líneas verticales mejoradas para mejor legibilidad
                min_date = gantt_df['Start'].min()
                max_date = gantt_df['Finish'].max()
                
                # # Líneas verticales para inicio de mes (más prominentes)
                # month_range = pd.date_range(start=min_date.replace(day=1), end=max_date, freq='MS')
                # for month_start in month_range:
                #     fig.add_vline(
                #         x=month_start.to_pydatetime(), 
                #         line_dash="solid", 
                #         line_color="gray", 
                #         line_width=2,
                #         opacity=0.8,
                #         annotation_text=month_start.strftime("%b %Y"),
                #         annotation_position="top",
                #         annotation_font_size=10
                #     )
                
                # # Líneas verticales para inicio de semana (más sutiles)
                # week_range = pd.date_range(start=min_date, end=max_date, freq='W-MON')
                # for week_start in week_range:
                #     if week_start.day != 1:  # No duplicar con inicio de mes
                #         fig.add_vline(
                #             x=week_start.to_pydatetime(), 
                #             line_dash="dot", 
                #             line_color="lightgray", 
                #             line_width=1,
                #             opacity=0.5
                #         )
                
                # # Línea vertical para "hoy" si está en el rango
                # today = date.today()
                # if min_date.date() <= today <= max_date.date():
                #     fig.add_vline(
                #         x=today, 
                #         line_dash="dash", 
                #         line_color="red", 
                #         line_width=2,
                #         opacity=0.9,
                #         annotation_text="HOY",
                #         annotation_position="top",
                #         annotation_font_color="red",
                #         annotation_font_size=12
                #     )
                
                st.plotly_chart(fig, use_container_width=True)
                
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
                            start_date = result.get_project_start_date(project_id)
                            st.metric("📅 Inicio", start_date.strftime("%Y-%m-%d") if start_date else "N/A")
                        with col2:
                            end_date = result.get_project_end_date(project_id)
                            st.metric("🏁 Fin", end_date.strftime("%Y-%m-%d") if end_date else "N/A")
                        with col3:
                            if start_date and end_date:
                                duration = (end_date - start_date).days + 1
                                st.metric("⏱️ Duración", f"{duration} días")
                        
                        # Detalle por fase
                        st.markdown("**📊 Detalle por Fase:**")
                        phase_data = []
                        for assignment in sorted(project_assignments, key=lambda a: a.team_name):
                            phase_data.append({
                                "Equipo": assignment.team_name,
                                "Tier": assignment.tier,
                                "Devs": assignment.devs_assigned,
                                "Horas": assignment.estimated_hours,
                                "Inicio": assignment.calculated_start_date.strftime("%Y-%m-%d") if assignment.calculated_start_date else "N/A",
                                "Fin": assignment.calculated_end_date.strftime("%Y-%m-%d") if assignment.calculated_end_date else "N/A",
                                "Estado": assignment.status
                            })
                        
                        if phase_data:
                            phase_df = pd.DataFrame(phase_data)
                            st.dataframe(phase_df, use_container_width=True, hide_index=True)
                        
                        # Análisis de cumplimiento del proyecto
                        if end_date:
                            if end_date <= project.due_date_wo_qa:
                                st.success(f"✅ Proyecto se completará a tiempo (Due: {project.due_date_wo_qa.strftime('%Y-%m-%d')})")
                            else:
                                delay_days = (end_date - project.due_date_wo_qa).days
                                st.error(f"⚠️ Proyecto se retrasará {delay_days} días (Due: {project.due_date_wo_qa.strftime('%Y-%m-%d')})")
                
                # Resumen ejecutivo
                st.subheader("📊 Resumen Ejecutivo")
                project_summary = []
                total_delays = 0
                for project_id, project in simulation_input.projects.items():
                    start_date = result.get_project_start_date(project_id)
                    end_date = result.get_project_end_date(project_id)
                    project_assignments = result.get_assignments_by_project(project_id)
                    
                    delay_days = 0
                    status = "✅ A tiempo"
                    if end_date and end_date > project.due_date_wo_qa:
                        delay_days = (end_date - project.due_date_wo_qa).days
                        total_delays += delay_days
                        status = f"⚠️ {delay_days} días de retraso"
                    
                    project_summary.append({
                        "Proyecto": project.name,
                        "Prioridad": project.priority,
                        "Inicio": start_date.strftime("%Y-%m-%d") if start_date else "N/A",
                        "Fin": end_date.strftime("%Y-%m-%d") if end_date else "N/A",
                        "Due Date": project.due_date_wo_qa.strftime("%Y-%m-%d"),
                        "Estado": status,
                        "Fases": len(project_assignments)
                    })
                
                summary_df = pd.DataFrame(project_summary)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                # Métricas finales
                col1, col2, col3 = st.columns(3)
                with col1:
                    on_time = len([p for p in project_summary if "A tiempo" in p["Estado"]])
                    st.metric("✅ Proyectos a Tiempo", on_time)
                with col2:
                    delayed = len([p for p in project_summary if "retraso" in p["Estado"]])
                    st.metric("⚠️ Proyectos con Retraso", delayed)
                with col3:
                    st.metric("📅 Total Días de Retraso", total_delays)
            
            else:
                st.warning("No se pudieron calcular fechas para las asignaciones. Revisa la configuración de los proyectos.")
                
        except Exception as e:
            st.error(f"Error en la simulación: {str(e)}")
            st.exception(e)
    
    # Información sobre la simulación
    with st.expander("ℹ️ Cómo usar la Simulación"):
        st.markdown("""
        **🎯 Control de Prioridades:**
        - Modifica las prioridades de los proyectos usando los controles numéricos
        - Los cambios son **temporales** y NO se guardan en la base de datos
        - Prioridad 1 = más alta, números mayores = menor prioridad
        
        **📅 Cronograma Gantt:**
        - Cada color representa un proyecto diferente
        - Las líneas grises separan proyectos para mejor legibilidad
        - Hover sobre las barras para ver detalles (tier, devs, horas)
        
        **📋 Resultado Detallado:**
        - Expandir cada proyecto para ver el detalle fase por fase
        - Verde = proyecto a tiempo, Rojo = proyecto con retraso
        - Fechas calculadas consideran dependencias y capacidad de equipos
        
        **🔄 Simulación en Tiempo Real:**
        - Activa "Ejecutar automáticamente" para ver cambios inmediatos
        - Experimenta con diferentes prioridades para optimizar cronogramas
        - Los resultados muestran el impacto real de las decisiones de priorización
        """)
    
    # Mostrar cambios aplicados
    if priority_overrides:
        st.info(f"🔄 **Cambios aplicados:** {len(priority_overrides)} proyecto(s) con prioridad modificada temporalmente")