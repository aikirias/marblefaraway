"""
Gestión de proyectos APE - Versión consolidada y refactorizada
Combina funcionalidad de projects.py y projects_simple.py eliminando duplicación
"""

import streamlit as st
from datetime import date
try:
    from st_draggable_list import DraggableList
    DRAGGABLE_AVAILABLE = True
except ImportError:
    DRAGGABLE_AVAILABLE = False
from modules.common.models import Project, Assignment
from modules.common.projects_crud import (
    create_project, read_all_projects, update_project, delete_project_by_name
)
from modules.common.assignments_crud import create_assignment
from modules.common.teams_crud import read_all_teams


def render_projects():
    """Renderiza la gestión de proyectos con tabs organizados"""
    st.header("Project Management")
    
    tab1, tab2, tab3 = st.tabs(["📊 Monitoring", "➕ Gestión", "🔄 Reordenar"])
    
    with tab1:
        render_projects_dashboard()
    
    with tab2:
        render_project_management()
    
    with tab3:
        render_project_reordering()


def render_projects_dashboard():
    """Monitoring con vista de proyectos y métricas"""
    st.subheader("📊 Monitoring de Proyectos")
    
    try:
        projects = _load_projects_safely()
        if not projects:
            st.info("No hay proyectos creados. Ve a la pestaña 'Gestión' para crear uno.")
            return
        
        # Métricas de proyectos
        _render_project_metrics(projects)
        
        # Sección de proyectos detallados
        st.markdown("---")
        st.markdown("### 📋 Detalle de Proyectos")
        _render_filtered_projects(projects, "dashboard_filter")
        
        # Sección de reordenamiento por drag and drop
        st.markdown("---")
        st.markdown("### 🔄 Reordenar Prioridades")
        
        # Mostrar lista simple de proyectos ordenados por prioridad efectiva
        all_projects = list(projects.values())
        def effective_priority(project):
            if project.is_active():
                return (0, project.priority)  # Activos primero
            else:
                return (1, project.priority)  # Pausados después
        
        sorted_projects = sorted(all_projects, key=effective_priority)
        
        st.write("📋 Orden actual de proyectos:")
        for i, p in enumerate(sorted_projects, 1):
            state_symbol = "🟢" if p.is_active() else "⏸️"
            state_text = "Activo" if p.is_active() else "Pausado"
            st.write(f"  {i}. ({p.priority}) {p.name} - {state_symbol} {state_text}")
        
    except Exception as e:
        st.error(f"Error general en dashboard: {e}")
        import traceback
        st.code(traceback.format_exc())


def render_project_management():
    """Gestión completa de proyectos: crear, editar, eliminar"""
    st.subheader("📋 Gestión de Proyectos")
    
    projects = _load_projects_safely()
    
    if projects:
        st.markdown("### Proyectos Existentes")
        _render_filtered_projects(projects, "mgmt_filter", editable=True)
        st.markdown("---")
    
    _render_project_creation_form(projects)
    _render_project_deletion_section(projects)


def render_project_reordering():
    """Reordenamiento de proyectos por prioridad con controles de estado"""
    st.subheader("🔄 Reordenar Proyectos")
    
    projects = _load_projects_safely()
    if not projects:
        st.info("No hay proyectos para reordenar.")
        return
    
    sorted_projects = sorted(projects.values(), key=lambda p: p.priority)
    
    # Controles de estado
    st.markdown("### Estados de Proyectos")
    _render_project_state_controls(sorted_projects)
    
    st.markdown("---")
    st.markdown("### Reordenar por Prioridad")
    
    # Recargar para datos actualizados
    projects = _load_projects_safely()
    _render_priority_reordering(projects)


# ============================================================================
# FUNCIONES PRIVADAS DE UTILIDAD
# ============================================================================

def _load_projects_safely():
    """Carga proyectos con manejo de errores"""
    try:
        return read_all_projects()
    except Exception as e:
        st.error(f"Error cargando proyectos: {e}")
        return {}


