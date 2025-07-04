"""
Módulo de gestión de planes guardados
Permite ver, activar y desactivar planes persistentes
"""

import streamlit as st
import logging
from datetime import date
from ..common.plans_crud import (
    list_plans, get_active_plan, activate_plan, deactivate_plan,
    delete_plan, get_plan_by_id
)
from ..common.plan_utils import get_active_assignments
from ..common.models import Plan

logger = logging.getLogger(__name__)

def render_plans():
    """Renderiza la interfaz de gestión de planes con un selectbox."""
    st.header("📋 Gestión de Planes Guardados")

    active_plan = get_active_plan()
    if active_plan:
        st.success(f"🟢 **Plan Activo:** {active_plan.name}")
        _display_active_plan_status(active_plan)
    else:
        st.warning("⚠️ No hay ningún plan activo actualmente.")
    
    st.divider()

    plans = list_plans(limit=100)
    if not plans:
        st.info("No hay planes guardados aún. Los planes se crean en la pestaña de simulación.")
        return

    # Crear un mapa de nombres de plan a IDs para el selectbox
    plan_options = {plan.name: plan.id for plan in plans}
    
    # Determinar la selección inicial del selectbox
    # Si hay un plan activo, lo seleccionamos. Si no, el primero de la lista.
    active_plan_name = active_plan.name if active_plan else list(plan_options.keys())[0]
    
    selected_plan_name = st.selectbox(
        "Selecciona un plan para ver sus detalles",
        options=list(plan_options.keys()),
        index=list(plan_options.keys()).index(active_plan_name)
    )

    if selected_plan_name:
        selected_plan_id = plan_options[selected_plan_name]
        # Usamos un spinner mientras cargamos los detalles completos del plan
        with st.spinner(f"Cargando detalles de '{selected_plan_name}'..."):
            # get_plan_by_id carga toda la info, incluyendo asignaciones
            selected_plan = get_plan_by_id(selected_plan_id)
        
        if selected_plan:
            st.subheader(f"Detalles del Plan: {selected_plan.name}")
            _render_plan_details_and_actions(selected_plan)
        else:
            st.error("No se pudieron cargar los detalles del plan seleccionado.")

def _display_active_plan_status(active_plan: Plan):
    """Muestra el estado y progreso del plan activo."""
    st.caption(f"Creado: {active_plan.created_at.strftime('%d/%m/%Y %H:%M')} | "
               f"Proyectos: {active_plan.total_projects} | "
               f"Asignaciones: {active_plan.total_assignments}")

    progress_info = get_active_assignments(active_plan, date.today())
    if progress_info:
        with st.expander("Ver progreso de fases activas"):
            for progress in progress_info:
                assign = progress["assignment"]
                st.write(f"**{assign.project_name} - {assign.team_name} (Tier {assign.tier})**")
                cols = st.columns(3)
                cols[0].metric("Progreso", f"{progress['progress_percentage']:.1f}%")
                cols[1].metric("Horas Trabajadas", f"{progress['worked_hours']:.1f}")
                cols[2].metric("Horas Restantes", f"{progress['remaining_hours']:.1f}")
    else:
        st.info("No hay fases activas en el plan para la fecha de hoy.")

