"""
Demo de Streamlit para visualizar el módulo de simulación
Ejecutar: streamlit run modules/simulation/streamlit_demo.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import json

from .scheduler import ProjectScheduler
from .models import Assignment, Team


def create_sample_data():
    """Crea datos de prueba para la demo"""
    
    # Equipos de ejemplo
    teams = {
        1: Team(id=1, name="Arch", total_devs=2, busy_devs=0),
        2: Team(id=2, name="Model", total_devs=4, busy_devs=0),
        3: Team(id=3, name="Devs", total_devs=6, busy_devs=1),  # 1 dev ocupado
        4: Team(id=4, name="Dqa", total_devs=3, busy_devs=0)
    }
    
    # Proyectos de ejemplo
    base_date = date(2025, 6, 16)
    
    assignments = [
        # Proyecto Alpha (Prioridad 1)
        Assignment(1, "Alpha", "Arch", 0, 1, 1, 1, 16, base_date),
        Assignment(1, "Alpha", "Model", 1, 2, 1, 1, 40, base_date),
        Assignment(1, "Alpha", "Devs", 2, 3, 1, 2, 80, base_date),
        Assignment(1, "Alpha", "Dqa", 3, 4, 1, 1, 24, base_date),
        
        # Proyecto Beta (Prioridad 2)
        Assignment(2, "Beta", "Arch", 0, 1, 2, 1, 32, base_date),
        Assignment(2, "Beta", "Model", 1, 2, 2, 1, 80, base_date),
        Assignment(2, "Beta", "Devs", 2, 3, 2, 1, 40, base_date),
        Assignment(2, "Beta", "Dqa", 3, 4, 2, 1, 16, base_date),
        
        # Proyecto Gamma (Prioridad 3)
        Assignment(3, "Gamma", "Arch", 0, 1, 3, 1, 24, base_date + timedelta(days=7)),
        Assignment(3, "Gamma", "Model", 1, 2, 3, 2, 120, base_date + timedelta(days=7)),
        Assignment(3, "Gamma", "Devs", 2, 3, 3, 3, 120, base_date + timedelta(days=7)),
    ]
    
    return assignments, teams


def render_simulation_demo():
    """Página principal de demo de simulación"""
    
    st.title("🔬 Demo del Módulo de Simulación APE")
    st.markdown("Visualización de estructuras de datos internas y algoritmo de scheduling")
    
    # Sidebar para controles
    st.sidebar.header("⚙️ Configuración")
    
    # Datos de prueba
    assignments, teams = create_sample_data()
    
    # Controles what-if
    st.sidebar.subheader("What-If Controls")
    
    # Modificar capacidad de equipos
    st.sidebar.write("**Capacidad de Equipos**")
    for team_id, team in teams.items():
        new_capacity = st.sidebar.slider(
            f"{team.name} (total devs)",
            min_value=1, max_value=10, value=team.total_devs,
            key=f"team_{team_id}_capacity"
        )
        teams[team_id].total_devs = new_capacity
        
        new_busy = st.sidebar.slider(
            f"{team.name} (busy devs)",
            min_value=0, max_value=new_capacity, value=team.busy_devs,
            key=f"team_{team_id}_busy"
        )
        teams[team_id].busy_devs = new_busy
    
    # Modificar prioridades
    st.sidebar.write("**Prioridades de Proyectos**")
    project_priorities = {}
    for project_name in ["Alpha", "Beta", "Gamma"]:
        priority = st.sidebar.selectbox(
            f"Prioridad {project_name}",
            options=[1, 2, 3],
            index=[1, 2, 3].index({"Alpha": 1, "Beta": 2, "Gamma": 3}[project_name]),
            key=f"priority_{project_name}"
        )
        project_priorities[project_name] = priority
    
    # Aplicar cambios de prioridad
    for assignment in assignments:
        assignment.priority = project_priorities[assignment.project_name]
    
    # Fecha de simulación
    sim_date = st.sidebar.date_input(
        "Fecha de simulación",
        value=date(2025, 6, 16),
        key="sim_date"
    )
    
    # Ejecutar simulación
    if st.sidebar.button("🚀 Ejecutar Simulación", type="primary"):
        st.session_state.run_simulation = True
    
    # Mostrar datos de entrada
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Equipos")
        teams_data = []
        for team in teams.values():
            teams_data.append({
                "Equipo": team.name,
                "Total Devs": team.total_devs,
                "Busy Devs": team.busy_devs,
                "Disponibles": team.total_devs - team.busy_devs
            })
        st.dataframe(pd.DataFrame(teams_data), use_container_width=True)
    
    with col2:
        st.subheader("📋 Asignaciones")
        assignments_data = []
        for assignment in sorted(assignments, key=lambda a: (a.priority, a.phase_order)):
            assignments_data.append({
                "Proyecto": assignment.project_name,
                "Fase": assignment.phase,
                "Prioridad": assignment.priority,
                "Equipo": teams[assignment.team_id].name,
                "Devs": assignment.devs_assigned,
                "Horas": assignment.hours_needed
            })
        st.dataframe(pd.DataFrame(assignments_data), use_container_width=True)
    
    # Ejecutar simulación si se solicitó
    if st.session_state.get('run_simulation', False):
        
        st.markdown("---")
        st.header("🎯 Resultados de Simulación")
        
        # Crear scheduler y ejecutar
        scheduler = ProjectScheduler()
        
        # Capturar estado interno durante simulación
        result = scheduler.simulate(assignments, teams, today=sim_date)
        
        # Mostrar resultados
        render_simulation_results(result, teams)
        
        # Mostrar estructuras internas
        render_internal_structures(result, assignments, teams, sim_date)
        
        # Reset flag
        st.session_state.run_simulation = False


def render_simulation_results(result, teams):
    """Muestra los resultados de la simulación"""
    
    # Cronograma detallado
    st.subheader("📅 Cronograma Detallado")
    
    schedule_data = []
    for assignment in result.assignments:
        if assignment.start_date and assignment.end_date:
            duration = (assignment.end_date - assignment.start_date).days + 1
            schedule_data.append({
                "Proyecto": assignment.project_name,
                "Fase": assignment.phase,
                "Equipo": teams[assignment.team_id].name,
                "Inicio": assignment.start_date,
                "Fin": assignment.end_date,
                "Duración": f"{duration} días",
                "Devs": assignment.devs_assigned
            })
    
    schedule_df = pd.DataFrame(schedule_data)
    st.dataframe(schedule_df, use_container_width=True)
    
    # Gráfico de Gantt
    st.subheader("📊 Diagrama de Gantt")
    
    if not schedule_df.empty:
        fig = px.timeline(
            schedule_df,
            x_start="Inicio",
            x_end="Fin",
            y="Proyecto",
            color="Equipo",
            text="Fase",
            title="Cronograma de Proyectos"
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Resumen por proyecto
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Resumen por Proyecto")
        summary_data = []
        for summary in result.project_summaries:
            if summary['start_date'] and summary['end_date']:
                duration = (summary['end_date'] - summary['start_date']).days + 1
                summary_data.append({
                    "Proyecto": summary['project_name'],
                    "Estado": summary['state'],
                    "Inicio": summary['start_date'],
                    "Fin": summary['end_date'],
                    "Duración": f"{duration} días"
                })
        
        if summary_data:
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    with col2:
        st.subheader("⚡ Métricas")
        if schedule_data:
            total_projects = len(set(item['Proyecto'] for item in schedule_data))
            avg_duration = sum((item['Fin'] - item['Inicio']).days + 1 for item in schedule_data) / len(schedule_data)
            
            st.metric("Total Proyectos", total_projects)
            st.metric("Duración Promedio", f"{avg_duration:.1f} días")
            
            # Utilización por equipo
            team_usage = {}
            for item in schedule_data:
                team = item['Equipo']
                if team not in team_usage:
                    team_usage[team] = 0
                team_usage[team] += item['Devs'] * ((item['Fin'] - item['Inicio']).days + 1)
            
            st.write("**Uso Total por Equipo:**")
            for team, usage in team_usage.items():
                st.write(f"- {team}: {usage} dev-días")


def render_internal_structures(result, assignments, teams, sim_date):
    """Muestra las estructuras de datos internas del algoritmo"""
    
    st.markdown("---")
    st.header("🔍 Under the Hood - Estructuras Internas")
    
    # Recrear simulación paso a paso para mostrar estados
    scheduler = ProjectScheduler()
    
    # Simular paso a paso
    active_by_team = {tid: [] for tid in teams.keys()}
    project_next_free = {}
    
    sorted_assignments = sorted(assignments, key=lambda a: (a.priority, a.phase_order))
    
    st.subheader("🔄 Proceso de Simulación Paso a Paso")
    
    steps_data = []
    
    for i, assignment in enumerate(sorted_assignments):
        
        # Calcular para esta asignación
        ready = max(assignment.ready_date, sim_date)
        if assignment.project_id in project_next_free:
            ready = max(ready, project_next_free[assignment.project_id])
        
        # Simular el procesamiento
        hours_per_day = assignment.devs_assigned * 8
        days_needed = (assignment.hours_needed + hours_per_day - 1) // hours_per_day  # ceil
        
        # Encontrar slot disponible (simplificado para demo)
        start_date = ready
        end_date = start_date + timedelta(days=days_needed - 1)
        
        # Actualizar estructuras
        active_by_team[assignment.team_id].append({
            'start': start_date,
            'end': end_date,
            'devs': assignment.devs_assigned,
            'project': assignment.project_name,
            'phase': assignment.phase
        })
        
        project_next_free[assignment.project_id] = end_date + timedelta(days=1)
        
        # Guardar estado para mostrar
        steps_data.append({
            "Paso": i + 1,
            "Procesando": f"{assignment.project_name}-{assignment.phase}",
            "Equipo": teams[assignment.team_id].name,
            "Ready Date": ready,
            "Inicio Calculado": start_date,
            "Fin Calculado": end_date,
            "Días Necesarios": days_needed
        })
    
    # Mostrar pasos
    steps_df = pd.DataFrame(steps_data)
    st.dataframe(steps_df, use_container_width=True)
    
    # Mostrar estructuras finales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 active_by_team (Estado Final)")
        
        for team_id, assignments_list in active_by_team.items():
            if assignments_list:
                st.write(f"**{teams[team_id].name} (Team {team_id}):**")
                for j, assignment in enumerate(assignments_list):
                    st.write(f"  {j+1}. {assignment['project']}-{assignment['phase']}: "
                           f"{assignment['start']} → {assignment['end']} "
                           f"({assignment['devs']} devs)")
            else:
                st.write(f"**{teams[team_id].name} (Team {team_id}):** Sin asignaciones")
    
    with col2:
        st.subheader("⏭️ project_next_free")
        
        if project_next_free:
            next_free_data = []
            for project_id, next_date in project_next_free.items():
                project_name = next(a.project_name for a in assignments if a.project_id == project_id)
                next_free_data.append({
                    "Proyecto": project_name,
                    "Próxima Fecha Libre": next_date
                })
            
            st.dataframe(pd.DataFrame(next_free_data), use_container_width=True)
        else:
            st.write("Sin proyectos procesados")
    
    # Visualización de ocupación por equipo
    st.subheader("📊 Ocupación por Equipo en el Tiempo")
    
    # Crear timeline de ocupación
    timeline_data = []
    
    for team_id, team in teams.items():
        team_assignments = active_by_team[team_id]
        
        # Crear rango de fechas
        if team_assignments:
            min_date = min(a['start'] for a in team_assignments)
            max_date = max(a['end'] for a in team_assignments)
            
            current_date = min_date
            while current_date <= max_date:
                # Calcular ocupación en esta fecha
                occupied = team.busy_devs  # Base occupation
                
                for assignment in team_assignments:
                    if assignment['start'] <= current_date <= assignment['end']:
                        occupied += assignment['devs']
                
                timeline_data.append({
                    "Fecha": current_date,
                    "Equipo": team.name,
                    "Ocupados": occupied,
                    "Total": team.total_devs,
                    "Disponibles": team.total_devs - occupied,
                    "Utilización %": (occupied / team.total_devs) * 100
                })
                
                current_date += timedelta(days=1)
    
    if timeline_data:
        timeline_df = pd.DataFrame(timeline_data)
        
        # Gráfico de utilización
        fig = px.line(
            timeline_df,
            x="Fecha",
            y="Utilización %",
            color="Equipo",
            title="Utilización de Equipos en el Tiempo",
            markers=True
        )
        fig.add_hline(y=100, line_dash="dash", line_color="red", 
                     annotation_text="Capacidad Máxima")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de ocupación detallada
        with st.expander("Ver Datos Detallados de Ocupación"):
            st.dataframe(timeline_df, use_container_width=True)


def main():
    """Función principal"""
    st.set_page_config(
        page_title="Demo Simulación APE",
        page_icon="🔬",
        layout="wide"
    )
    
    render_simulation_demo()


if __name__ == "__main__":
    main()