def _render_project_metrics(projects):
    """Renderiza métricas de proyectos"""
    active_count = sum(1 for p in projects.values() if p.is_active())
    inactive_count = len(projects) - active_count
    total_hours_worked = sum(p.horas_trabajadas for p in projects.values())
    total_hours_estimated = sum(p.horas_totales_estimadas for p in projects.values())
    total_hours_remaining = sum(p.get_horas_faltantes() for p in projects.values())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Proyectos Activos", active_count)
    with col2:
        st.metric("Proyectos Inactivos", inactive_count)
    with col3:
        st.metric("Horas Trabajadas", total_hours_worked)
    with col4:
        st.metric("Horas Faltantes", total_hours_remaining)


def _render_filtered_projects(projects, filter_key, editable=False):
    """Renderiza proyectos con filtros aplicados"""
    show_filter = st.selectbox(
        "🔍 Mostrar",
        ["Todos", "Solo Activos", "Solo Inactivos"],
        index=0,  # Por defecto mostrar "Todos"
        key=filter_key
    )
    
    filtered_projects = _filter_projects(projects, show_filter)
    
    # Debug info
    st.write(f"🔍 Filtro aplicado: {show_filter}")
    st.write(f"📊 Proyectos encontrados: {len(filtered_projects)}")
    
    if not filtered_projects:
        st.info(f"No hay proyectos para mostrar con el filtro '{show_filter}'")
        return
    
    # Mostrar lista de proyectos encontrados
    st.write("📋 Proyectos a mostrar:")
    for i, project in enumerate(filtered_projects):
        state = "Activo" if project.is_active() else "Pausado"
        st.write(f"  {i+1}. {project.name} - {state} (Prioridad: {project.priority})")
    
    st.markdown("---")
    
    for project in filtered_projects:
        if editable:
            _render_editable_project_card(project)
        else:
            _render_simple_project_card(project)


def _filter_projects(projects, filter_type):
    """Filtra proyectos según el tipo especificado con prioridad efectiva"""
    filtered = list(projects.values())
    
    if filter_type == "Solo Activos":
        filtered = [p for p in filtered if p.is_active()]
    elif filter_type == "Solo Inactivos":
        filtered = [p for p in filtered if not p.is_active()]
    
    # Implementar prioridad efectiva: activos primero por prioridad, luego pausados por prioridad
    def effective_priority(project):
        if project.is_active():
            return (0, project.priority)  # Activos tienen prioridad 0 (más alta)
        else:
            return (1, project.priority)  # Pausados tienen prioridad 1 (más baja)
    
    return sorted(filtered, key=effective_priority)


def _render_simple_project_card(project):
    """Renderiza tarjeta simple de proyecto"""
    bg_color = "#e8f5e8" if project.is_active() else "#f5f5f5"
    
    with st.container():
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{project.name}** (Prioridad: {project.priority})")
            st.markdown(f"📅 {project.start_date} → {project.due_date_with_qa}")
            
            if project.horas_totales_estimadas > 0:
                st.markdown(f"⏱️ Progreso: {project.get_progreso_display()}")
                st.markdown(f"🔄 Horas faltantes: {project.get_horas_faltantes()}")
                progress_pct = project.get_progreso_porcentaje() / 100
                st.progress(progress_pct)
            elif project.horas_trabajadas > 0:
                st.markdown(f"⏱️ Horas trabajadas: {project.horas_trabajadas}")
            
            if project.fecha_inicio_real:
                st.markdown(f"🚀 Inicio real: {project.fecha_inicio_real}")
        
        with col2:
            st.markdown(f"**Estado:** {project.get_state_display()}")
        
        with col3:
            _render_project_activation_control(project)
        
        st.markdown("</div>", unsafe_allow_html=True)