def _render_plan_details_and_actions(plan: Plan):
    """Muestra los detalles de un plan y los botones de acción."""
    
    # --- Botones de Acción ---
    cols = st.columns(3)
    with cols[0]:
        if not plan.is_active:
            if st.button("🔄 Activar Plan", key=f"activate_{plan.id}", use_container_width=True):
                if activate_plan(plan.id):
                    st.success(f"Plan '{plan.name}' activado.")
                    st.rerun()
                else:
                    st.error("Error al activar el plan.")
        else:
            if st.button("⏸️ Desactivar Plan", key=f"deactivate_{plan.id}", use_container_width=True):
                if deactivate_plan(plan.id):
                    st.success(f"Plan '{plan.name}' desactivado.")
                    st.rerun()
                else:
                    st.error("Error al desactivar.")

    with cols[1]:
        # Lógica para el botón de eliminar con confirmación
        confirm_key = f"confirm_delete_{plan.id}"
        if st.session_state.get(confirm_key, False):
            if st.button("🚨 Confirmar Eliminación", key=f"delete_{plan.id}", use_container_width=True, type="primary"):
                if delete_plan(plan.id):
                    st.success(f"Plan '{plan.name}' eliminado.")
                    del st.session_state[confirm_key]
                    st.rerun()
                else:
                    st.error("Error al eliminar.")
                    del st.session_state[confirm_key]
        elif not plan.is_active:
            st.button("🗑️ Eliminar Plan", key=f"ask_delete_{plan.id}", use_container_width=True, on_click=lambda: st.session_state.update({confirm_key: True}))

    # --- Pestañas con Detalles del Plan ---
    tab_info, tab_priorities, tab_assignments = st.tabs(["ℹ️ Información", "🎯 Prioridades", "📋 Asignaciones"])

    with tab_info:
        _show_general_info(plan)
    
    with tab_priorities:
        _show_plan_priorities(plan)

    with tab_assignments:
        _show_plan_assignments(plan)


def _show_general_info(plan: Plan):
    """Muestra la información general del plan."""
    st.write(f"**Descripción:** {plan.description or 'No disponible'}")
    cols = st.columns(2)
    cols[0].metric("Fecha de Creación", plan.created_at.strftime('%d/%m/%Y %H:%M'))
    cols[1].metric("Fecha de Simulación Base", plan.simulation_date.strftime('%d/%m/%Y'))
    cols[0].metric("Total Proyectos", plan.total_projects)
    cols[1].metric("Total Asignaciones", plan.total_assignments)
    st.caption(f"Checksum: {plan.checksum[:12]}...")


def _show_plan_priorities(plan: Plan):
    """Muestra las prioridades de los proyectos en el plan."""
    from ..common.plans_crud import get_plan_priorities
    priorities = get_plan_priorities(plan.id)
    if not priorities:
        st.info("Este plan no tiene prioridades específicas guardadas.")
        return

    # Crear un mapa de ID de proyecto a nombre para una búsqueda más fácil
    project_names = {assign.project_id: assign.project_name for assign in plan.assignments}
    
    priority_data = []
    for project_id, priority in sorted(priorities.items(), key=lambda item: item[1]):
        priority_data.append({
            "Prioridad": priority,
            "Proyecto": project_names.get(project_id, f"ID: {project_id}")
        })
    
    if priority_data:
        st.dataframe(priority_data, use_container_width=True, hide_index=True)


def _show_plan_assignments(plan: Plan):
    """Muestra la tabla de asignaciones del plan."""
    if not plan.assignments:
        st.info("No hay datos de asignaciones para este plan.")
        return
        
    assignment_data = [{
        "Proyecto": a.project_name,
        "Equipo": a.team_name,
        "Tier": a.tier,
        "Inicio": a.calculated_start_date.strftime('%d/%m/%Y') if a.calculated_start_date else "N/A",
        "Fin": a.calculated_end_date.strftime('%d/%m/%Y') if a.calculated_end_date else "N/A",
        "Horas": a.estimated_hours,
        "Devs": a.devs_assigned
    } for a in sorted(plan.assignments, key=lambda x: (x.project_priority, x.tier))]
    
    st.dataframe(assignment_data, use_container_width=True, hide_index=True)


def show_plan_creation_success(plan: Plan):
    """Muestra mensaje de éxito cuando se crea un plan."""
    st.success(f"✅ Plan '{plan.name}' guardado exitosamente")
    st.info(f"📊 **Resumen:** {plan.total_projects} proyectos, {plan.total_assignments} asignaciones")
    
    if plan.is_active:
        st.success("🟢 Este plan está ahora activo y sus prioridades han sido aplicadas")