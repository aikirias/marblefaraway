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
    st.markdown("Visualiza cómo funciona el algoritmo de scheduling **under the hood** usando la estructura real de APE.")
    
    # Pestañas para diferentes tipos de simulación
    tab1, tab2 = st.tabs(["🎮 Constructor Visual", "🏢 Datos Reales"])
    
    with tab1:
        st.markdown("**Crea casos de prueba personalizados para experimentar**")
        render_visual_builder()
    
    with tab2:
        st.markdown("**Simula usando proyectos y equipos reales de la base de datos**")
        render_real_data_simulation()


def render_visual_builder():
    """Renderiza el constructor visual de casos de prueba"""
    from .test_case_builder import render_test_case_builder
    render_test_case_builder()


def render_real_data_simulation():
    """Renderiza simulación con datos reales de la DB"""
    
    st.subheader("🏢 Simulación con Datos Reales")
    
    # Configuración de simulación
    col1, col2 = st.columns(2)
    with col1:
        sim_start_date = st.date_input(
            "Fecha de inicio de simulación",
            value=date.today(),
            key="real_sim_start"
        )
    
    with col2:
        if st.button("🚀 Ejecutar Simulación con Datos Reales", key="run_real_sim"):
            try:
                # Cargar datos reales
                with st.spinner("Cargando datos desde la base de datos..."):
                    simulation_input = load_simulation_input_from_db(sim_start_date)
                
                # Verificar que hay datos
                if not simulation_input.teams:
                    st.error("No hay equipos en la base de datos. Crea equipos primero en la pestaña Teams.")
                    return
                
                if not simulation_input.projects:
                    st.error("No hay proyectos en la base de datos. Crea proyectos primero en la pestaña Projects.")
                    return
                
                if not simulation_input.assignments:
                    st.error("No hay asignaciones en la base de datos. Los proyectos necesitan asignaciones de equipos.")
                    return
                
                # Ejecutar simulación
                with st.spinner("Ejecutando simulación..."):
                    scheduler = ProjectScheduler()
                    result = scheduler.simulate(simulation_input)
                
                # Mostrar resultados
                st.success(f"✅ Simulación completada con {len(result.assignments)} asignaciones")
                
                # Métricas generales
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📋 Proyectos", len(simulation_input.projects))
                with col2:
                    st.metric("👥 Equipos", len(simulation_input.teams))
                with col3:
                    st.metric("🎯 Asignaciones", len(result.assignments))
                
                # Gráfico Gantt
                st.subheader("📅 Cronograma de Proyectos")
                
                # Preparar datos para Gantt
                gantt_data = []
                for assignment in result.assignments:
                    if assignment.calculated_start_date and assignment.calculated_end_date:
                        gantt_data.append({
                            "Task": f"{assignment.project_name} - {assignment.team_name}",
                            "Start": assignment.calculated_start_date,
                            "Finish": assignment.calculated_end_date,
                            "Project": assignment.project_name,
                            "Team": assignment.team_name,
                            "Priority": assignment.project_priority,
                            "Resource": f"Tier {assignment.tier} ({assignment.devs_assigned} devs)"
                        })
                
                if gantt_data:
                    gantt_df = pd.DataFrame(gantt_data)
                    
                    fig = px.timeline(
                        gantt_df,
                        x_start="Start",
                        x_end="Finish",
                        y="Task",
                        color="Project",
                        title="📅 Cronograma de Proyectos - Datos Reales",
                        hover_data=["Team", "Priority", "Resource"],
                        height=max(400, len(gantt_data) * 25)
                    )
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Resumen por proyecto
                    st.subheader("📊 Resumen por Proyecto")
                    project_summary = []
                    for project_id, project in simulation_input.projects.items():
                        start_date = result.get_project_start_date(project_id)
                        end_date = result.get_project_end_date(project_id)
                        project_assignments = result.get_assignments_by_project(project_id)
                        
                        project_summary.append({
                            "Proyecto": project.name,
                            "Prioridad": project.priority,
                            "Inicio Calculado": start_date.strftime("%Y-%m-%d") if start_date else "N/A",
                            "Fin Calculado": end_date.strftime("%Y-%m-%d") if end_date else "N/A",
                            "Equipos Asignados": len(project_assignments),
                            "Due Date (sin QA)": project.due_date_wo_qa.strftime("%Y-%m-%d"),
                            "Due Date (con QA)": project.due_date_with_qa.strftime("%Y-%m-%d")
                        })
                    
                    summary_df = pd.DataFrame(project_summary)
                    st.dataframe(summary_df, use_container_width=True)
                    
                    # Análisis de cumplimiento
                    st.subheader("⚠️ Análisis de Cumplimiento")
                    delays = []
                    for _, row in summary_df.iterrows():
                        if row["Fin Calculado"] != "N/A":
                            calc_end = pd.to_datetime(row["Fin Calculado"]).date()
                            due_date = pd.to_datetime(row["Due Date (sin QA)"]).date()
                            if calc_end > due_date:
                                delay_days = (calc_end - due_date).days
                                delays.append({
                                    "Proyecto": row["Proyecto"],
                                    "Días de Retraso": delay_days,
                                    "Fin Calculado": row["Fin Calculado"],
                                    "Due Date": row["Due Date (sin QA)"]
                                })
                    
                    if delays:
                        st.warning(f"⚠️ {len(delays)} proyecto(s) con retrasos detectados:")
                        delays_df = pd.DataFrame(delays)
                        st.dataframe(delays_df, use_container_width=True)
                    else:
                        st.success("✅ Todos los proyectos se completarán a tiempo según la simulación")
                
                else:
                    st.warning("No se pudieron calcular fechas para las asignaciones. Revisa la configuración de los proyectos.")
                
            except Exception as e:
                st.error(f"Error en la simulación: {str(e)}")
                st.exception(e)
    
    # Información sobre datos reales
    with st.expander("ℹ️ Información sobre Simulación con Datos Reales"):
        st.markdown("""
        **¿Qué hace esta simulación?**
        
        1. **Carga datos reales** de proyectos, equipos y asignaciones desde la base de datos
        2. **Ejecuta el algoritmo de scheduling** usando la misma lógica que el constructor visual
        3. **Calcula fechas reales** de inicio y fin para cada asignación
        4. **Detecta conflictos** y retrasos potenciales
        5. **Muestra el cronograma** resultante en formato Gantt
        
        **¿Cómo usar los resultados?**
        
        - **Ajusta prioridades** de proyectos si hay retrasos
        - **Modifica asignaciones** de equipos para optimizar tiempos
        - **Cambia fechas** de ready_to_start si hay dependencias
        - **Re-ejecuta la simulación** para ver el impacto de los cambios
        
        **Nota:** Los campos calculados (calculated_start_date, calculated_end_date) 
        son solo para la simulación y NO se guardan en la base de datos.
        """)