def _render_editable_project_card(project):
    """Renderiza tarjeta editable de proyecto"""
    from modules.common.assignments_crud import read_assignments_by_project
    
    with st.expander(f"{project.get_state_display()} {project.name} (Prioridad: {project.priority})"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_active = st.checkbox(
                "Proyecto Activo",
                value=project.is_active(),
                key=f"edit_active_{project.id}"
            )
            
            new_hours = st.number_input(
                "Horas Trabajadas",
                min_value=0,
                value=project.horas_trabajadas,
                key=f"hours_{project.id}"
            )
            
            new_total_hours = st.number_input(
                "Horas Totales Estimadas",
                min_value=0,
                value=project.horas_totales_estimadas,
                key=f"total_hours_{project.id}",
                help="Estimación total de horas para completar el proyecto"
            )
        
        with col2:
            new_start_real = st.date_input(
                "Fecha de Inicio Real",
                value=project.fecha_inicio_real,
                key=f"start_real_{project.id}"
            )
            
            st.markdown(f"**Fechas:** {project.start_date} → {project.due_date_with_qa}")
            
            if new_total_hours > 0:
                temp_progress = _calculate_temp_progress(project, new_hours, new_total_hours)
                st.markdown(f"**Progreso:** {temp_progress['display']}")
                st.markdown(f"**Horas faltantes:** {temp_progress['remaining']}")
        
        # Configuración de Tiers y Devs por Etapa
        st.markdown("---")
        st.markdown("**🎯 Configuración de Tiers y Devs por Etapa**")
        
        # Cargar asignaciones actuales del proyecto
        current_assignments = read_assignments_by_project(project.id)
        teams = read_all_teams()
        tier_changes = {}
        dev_changes = {}
        
        if current_assignments and teams:
            for assignment in current_assignments:
                team = teams.get(assignment.team_id)
                if team and team.tier_capacities:
                    col_tier, col_devs = st.columns(2)
                    
                    with col_tier:
                        available_tiers = list(team.tier_capacities.keys())
                        current_tier = assignment.tier
                        
                        new_tier = st.selectbox(
                            f"Tier para {assignment.team_name}",
                            available_tiers,
                            index=available_tiers.index(current_tier) if current_tier in available_tiers else 0,
                            key=f"tier_{assignment.team_id}_{project.id}"
                        )
                        
                        if new_tier != current_tier:
                            tier_changes[assignment.id] = new_tier
                            # Mostrar preview de horas estimadas
                            new_estimated_hours = team.get_hours_per_person_for_tier(new_tier)
                            st.info(f"Nuevo tier {new_tier}: {new_estimated_hours} horas estimadas")
                    
                    with col_devs:
                        current_devs = assignment.devs_assigned
                        max_devs = team.total_devs  # Usar total de devs del equipo como máximo
                        
                        new_devs = st.number_input(
                            f"Devs asignados para {assignment.team_name}",
                            min_value=0.0,
                            max_value=float(max_devs),
                            value=float(current_devs),
                            step=0.5,
                            key=f"devs_{assignment.team_id}_{project.id}",
                            help=f"Máximo disponible: {max_devs}"
                        )
                        
                        if new_devs != current_devs:
                            dev_changes[assignment.id] = new_devs
                
                # Campo de horas estimadas personalizadas
        st.markdown("---")
        st.markdown("**⏱️ Horas Estimadas Personalizadas**")
        custom_hours_changes = {}
        
        if current_assignments and teams:
            for assignment in current_assignments:
                team = teams.get(assignment.team_id)
                if team:
                    col_custom, col_info = st.columns([2, 1])
                    
                    with col_custom:
                        current_custom = assignment.custom_estimated_hours
                        tier_hours = team.get_hours_per_person_for_tier(assignment.tier)
                        
                        new_custom_hours = st.number_input(
                            f"Horas estimadas para {assignment.team_name}",
                            min_value=0,
                            value=current_custom if current_custom is not None else 0,
                            key=f"custom_hours_{assignment.id}_{project.id}",
                            help=f"Dejar en 0 para usar tier ({tier_hours}h). Valor específico override el tier."
                        )
                        
                        # Si el valor cambió, guardarlo
                        new_value = new_custom_hours if new_custom_hours > 0 else None
                        if new_value != current_custom:
                            custom_hours_changes[assignment.id] = new_value
                    
                    with col_info:
                        if new_custom_hours > 0:
                            st.info(f"Usando: {new_custom_hours}h (personalizado)")
                        else:
                            st.info(f"Usando: {tier_hours}h (tier {assignment.tier})")
        
        if st.button(f"💾 Guardar Cambios", key=f"save_{project.id}"):
            _save_project_changes(project, new_active, new_hours, new_total_hours, new_start_real, tier_changes, dev_changes, custom_hours_changes)


def _render_project_activation_control(project):
    """Renderiza control de activación de proyecto"""
    new_active = st.checkbox(
        "Activo",
        value=project.is_active(),
        key=f"active_{project.id}"
    )
    
    if new_active != project.is_active():
        project.active = new_active
        if new_active and project.fecha_inicio_real is None:
            project.fecha_inicio_real = date.today()
        
        try:
            update_project(project)
            st.success(f"Proyecto {project.name} actualizado")
            st.rerun()
        except Exception as e:
            st.error(f"Error actualizando proyecto: {e}")


def _render_project_state_controls(sorted_projects):
    """Renderiza controles de estado para reordenamiento"""
    for i, project in enumerate(sorted_projects):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**({project.priority}) {project.name}**")
        
        with col2:
            new_active = st.checkbox(
                "Activo" if project.is_active() else "Inactivo",
                value=project.is_active(),
                key=f"reorder_active_{project.id}_{i}"
            )
            
            if new_active != project.is_active():
                project.active = new_active
                if new_active and project.fecha_inicio_real is None:
                    project.fecha_inicio_real = date.today()
                
                try:
                    update_project(project)
                    st.success(f"Estado de '{project.name}' actualizado")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error actualizando estado: {e}")


def _render_priority_reordering(projects):
    """Renderiza interfaz de reordenamiento por prioridad"""
    sorted_projects = sorted(projects.values(), key=lambda p: p.priority)
    
    if not DRAGGABLE_AVAILABLE:
        st.info("🔄 Funcionalidad de drag-and-drop no disponible. Mostrando orden actual:")
        for p in sorted_projects:
            state_symbol = "☑️" if p.is_active() else "☐"
            state_text = "Activo" if p.is_active() else "Inactivo"
            st.write(f"({p.priority}) {p.name} - {state_symbol} {state_text}")
        return
    
    items = []
    for p in sorted_projects:
        state_symbol = "☑️" if p.is_active() else "☐"
        state_text = "Activo" if p.is_active() else "Inactivo"
        items.append({
            "id": p.id, 
            "name": f"({p.priority}) {p.name} - {state_symbol} {state_text}"
        })
    
    new_order = DraggableList(items, text_key="name", key="proj_sort")
    
    if st.button("💾 Guardar Nuevo Orden"):
        try:
            for idx, item in enumerate(new_order, start=1):
                project = projects[item["id"]]
                project.priority = idx
                update_project(project)
            st.success("✅ Prioridades de proyectos actualizadas.")
            st.rerun()
        except Exception as e:
            st.error(f"Error actualizando prioridades: {e}")


def _render_project_creation_form(projects):
    """Renderiza formulario de creación de proyectos"""
    st.subheader("➕ Crear Nuevo Proyecto")
    
    with st.form("create_project"):
        col1, col2 = st.columns(2)
        
        with col1:
            pname = st.text_input("📝 Nombre del Proyecto")
            start = st.date_input("📅 Fecha de Inicio")
            initial_total_hours = st.number_input(
                "⏱️ Horas Totales Estimadas", 
                min_value=0, 
                value=0,
                help="Estimación total de horas para completar el proyecto"
            )
            
            # Configuración de Tiers y Devs por Etapa
            st.markdown("**🎯 Configuración de Tiers y Devs por Etapa**")
            teams = read_all_teams()
            tier_config = {}
            dev_config = {}
            if teams:
                for team_id, team in teams.items():
                    col_tier, col_devs = st.columns(2)
                    
                    with col_tier:
                        available_tiers = list(team.tier_capacities.keys()) if team.tier_capacities else [1]
                        if available_tiers:
                            selected_tier = st.selectbox(
                                f"Tier para {team.name}",
                                available_tiers,
                                key=f"tier_{team.name}_create"
                            )
                            tier_config[team_id] = selected_tier
                    
                    with col_devs:
                        max_available = team.get_available_devs()
                        selected_devs = st.number_input(
                            f"Devs para {team.name}",
                            min_value=0.0,
                            max_value=float(max_available),
                            value=1.0,
                            step=0.5,
                            key=f"devs_{team.name}_create",
                            help=f"Máximo disponible: {max_available}"
                        )
                        dev_config[team_id] = selected_devs
        
        with col2:
            due_with_qa = st.date_input("📅 Fecha Límite (con QA)")
            initial_active = st.checkbox("🟢 Crear como proyecto activo", value=True)
        
        submitted = st.form_submit_button("🚀 Crear Proyecto", type="primary")
        
        if submitted and pname:
            _create_new_project(pname, start, due_with_qa, 
                              initial_total_hours, initial_active, projects, tier_config, dev_config)


def _render_project_deletion_section(projects):
    """Renderiza sección de eliminación de proyectos"""
    st.subheader("🗑️ Eliminar Proyecto")
    
    if not projects:
        st.info("No hay proyectos disponibles para eliminar.")
        return
    
    project_names = [p.name for p in projects.values()]
    selected_project_to_delete = st.selectbox(
        "Seleccionar proyecto a eliminar",
        [""] + project_names,
        key="delete_project_select"
    )
    
    if selected_project_to_delete:
        st.warning(f"⚠️ Esto eliminará permanentemente '{selected_project_to_delete}' y todas sus asignaciones!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Confirmar Eliminación", type="primary"):
                _delete_project_by_name(selected_project_to_delete)
        
        with col2:
            if st.button("Cancelar"):
                st.rerun()


def _calculate_temp_progress(project, new_hours, new_total_hours):
    """Calcula progreso temporal para preview"""
    if new_total_hours <= 0:
        return {"display": "Sin estimación", "remaining": 0}
    
    faltantes = max(0, new_total_hours - new_hours)
    porcentaje = (new_hours / new_total_hours) * 100
    
    return {
        "display": f"{porcentaje:.1f}% ({new_hours}/{new_total_hours}h)",
        "remaining": faltantes
    }


def _save_project_changes(project, new_active, new_hours, new_total_hours, new_start_real, tier_changes=None, dev_changes=None, custom_hours_changes=None):
    """Guarda cambios en proyecto y actualiza tiers y devs de asignaciones"""
    from modules.common.assignments_crud import read_assignment, update_assignment
    
    try:
        # Actualizar proyecto
        project.active = new_active
        project.horas_trabajadas = new_hours
        project.horas_totales_estimadas = new_total_hours
        project.fecha_inicio_real = new_start_real
        
        if new_active and project.fecha_inicio_real is None:
            project.fecha_inicio_real = date.today()
        
        update_project(project)
        
        # Actualizar tiers de asignaciones si hay cambios
        if tier_changes:
            teams = read_all_teams()
            for assignment_id, new_tier in tier_changes.items():
                assignment = read_assignment(assignment_id)
                if assignment:
                    assignment.tier = new_tier
                    # Actualizar horas estimadas basado en el nuevo tier
                    team = teams.get(assignment.team_id)
                    if team:
                        assignment.estimated_hours = team.get_hours_per_person_for_tier(new_tier)
                    update_assignment(assignment)
        
        # Actualizar devs asignados si hay cambios
        if dev_changes:
            for assignment_id, new_devs in dev_changes.items():
                assignment = read_assignment(assignment_id)
                if assignment:
                    assignment.devs_assigned = new_devs
                    update_assignment(assignment)
        
        # Actualizar horas estimadas personalizadas si hay cambios
        if custom_hours_changes:
            for assignment_id, new_custom_hours in custom_hours_changes.items():
                assignment = read_assignment(assignment_id)
                if assignment:
                    assignment.custom_estimated_hours = new_custom_hours
                    update_assignment(assignment)
        
        st.success(f"✅ Proyecto '{project.name}' actualizado")
        st.rerun()
    except Exception as e:
        st.error(f"Error guardando cambios: {e}")


def _create_new_project(pname, start, due_with_qa, 
                       initial_total_hours, initial_active, projects, tier_config=None, dev_config=None):
    """Crea nuevo proyecto con validaciones"""
    try:
        if due_with_qa < start:
            st.error("❌ La fecha límite con QA debe ser posterior a la fecha de inicio")
            return
        
        next_priority = max([p.priority for p in projects.values()], default=0) + 1
        
        new_project = Project(
            id=0,
            name=pname,
            priority=next_priority,
            start_date=start,
            due_date_wo_qa=start,  # Usar start_date como valor por defecto
            due_date_with_qa=due_with_qa,
            phase="draft",
            active=initial_active,
            horas_trabajadas=0,
            horas_totales_estimadas=initial_total_hours,
            fecha_inicio_real=date.today() if initial_active else None
        )
        
        proj_id = create_project(new_project)
        _create_default_assignments(proj_id, pname, next_priority, start, tier_config, dev_config)
        
        st.success(f"✅ Proyecto '{pname}' creado exitosamente")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error creando proyecto: {e}")


def _create_default_assignments(proj_id, pname, priority, start, tier_config=None, dev_config=None):
    """Crea asignaciones por defecto para todos los equipos con tiers y devs configurados"""
    try:
        teams = read_all_teams()
        for team_id, team in teams.items():
            # Usar tier configurado o el máximo disponible como fallback
            if tier_config and team_id in tier_config:
                selected_tier = tier_config[team_id]
            else:
                selected_tier = max(team.tier_capacities.keys()) if team.tier_capacities else 1
            
            # Usar devs configurados o 1.0 como fallback
            if dev_config and team_id in dev_config:
                selected_devs = dev_config[team_id]
            else:
                selected_devs = 1.0
            
            # Calcular horas estimadas basado en el tier
            estimated_hours = team.get_hours_per_person_for_tier(selected_tier)
            
            assignment = Assignment(
                id=0,
                project_id=proj_id,
                project_name=pname,
                project_priority=priority,
                team_id=team_id,
                team_name=team.name,
                tier=selected_tier,
                devs_assigned=selected_devs,
                max_devs=float(team.total_devs),
                estimated_hours=estimated_hours,
                ready_to_start_date=start,
                assignment_start_date=start,
                status="Not Started",
                pending_hours=0,
                paused_on=None,
                custom_estimated_hours=None
            )
            create_assignment(assignment)
    except Exception as e:
        st.error(f"Error creando asignaciones por defecto: {e}")


def _delete_project_by_name(project_name):
    """Elimina proyecto por nombre"""
    try:
        if delete_project_by_name(project_name):
            st.success(f"Proyecto '{project_name}' eliminado.")
            st.rerun()
        else:
            st.error(f"Proyecto '{project_name}' no encontrado.")
    except Exception as e:
        st.error(f"Error eliminando proyecto: {e}")
