"""
Módulo de gestión de planes guardados
Permite ver, activar y desactivar planes persistentes
"""

import streamlit as st
import logging
from datetime import datetime, date
from typing import List, Optional

from ..common.plans_crud import (
    list_plans, get_active_plan, activate_plan, deactivate_plan,
    delete_plan, get_plan_priorities
)
from ..common.plan_utils import get_active_assignments
from ..common.models import Plan

logger = logging.getLogger(__name__)


def render_plans():
    """Renderiza la interfaz de gestión de planes"""
    st.header("📋 Gestión de Planes Guardados")
    
    # Obtener planes existentes
    plans = list_plans(limit=20)
    active_plan = get_active_plan()
    
    if not plans:
        st.info("No hay planes guardados aún. Los planes se crean automáticamente cuando se ejecuta una simulación.")
        return
    
    # Mostrar plan activo actual
    if active_plan:
        st.success(f"🟢 **Plan Activo:** {active_plan.name}")
        st.caption(f"Creado: {active_plan.created_at.strftime('%d/%m/%Y %H:%M')} | "
                  f"Proyectos: {active_plan.total_projects} | "
                  f"Asignaciones: {active_plan.total_assignments}")

        active_assignments_progress = get_active_assignments(active_plan, date.today())

        if active_assignments_progress:
            st.write("**Fases Activas del Plan:**")
            for progress in active_assignments_progress:
                assignment = progress["assignment"]
                st.write(f"**Proyecto {assignment.project_name} - {assignment.team_name} (Tier {assignment.tier})**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Progreso", f"{progress['progress_percentage']:.2f}%")
                with col2:
                    st.metric("Horas Trabajadas", f"{progress['worked_hours']:.2f}")
                with col3:
                    st.metric("Horas Restantes", f"{progress['remaining_hours']:.2f}")
        else:
            st.info("No hay fases activas en el plan para la fecha de hoy.")

    else:
        st.warning("⚠️ No hay ningún plan activo actualmente")
    
    st.divider()
    
    # Lista de planes
    st.subheader("📋 Planes Disponibles")
    
    for plan in plans:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                # Indicador de estado
                status_icon = "🟢" if plan.is_active else "⚪"
                st.write(f"{status_icon} **{plan.name}**")
                if plan.description:
                    st.caption(plan.description)
            
            with col2:
                st.write(f"📅 {plan.created_at.strftime('%d/%m/%Y %H:%M')}")
                st.caption(f"Proyectos: {plan.total_projects} | Asignaciones: {plan.total_assignments}")
            
            with col3:
                if not plan.is_active:
                    if st.button("🔄 Activar", key=f"activate_{plan.id}", 
                                help="Activar este plan y aplicar sus prioridades"):
                        if activate_plan(plan.id):
                            st.success(f"Plan '{plan.name}' activado exitosamente")
                            st.rerun()
                        else:
                            st.error("Error activando el plan")
                else:
                    if st.button("⏸️ Desactivar", key=f"deactivate_{plan.id}",
                                help="Desactivar este plan"):
                        if deactivate_plan(plan.id):
                            st.success(f"Plan '{plan.name}' desactivado")
                            st.rerun()
                        else:
                            st.error("Error desactivando el plan")
            
            with col4:
                # Botón de detalles
                if st.button("👁️ Ver", key=f"view_{plan.id}", help="Ver detalles del plan"):
                    st.session_state[f"show_details_{plan.id}"] = True
                
                # Botón de eliminar (solo para planes inactivos)
                if not plan.is_active:
                    if st.button("🗑️", key=f"delete_{plan.id}", help="Eliminar plan"):
                        if st.session_state.get(f"confirm_delete_{plan.id}", False):
                            if delete_plan(plan.id):
                                st.success(f"Plan '{plan.name}' eliminado")
                                st.rerun()
                            else:
                                st.error("Error eliminando el plan")
                        else:
                            st.session_state[f"confirm_delete_{plan.id}"] = True
                            st.warning("Haz clic nuevamente para confirmar eliminación")
            
            # Mostrar detalles si se solicitó
            if st.session_state.get(f"show_details_{plan.id}", False):
                from ..common.plans_crud import get_plan_by_id
                detailed_plan = get_plan_by_id(plan.id)
                if detailed_plan:
                    _show_plan_details(detailed_plan)
                else:
                    st.error(f"No se pudieron cargar los detalles del plan {plan.id}")

                if st.button("❌ Cerrar detalles", key=f"close_{plan.id}"):
                    st.session_state[f"show_details_{plan.id}"] = False
                    st.rerun()
            
            st.divider()


def _show_plan_details(plan: Plan):
    """Muestra los detalles de un plan específico"""
    st.subheader(f"📋 Detalles del Plan: {plan.name}")
    
    # Información general
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Información General:**")
        st.write(f"• **ID:** {plan.id}")
        st.write(f"• **Estado:** {'🟢 Activo' if plan.is_active else '⚪ Inactivo'}")
        st.write(f"• **Fecha de creación:** {plan.created_at.strftime('%d/%m/%Y %H:%M:%S')}")
        st.write(f"• **Fecha de simulación:** {plan.simulation_date.strftime('%d/%m/%Y')}")
    
    with col2:
        st.write("**Estadísticas:**")
        st.write(f"• **Total de proyectos:** {plan.total_projects}")
        st.write(f"• **Total de asignaciones:** {plan.total_assignments}")
        st.write(f"• **Checksum:** {plan.checksum[:12]}...")
    
    if plan.description:
        st.write("**Descripción:**")
        st.write(plan.description)
    
    # Obtener prioridades del plan
    priorities = get_plan_priorities(plan.id)
    if priorities:
        st.write("**Prioridades específicas del plan:**")
        priority_data = []
        for project_id, priority in sorted(priorities.items(), key=lambda x: x[1]):
            # Buscar el nombre del proyecto en las asignaciones
            project_name = "Proyecto desconocido"
            for assignment in plan.assignments:
                if assignment.project_id == project_id:
                    project_name = assignment.project_name
                    break
            priority_data.append({
                "Proyecto": project_name,
                "ID": project_id,
                "Prioridad": priority
            })
        
        if priority_data:
            st.dataframe(priority_data, use_container_width=True)

    # Mostrar asignaciones si están cargadas
    if plan.assignments:
        st.write("**Asignaciones del plan:**")
        assignment_data = []
        for assignment in plan.assignments[:10]:  # Mostrar solo las primeras 10
            assignment_data.append({
                "Proyecto": assignment.project_name,
                "Equipo": assignment.team_name,
                "Tier": assignment.tier,
                "Devs": assignment.devs_assigned,
                "Horas": assignment.estimated_hours,
                "Inicio": assignment.calculated_start_date.strftime('%d/%m/%Y') if assignment.calculated_start_date else "N/A",
                "Fin": assignment.calculated_end_date.strftime('%d/%m/%Y') if assignment.calculated_end_date else "N/A",
                "Prioridad Plan": assignment.priority_order or assignment.project_priority
            })
        
        if assignment_data:
            st.dataframe(assignment_data, use_container_width=True)
            if len(plan.assignments) > 10:
                st.caption(f"Mostrando 10 de {len(plan.assignments)} asignaciones")


def show_plan_creation_success(plan: Plan):
    """Muestra mensaje de éxito cuando se crea un plan"""
    st.success(f"✅ Plan '{plan.name}' guardado exitosamente")
    st.info(f"📊 **Resumen:** {plan.total_projects} proyectos, {plan.total_assignments} asignaciones")
    
    if plan.is_active:
        st.success("🟢 Este plan está ahora activo y sus prioridades han sido aplicadas")