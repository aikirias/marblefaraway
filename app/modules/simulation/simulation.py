import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from .scheduler import ProjectScheduler
from .models import Team, Assignment

def render_simulation():
    """Renderiza la interfaz de simulación de scheduling APE"""
    
    st.header("🔬 Simulador de Scheduling APE")
    st.markdown("Visualiza cómo funciona el algoritmo de scheduling **under the hood** y experimenta con escenarios what-if.")
    
    # Sidebar para controles
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Fecha de inicio
        start_date = st.date_input(
            "📅 Fecha de inicio",
            value=datetime(2025, 6, 16),
            help="Fecha de inicio de la simulación"
        )
        
        st.subheader("👥 Capacidad de Equipos")
        
        # Controles de equipos
        arch_total = st.slider("Arch - Total devs", 1, 5, 2)
        arch_busy = st.slider("Arch - Devs ocupados", 0, arch_total, 0)
        
        model_total = st.slider("Model - Total devs", 1, 8, 4)
        model_busy = st.slider("Model - Devs ocupados", 0, model_total, 0)
        
        devs_total = st.slider("Devs - Total devs", 1, 10, 6)
        devs_busy = st.slider("Devs - Devs ocupados", 0, devs_total, 1)
        
        dqa_total = st.slider("Dqa - Total devs", 1, 6, 3)
        dqa_busy = st.slider("Dqa - Devs ocupados", 0, dqa_total, 0)
        
        st.subheader("🎯 Prioridades")
        
        # Controles de prioridades
        alpha_priority = st.selectbox("Alpha prioridad", [1, 2, 3], index=0)
        beta_priority = st.selectbox("Beta prioridad", [1, 2, 3], index=1)
        gamma_priority = st.selectbox("Gamma prioridad", [1, 2, 3], index=2)
    
    # Crear datos de simulación
    teams = {
        1: Team(id=1, name="Arch", total_devs=arch_total, busy_devs=arch_busy),
        2: Team(id=2, name="Model", total_devs=model_total, busy_devs=model_busy),
        3: Team(id=3, name="Devs", total_devs=devs_total, busy_devs=devs_busy),
        4: Team(id=4, name="Dqa", total_devs=dqa_total, busy_devs=dqa_busy)
    }
    
    assignments = [
        # Alpha
        Assignment(project_id=1, project_name="Alpha", phase="Arch", phase_order=0,
                  team_id=1, priority=alpha_priority, devs_assigned=1, hours_needed=16,
                  ready_date=start_date),
        Assignment(project_id=1, project_name="Alpha", phase="Model", phase_order=1,
                  team_id=2, priority=alpha_priority, devs_assigned=1, hours_needed=56,
                  ready_date=start_date),
        Assignment(project_id=1, project_name="Alpha", phase="Devs", phase_order=2,
                  team_id=3, priority=alpha_priority, devs_assigned=1, hours_needed=40,
                  ready_date=start_date),
        Assignment(project_id=1, project_name="Alpha", phase="Dqa", phase_order=3,
                  team_id=4, priority=alpha_priority, devs_assigned=1, hours_needed=24,
                  ready_date=start_date),
        
        # Beta
        Assignment(project_id=2, project_name="Beta", phase="Arch", phase_order=0,
                  team_id=1, priority=beta_priority, devs_assigned=1, hours_needed=16,
                  ready_date=start_date),
        Assignment(project_id=2, project_name="Beta", phase="Model", phase_order=1,
                  team_id=2, priority=beta_priority, devs_assigned=1, hours_needed=56,
                  ready_date=start_date),
        Assignment(project_id=2, project_name="Beta", phase="Devs", phase_order=2,
                  team_id=3, priority=beta_priority, devs_assigned=1, hours_needed=40,
                  ready_date=start_date),
        Assignment(project_id=2, project_name="Beta", phase="Dqa", phase_order=3,
                  team_id=4, priority=beta_priority, devs_assigned=1, hours_needed=24,
                  ready_date=start_date),
        
        # Gamma (sin Dqa)
        Assignment(project_id=3, project_name="Gamma", phase="Arch", phase_order=0,
                  team_id=1, priority=gamma_priority, devs_assigned=1, hours_needed=8,
                  ready_date=start_date),
        Assignment(project_id=3, project_name="Gamma", phase="Model", phase_order=1,
                  team_id=2, priority=gamma_priority, devs_assigned=1, hours_needed=28,
                  ready_date=start_date),
        Assignment(project_id=3, project_name="Gamma", phase="Devs", phase_order=2,
                  team_id=3, priority=gamma_priority, devs_assigned=1, hours_needed=20,
                  ready_date=start_date),
    ]
    
    # Ejecutar simulación
    scheduler = ProjectScheduler()
    result = scheduler.simulate(assignments, teams, today=start_date)
    
    # Layout en columnas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Datos de Entrada")
        
        # Tabla de equipos
        st.write("**Equipos:**")
        teams_df = pd.DataFrame([
            {
                "Equipo": team.name,
                "Total": team.total_devs,
                "Ocupados": team.busy_devs,
                "Disponibles": team.total_devs - team.busy_devs
            }
            for team in teams.values()
        ])
        st.dataframe(teams_df, use_container_width=True)
        
        # Tabla de asignaciones
        st.write("**Asignaciones:**")
        assignments_df = pd.DataFrame([
            {
                "Proyecto": a.project_name,
                "Fase": a.phase,
                "Prioridad": a.priority,
                "Horas": a.hours_needed
            }
            for a in assignments
        ])
        st.dataframe(assignments_df, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Resultados")
        
        if result.assignments:
            # Cronograma
            schedule_df = pd.DataFrame([
                {
                    "Proyecto": item.project_name,
                    "Fase": item.phase,
                    "Inicio": item.start_date.strftime("%Y-%m-%d"),
                    "Fin": item.end_date.strftime("%Y-%m-%d"),
                    "Días": (item.end_date - item.start_date).days + 1,
                    "Devs": item.devs_assigned
                }
                for item in result.assignments
            ])
            st.dataframe(schedule_df, use_container_width=True)
            
            # Métricas
            total_days = max((item.end_date - min(s.start_date for s in result.assignments)).days 
                           for item in result.assignments) + 1
            st.metric("📊 Duración Total", f"{total_days} días")
            st.metric("📈 Asignaciones", len(result.assignments))
        else:
            st.warning("No se pudieron programar las asignaciones")
    
    # Visualizaciones
    st.subheader("📊 Visualizaciones")
    
    if result.assignments:
        # Gráfico de Gantt
        gantt_data = []
        colors = {"Alpha": "#FF6B6B", "Beta": "#4ECDC4", "Gamma": "#45B7D1"}
        
        for item in result.assignments:
            gantt_data.append({
                "Task": f"{item.project_name}-{item.phase}",
                "Start": item.start_date,
                "Finish": item.end_date,
                "Project": item.project_name,
                "Resource": f"{item.devs_assigned} dev(s)"
            })
        
        gantt_df = pd.DataFrame(gantt_data)
        
        fig = px.timeline(
            gantt_df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Project",
            color_discrete_map=colors,
            title="📅 Cronograma de Proyectos (Gantt)",
            hover_data=["Resource"]
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de utilización por equipo
        utilization_data = []
        for team in teams.values():
            team_assignments = [item for item in result.assignments if item.phase == team.name]
            if team_assignments:
                max_concurrent = max(
                    sum(1 for item in team_assignments 
                        if item.start_date <= date.date() <= item.end_date)
                    for date in pd.date_range(
                        min(item.start_date for item in team_assignments),
                        max(item.end_date for item in team_assignments)
                    )
                )
                utilization = (max_concurrent / team.total_devs) * 100
            else:
                utilization = 0
            
            utilization_data.append({
                "Equipo": team.name,
                "Utilización %": utilization,
                "Capacidad": team.total_devs,
                "Ocupados": team.busy_devs
            })
        
        util_df = pd.DataFrame(utilization_data)
        
        fig2 = px.bar(
            util_df,
            x="Equipo",
            y="Utilización %",
            title="📈 Utilización Máxima por Equipo",
            color="Utilización %",
            color_continuous_scale="RdYlGn_r"
        )
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Under the Hood
    st.subheader("🔍 Under the Hood")
    
    with st.expander("Ver estructuras internas del algoritmo"):
        st.write("**Proceso paso a paso:**")
        
        if hasattr(result, 'debug_info') and result.debug_info:
            for step in result.debug_info:
                st.write(f"• {step}")
        else:
            st.write("Información de debug no disponible en esta versión")
        
        st.write("**Estructuras de memoria:**")
        st.code("""
# active_by_team: Tracking de asignaciones activas por equipo
active_by_team = {
    "Arch": [("Alpha", "2025-06-16", "2025-06-17")],
    "Model": [("Alpha", "2025-06-18", "2025-06-24")],
    "Devs": [],
    "Dqa": []
}

# project_next_free: Cuándo puede continuar cada proyecto
project_next_free = {
    "Alpha": "2025-06-18",  # Después de Arch
    "Beta": "2025-06-18",   # Después de Arch
    "Gamma": "2025-06-16"   # Puede empezar inmediatamente
}
        """, language="python")
    
    # Análisis What-If
    st.subheader("🎲 Análisis What-If")
    
    st.info("""
    **Experimenta con los controles del sidebar:**
    
    🔄 **Cambiar Prioridades**: ¿Qué pasa si Beta tiene prioridad 1?
    
    👥 **Ajustar Capacidad**: ¿Cómo afecta reducir Arch a 1 dev?
    
    ⏰ **Modificar Ocupación**: ¿Qué impacto tiene tener 2 devs ocupados en Model?
    
    📊 **Observar Paralelismo**: Nota cómo Alpha-Arch y Beta-Arch ejecutan simultáneamente
    """)