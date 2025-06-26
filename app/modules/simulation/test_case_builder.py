import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any
from ..common.models import Team, Assignment
from .scheduler import ProjectScheduler

class TestCaseBuilder:
    """Constructor visual de casos de prueba para simulación APE"""
    
    def __init__(self):
        self.default_teams = {
            1: {"name": "Arch", "total_devs": 2, "busy_devs": 0},
            2: {"name": "Model", "total_devs": 4, "busy_devs": 0},
            3: {"name": "Devs", "total_devs": 6, "busy_devs": 1},
            4: {"name": "Dqa", "total_devs": 3, "busy_devs": 0}
        }
        
        self.phase_templates = {
            "Completo (4 fases)": ["Arch", "Model", "Devs", "Dqa"],
            "Sin DQA": ["Arch", "Model", "Devs"],
            "Solo Backend": ["Arch", "Model"],
            "Solo Frontend": ["Devs", "Dqa"]
        }
        
        # Configuración de tiers por fase según patrón real APE
        self.default_phase_tiers = {
            "Arch": 1,    # Arch siempre Tier 1
            "Model": 2,   # Model típicamente Tier 2
            "Devs": 3,    # Dev siempre Tier 3
            "Dqa": 2      # DQA típicamente Tier 2, máximo 3
        }
        
        # Configuración de devs por fase según patrón real APE
        self.default_phase_devs = {
            "Arch": 1.0,  # Arch: 2 devs por defecto
            "Model": 1.0, # Model: 1 dev por defecto
            "Devs": 1.0,  # Dev: 1 dev por defecto
            "Dqa": 1.0    # DQA: 1 dev por defecto
        }
        
        # Matriz de horas por tier y fase según arquitectura APE
        self.tier_hours_by_phase = {
            "Arch": {1: 16, 2: 32, 3: 72, 4: 240},
            "Model": {1: 40, 2: 80, 3: 120, 4: 160},
            "Devs": {1: 16, 2: 40, 3: 80, 4: 120},
            "Dqa": {1: 8, 2: 24, 3: 40, 4: 0}  # Tier 4 no disponible para Dqa
        }
        
        # Mantener nombres de tamaños para compatibilidad con UI
        self.size_names = ["Pequeño", "Mediano", "Grande", "Crítico"]
    
    
    def render_team_configuration(self) -> Dict[int, Team]:
        """Renderiza la configuración de equipos"""
        st.subheader("👥 Configuración de Equipos")
        
        teams = {}
        cols = st.columns(4)
        
        for i, (team_id, team_data) in enumerate(self.default_teams.items()):
            with cols[i]:
                st.write(f"**{team_data['name']}**")
                total = st.number_input(
                    "Total devs", 
                    min_value=1, max_value=20, 
                    value=team_data['total_devs'],
                    key=f"total_{team_id}"
                )
                busy = st.number_input(
                    "Ocupados", 
                    min_value=0, max_value=total,
                    value=team_data['busy_devs'],
                    key=f"busy_{team_id}"
                )
                
                teams[team_id] = Team(
                    id=team_id,
                    name=team_data['name'],
                    total_devs=total,
                    busy_devs=busy
                )
        
        return teams
    
    def render_project_builder(self) -> List[Dict]:
        """Renderiza el constructor de proyectos con configuración de tiers por fase"""
        st.subheader("➕ Constructor de Proyectos")
        
        # Inicializar datos de proyectos en session_state
        if 'projects_data' not in st.session_state:
            st.session_state.projects_data = []
        
        # Formulario para nuevo proyecto
        with st.form("new_project_form"):
            st.write("**Agregar Nuevo Proyecto**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                project_name = st.text_input("Nombre del Proyecto", placeholder="ej: MiProyecto")
                priority = st.selectbox("Prioridad", [1, 2, 3], help="1 = Alta, 3 = Baja")
            
            with col2:
                tier = st.selectbox("Tamaño", self.size_names)
                start_date = st.date_input("Fecha de Inicio", value=datetime.now().date())
            
            with col3:
                phase_template = st.selectbox("Fases", list(self.phase_templates.keys()))
                phases = self.phase_templates[phase_template]
                st.write(f"Fases: {', '.join(phases)}")
            
            # Configuración de tiers por fase
            st.write("**🏗️ Configuración de Tiers por Fase:**")
            st.write("*Configura el tier individual para cada fase del proyecto*")
            
            phase_tiers = {}
            tier_cols = st.columns(len(phases))
            
            for i, phase in enumerate(phases):
                with tier_cols[i]:
                    max_tier = 4 if phase != "Dqa" else 3  # DQA limitado a Tier 3
                    default_tier = self.default_phase_tiers.get(phase, 2)
                    
                    phase_tiers[phase] = st.selectbox(
                        f"{phase} Tier",
                        options=list(range(1, max_tier + 1)),
                        index=default_tier - 1,
                        key=f"tier_{phase}_{len(st.session_state.projects_data)}",
                        help=f"Tier para la fase {phase} (1=Simple, {max_tier}=Complejo)"
                    )
# Configuración de devs por fase
            st.write("**👥 Configuración de Devs por Fase:**")
            st.write("*Configura la cantidad de desarrolladores asignados a cada fase*")
            
            phase_devs = {}
            devs_cols = st.columns(len(phases))
            
            for i, phase in enumerate(phases):
                with devs_cols[i]:
                    default_devs = self.default_phase_devs.get(phase, 1.0)
                    
                    phase_devs[phase] = st.number_input(
                        f"{phase} Devs",
                        min_value=0.5, max_value=10.0, step=0.5,
                        value=default_devs,
                        key=f"devs_{phase}_{len(st.session_state.projects_data)}",
                        help=f"Cantidad de devs para la fase {phase}"
                    )
            
            submitted = st.form_submit_button("➕ Agregar Proyecto", type="primary")
            
            if submitted and project_name:
                new_project = {
                    "id": len(st.session_state.projects_data) + 1,
                    "name": project_name,
                    "priority": priority,
                    "tier": tier,
                    "start_date": start_date,
                    "phases": phases,
                    "phase_tiers": phase_tiers,
                    "phase_devs": phase_devs
                }
                st.session_state.projects_data.append(new_project)
                st.success(f"✅ Proyecto '{project_name}' agregado con tiers: {phase_tiers} y devs: {phase_devs}")
                st.rerun()
        
        return st.session_state.projects_data
    
    def render_projects_editor(self, projects_data: List[Dict]) -> List[Dict]:
        """Renderiza el editor de proyectos existentes"""
        if not projects_data:
            st.info("👆 Agrega un nuevo proyecto para comenzar")
            return []
        
        st.subheader("📝 Resumen de Proyectos")
        
        # Mostrar proyectos con sus configuraciones de tier
        for i, project in enumerate(projects_data):
            with st.expander(f"🎯 {project['name']} (Prioridad {project['priority']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Información General:**")
                    st.write(f"- **ID:** {project['id']}")
                    st.write(f"- **Tamaño:** {project['tier']}")
                    st.write(f"- **Fecha Inicio:** {project['start_date']}")
                    st.write(f"- **Fases:** {', '.join(project['phases'])}")
                
                with col2:
                    st.write("**Configuración de Tiers:**")
                    for phase in project['phases']:
                        tier = project.get('phase_tiers', {}).get(phase, self.default_phase_tiers.get(phase, 2))
                        devs = project.get('phase_devs', {}).get(phase, self.default_phase_devs.get(phase, 1.0))
                        st.write(f"- **{phase}:** Tier {tier}, {devs} devs")
        
        # Detalle por Stage/Fase
        self.render_stage_details(projects_data)
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Limpiar Todo"):
                st.session_state.projects_data = []
                st.success("🧹 Proyectos eliminados")
                st.rerun()
        
        with col2:
            if st.button("📋 Exportar JSON"):
                json_data = json.dumps(st.session_state.projects_data, indent=2, default=str)
                st.download_button(
                    "⬇️ Descargar",
                    json_data,
                    "test_case.json",
                    mime_type="application/json"
                )
        
        with col3:
            if st.button("🔄 Regenerar IDs"):
                for i, project in enumerate(st.session_state.projects_data):
                    project['id'] = i + 1
                st.success("✅ IDs regenerados")
                st.rerun()
        
        return st.session_state.projects_data
    
    def render_stage_details(self, projects_data: List[Dict]):
        """Renderiza el detalle por stage/fase"""
        st.subheader("🔍 Detalle por Stage/Fase")
        
        if not projects_data:
            st.info("No hay proyectos para mostrar detalles")
            return
        
        # Crear tabla detallada por fase
        stage_details = []
        for project in projects_data:
            phase_tiers = project.get("phase_tiers", {})
            
            for phase_order, phase in enumerate(project["phases"]):
                tier = phase_tiers.get(phase, self.default_phase_tiers.get(phase, 2))
                devs = project.get('phase_devs', {}).get(phase, self.default_phase_devs.get(phase, 1.0))
                hours = self.tier_hours_by_phase.get(phase, {}).get(tier, 16)  # Usar matriz por fase y tier
                
                # Calcular duración estimada (8 horas por día)
                duration_days = max(1, round(hours / (8 * devs)))
                
                stage_details.append({
                    "Proyecto": project["name"],
                    "Fase": phase,
                    "Orden": phase_order + 1,
                    "Tier": tier,
                    "Devs Asignados": devs,
                    "Horas Estimadas": hours,
                    "Duración (días)": duration_days,
                    "Fecha Inicio": project["start_date"],
                    "Prioridad": project["priority"],
                    "Tamaño Proyecto": project["tier"]
                })
        
        stage_df = pd.DataFrame(stage_details)
        
        # Mostrar tabla con formato mejorado
        st.dataframe(
            stage_df,
            use_container_width=True,
            column_config={
                "Proyecto": st.column_config.TextColumn("Proyecto", width="medium"),
                "Fase": st.column_config.TextColumn("Fase", width="small"),
                "Tier": st.column_config.NumberColumn("Tier", width="small"),
                "Devs Asignados": st.column_config.NumberColumn("Devs", width="small"),
                "Horas Estimadas": st.column_config.NumberColumn("Horas", width="small"),
                "Duración (días)": st.column_config.NumberColumn("Días", width="small"),
                "Fecha Inicio": st.column_config.DateColumn("Inicio", width="medium"),
                "Prioridad": st.column_config.NumberColumn("Prioridad", width="small"),
                "Tamaño Proyecto": st.column_config.TextColumn("Tamaño", width="small")
            }
        )
        
        # Métricas resumen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_phases = len(stage_details)
            st.metric("📋 Total Fases", total_phases)
        
        with col2:
            total_hours = sum(detail["Horas Estimadas"] for detail in stage_details)
            st.metric("⏱️ Total Horas", f"{total_hours:,}")
        
        with col3:
            total_devs = sum(detail["Devs Asignados"] for detail in stage_details)
            st.metric("👥 Total Dev-Asignaciones", f"{total_devs:.1f}")
        
        with col4:
            avg_duration = sum(detail["Duración (días)"] for detail in stage_details) / len(stage_details) if stage_details else 0
            st.metric("📅 Duración Promedio", f"{avg_duration:.1f} días")
    
    def create_assignments_from_projects(self, projects_data: List[Dict]) -> List[Assignment]:
        """
        Convierte los datos de proyectos en assignments para la simulación
        AUTOMÁTICAMENTE genera assignments respetando el patrón real APE:
        - Arch: Tier 1, 2 devs
        - Model: Tier variable, 1 dev  
        - Dev: Tier 3, 1 dev
        - DQA: Tier variable (máx 3), 1 dev
        """
        assignments = []
        
        for project in projects_data:
            phase_tiers = project.get("phase_tiers", {})
            
            for phase_order, phase in enumerate(project["phases"]):
                # Mapear fase a team_id
                team_mapping = {"Arch": 1, "Model": 2, "Devs": 3, "Dqa": 4}
                team_id = team_mapping.get(phase, 1)
                
                # Obtener tier específico para esta fase
                phase_tier = phase_tiers.get(phase, self.default_phase_tiers.get(phase, 2))
                
                # Obtener devs asignados desde configuración del proyecto
                devs_assigned = project.get('phase_devs', {}).get(phase, self.default_phase_devs.get(phase, 1.0))
                
                # Calcular horas basado en el tier de la fase usando matriz específica
                estimated_hours = self.tier_hours_by_phase.get(phase, {}).get(phase_tier, 16)
                
                # Crear assignment con ID único
                assignment_id = project["id"] * 100 + phase_order + 1
                
                assignment = Assignment(
                    id=assignment_id,
                    project_id=project["id"],
                    project_name=project["name"],
                    project_priority=project["priority"],
                    team_id=team_id,
                    team_name=phase,  # Usar phase como team_name
                    tier=phase_tier,
                    devs_assigned=devs_assigned,
                    max_devs=devs_assigned,
                    estimated_hours=estimated_hours,
                    ready_to_start_date=project["start_date"],
                    assignment_start_date=project["start_date"]
                )
                
                assignments.append(assignment)
        
        return assignments
    
    def validate_test_case(self, projects_data: List[Dict], teams: Dict[int, Team]) -> List[str]:
        """Valida el caso de prueba antes de ejecutar la simulación"""
        errors = []
        
        if not projects_data:
            errors.append("❌ No hay proyectos definidos")
        
        # Validar nombres únicos
        names = [p["name"] for p in projects_data]
        if len(names) != len(set(names)):
            errors.append("❌ Los nombres de proyectos deben ser únicos")
        
        # Validar disponibilidad de equipos
        for team in teams.values():
            if team.busy_devs >= team.total_devs:
                errors.append(f"❌ Equipo {team.name} no tiene desarrolladores disponibles")
        
        # Validar fechas
        for project in projects_data:
            if project["start_date"] < datetime.now().date():
                errors.append(f"⚠️ Proyecto {project['name']} tiene fecha de inicio en el pasado")
        
        # Validar configuración de tiers
        for project in projects_data:
            phase_tiers = project.get("phase_tiers", {})
            for phase in project["phases"]:
                tier = phase_tiers.get(phase, self.default_phase_tiers.get(phase, 2))
                if phase == "Dqa" and tier > 3:
                    errors.append(f"⚠️ Proyecto {project['name']}: DQA no puede tener Tier > 3")
                
                # Validar que la matriz tenga valores para la combinación fase-tier
                hours = self.tier_hours_by_phase.get(phase, {}).get(tier, 0)
                if hours == 0 and phase == "Dqa" and tier == 4:
                    errors.append(f"⚠️ Proyecto {project['name']}: DQA Tier 4 no está disponible")
        
        return errors
    
    def render_simulation_runner(self, projects_data: List[Dict], teams: Dict[int, Team]):
        """Renderiza el ejecutor de simulación con validación"""
        st.subheader("▶️ Ejecutar Simulación")
        
        if not projects_data:
            st.warning("📋 Primero define algunos proyectos usando las plantillas o el constructor")
            return
        
        # Validación
        errors = self.validate_test_case(projects_data, teams)
        
        if errors:
            st.error("🚨 **Errores de Validación:**")
            for error in errors:
                st.write(error)
            return
        
        # Vista previa con assignments generados automáticamente
        with st.expander("👀 Vista Previa del Caso de Prueba"):
            st.write("**Proyectos y Assignments Generados Automáticamente:**")
            
            preview_data = []
            for project in projects_data:
                phase_tiers = project.get("phase_tiers", {})
                
                for phase in project["phases"]:
                    tier = phase_tiers.get(phase, self.default_phase_tiers.get(phase, 2))
                    devs = project.get('phase_devs', {}).get(phase, self.default_phase_devs.get(phase, 1.0))
                    hours = self.tier_hours_by_phase.get(phase, {}).get(tier, 16)  # Usar matriz por fase y tier
                    
                    preview_data.append({
                        "Proyecto": project["name"],
                        "Fase": phase,
                        "Tier": tier,
                        "Devs": devs,
                        "Horas": hours,
                        "Prioridad": project["priority"]
                    })
            
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
            
            st.info("💡 **Los assignments se generan automáticamente** siguiendo el patrón APE: Arch=Tier1+2devs, Model=TierVariable+1dev, Dev=Tier3+1dev, DQA=TierVariable+1dev")
        
        # Botón de simulación
        if st.button("🚀 Ejecutar Simulación", type="primary", use_container_width=True):
            with st.spinner("🔄 Ejecutando simulación..."):
                assignments = self.create_assignments_from_projects(projects_data)
                scheduler = ProjectScheduler()
                
                # DEBUG: Validar datos antes de la simulación
                st.write(f"DEBUG: {len(assignments)} assignments creados")
                st.write(f"DEBUG: {len(teams)} teams disponibles")
                st.write(f"DEBUG: {len(projects_data)} projects en datos")
                
                # Crear SimulationInput correctamente
                from ..common.models import SimulationInput, Project
                from datetime import timedelta
                
                today = min(p["start_date"] for p in projects_data)
                
                # Convertir projects_data a objetos Project
                projects_dict = {}
                for p in projects_data:
                    # Calcular fechas de entrega estimadas (30 días por defecto)
                    due_wo_qa = p["start_date"] + timedelta(days=30)
                    due_with_qa = due_wo_qa + timedelta(days=7)
                    
                    project = Project(
                        id=p["id"],
                        name=p["name"],
                        priority=p["priority"],
                        start_date=p["start_date"],
                        due_date_wo_qa=due_wo_qa,
                        due_date_with_qa=due_with_qa,
                        phase=p.get("tier", "")  # Usar tier como phase
                    )
                    projects_dict[p["id"]] = project
                
                simulation_input = SimulationInput(
                    teams=teams,
                    projects=projects_dict,
                    assignments=assignments,
                    simulation_start_date=today
                )
                
                st.write(f"DEBUG: Fecha de inicio de simulación: {today}")
                result = scheduler.simulate(simulation_input)
                
                st.session_state.simulation_result = result
                st.session_state.simulation_assignments = assignments
                st.success(f"✅ Simulación completada - {len(assignments)} assignments generados automáticamente")
                st.rerun()
    
    def render_gantt_chart(self):
        """Renderiza el gráfico Gantt de los resultados"""
        if 'simulation_result' not in st.session_state:
            return
        
        result = st.session_state.simulation_result
        
        if not result.assignments or not any(a.calculated_start_date and a.calculated_end_date for a in result.assignments):
            st.warning("No hay datos suficientes para generar el gráfico Gantt")
            return
        
        st.subheader("📊 Gráfico Gantt - Timeline de Proyectos")
        
        # Preparar datos para el gráfico Gantt
        gantt_data = []
        colors = {
            "Proyecto-A": "#FF6B6B", "Proyecto-B": "#4ECDC4", "Proyecto-C": "#45B7D1",
            "Urgente-1": "#FF8E53", "Urgente-2": "#FF6B9D", "Crítico": "#C44569",
            "Fase-1": "#6C5CE7", "Fase-2": "#A29BFE", "Fase-3": "#74B9FF",
            "API-Core": "#00B894", "Microservice-A": "#00CEC9", "Integration": "#55A3FF"
        }
        
        for item in result.assignments:
            if item.calculated_start_date and item.calculated_end_date:
                # Usar colores dinámicos si el proyecto no está en el mapeo predefinido
                project_color = colors.get(item.project_name, f"#{hash(item.project_name) % 0xFFFFFF:06x}")
                
                gantt_data.append({
                    "Task": f"{item.project_name}-{item.team_name}",
                    "Start": item.calculated_start_date,
                    "Finish": item.calculated_end_date,
                    "Project": item.project_name,
                    "Resource": f"Tier {getattr(item, 'tier', '?')} ({getattr(item, 'pending_hours', 0)}h)",
                    "Team": item.team_name,
                    "Priority": getattr(item, 'project_priority', 1)
                })
        
        if gantt_data:
            gantt_df = pd.DataFrame(gantt_data)
            
            # Crear gráfico Gantt con Plotly
            fig = px.timeline(
                gantt_df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Project",
                title="📅 Cronograma de Proyectos - Vista Gantt",
                hover_data=["Resource", "Team", "Priority"],
                height=max(400, len(gantt_data) * 30)  # Altura dinámica
            )
            
            # Personalizar el gráfico
            fig.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Tareas (Proyecto-Fase)",
                showlegend=True,
                font=dict(size=12),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Mejorar el formato de las fechas en el eje X
            fig.update_xaxes(
                tickformat="%Y-%m-%d",
                tickangle=45
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Información adicional del Gantt
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📈 Estadísticas del Timeline:**")
                min_start = min(item["Start"] for item in gantt_data)
                max_end = max(item["Finish"] for item in gantt_data)
                total_duration = (max_end - min_start).days + 1
                st.write(f"- **Duración total:** {total_duration} días")
                st.write(f"- **Fecha inicio:** {min_start.strftime('%Y-%m-%d')}")
                st.write(f"- **Fecha fin:** {max_end.strftime('%Y-%m-%d')}")
            
            with col2:
                st.write("**🎯 Distribución por Proyecto:**")
                project_counts = gantt_df['Project'].value_counts()
                for project, count in project_counts.items():
                    st.write(f"- **{project}:** {count} fases")
        else:
            st.warning("No hay datos para mostrar en el gráfico Gantt")
    
    def render_results(self):
        """Renderiza los resultados de la simulación"""
        if 'simulation_result' not in st.session_state:
            return
        
        result = st.session_state.simulation_result
        
        st.subheader("📊 Resultados de la Simulación")
        
        if result.assignments:
            # Cronograma con información de tier
            schedule_df = pd.DataFrame([
                {
                    "Proyecto": item.project_name,
                    "Fase": item.team_name,
                    "Tier": getattr(item, 'tier', 'N/A'),
                    "Devs": item.devs_assigned,
                    "Inicio": item.calculated_start_date.strftime("%Y-%m-%d") if item.calculated_start_date else "N/A",
                    "Fin": item.calculated_end_date.strftime("%Y-%m-%d") if item.calculated_end_date else "N/A",
                    "Días": (item.calculated_end_date - item.calculated_start_date).days + 1 if item.calculated_start_date and item.calculated_end_date else 0
                }
                for item in result.assignments
            ])
            
            st.dataframe(schedule_df, use_container_width=True)
            
            # Métricas clave
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                valid_assignments = [item for item in result.assignments if item.calculated_start_date and item.calculated_end_date]
                if valid_assignments:
                    min_start = min(s.calculated_start_date for s in valid_assignments)
                    total_days = max((item.calculated_end_date - min_start).days for item in valid_assignments) + 1
                else:
                    total_days = 0
                st.metric("📅 Duración Total", f"{total_days} días")
            
            with col2:
                st.metric("📋 Assignments", len(result.assignments))
            
            with col3:
                unique_projects = len(set(item.project_name for item in result.assignments))
                st.metric("🎯 Proyectos", unique_projects)
            
            with col4:
                total_devs_used = sum(item.devs_assigned for item in result.assignments)
                st.metric("👥 Total Dev-Días", f"{total_devs_used:.1f}")
            
            # Resumen por proyecto
            st.write("**📈 Resumen por Proyecto:**")
            project_summary = {}
            for item in result.assignments:
                if item.project_name not in project_summary:
                    project_summary[item.project_name] = {
                        "Fases": [],
                        "Inicio": item.calculated_start_date,
                        "Fin": item.calculated_end_date,
                        "Total Devs": 0
                    }
                
                project_summary[item.project_name]["Fases"].append(f"{item.team_name}(T{getattr(item, 'tier', '?')})")
                if item.calculated_start_date and project_summary[item.project_name]["Inicio"]:
                    project_summary[item.project_name]["Inicio"] = min(project_summary[item.project_name]["Inicio"], item.calculated_start_date)
                elif item.calculated_start_date:
                    project_summary[item.project_name]["Inicio"] = item.calculated_start_date
                
                if item.calculated_end_date and project_summary[item.project_name]["Fin"]:
                    project_summary[item.project_name]["Fin"] = max(project_summary[item.project_name]["Fin"], item.calculated_end_date)
                elif item.calculated_end_date:
                    project_summary[item.project_name]["Fin"] = item.calculated_end_date
                project_summary[item.project_name]["Total Devs"] += item.devs_assigned
            
            summary_df = pd.DataFrame([
                {
                    "Proyecto": name,
                    "Fases": " → ".join(data["Fases"]),
                    "Inicio": data["Inicio"].strftime("%Y-%m-%d"),
                    "Fin": data["Fin"].strftime("%Y-%m-%d"),
                    "Duración": (data["Fin"] - data["Inicio"]).days + 1,
                    "Total Devs": f"{data['Total Devs']:.1f}"
                }
                for name, data in project_summary.items()
            ])
            
            st.dataframe(summary_df, use_container_width=True)
            
            # Mostrar gráfico Gantt
            st.divider()
            self.render_gantt_chart()
        
        else:
            st.error("❌ No se pudieron programar las asignaciones con la configuración actual")


def render_test_case_builder():
    """Función principal para renderizar el constructor de casos de prueba"""
    builder = TestCaseBuilder()
    
    st.header("📋 Constructor de Casos de Prueba APE")
    st.markdown("Crea y modifica casos de prueba de forma visual. **Los assignments se generan automáticamente** siguiendo el patrón real de APE.")
    
    # Información del patrón APE
    with st.expander("ℹ️ Patrón de Generación Automática de Assignments"):
        st.markdown("""
        **El sistema genera automáticamente los assignments siguiendo el patrón real de APE:**
        
        - **🏗️ Arch**: Siempre Tier 1, **2 devs** por defecto
        - **📊 Model**: Tier configurable por proyecto, **1 dev** por defecto  
        - **💻 Dev**: Siempre Tier 3, **1 dev** por defecto
        - **🧪 DQA**: Tier configurable (máximo 3), **1 dev** por defecto
        
        Cada fase puede tener su **tier individual** configurado en el constructor de proyectos.
        """)
    
    # Configuración de equipos
    teams = builder.render_team_configuration()
    
    st.divider()
    
    # Constructor de proyectos
    projects_data = builder.render_project_builder()
    
    st.divider()
    
    # Editor de proyectos y detalle por stage
    projects_data = builder.render_projects_editor(projects_data)
    
    st.divider()
    
    # Ejecutor de simulación
    builder.render_simulation_runner(projects_data, teams)
    
    st.divider()
    
    # Resultados con Gantt integrado
    builder.render_results()