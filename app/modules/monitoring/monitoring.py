# app/modules/monitoring/monitoring.py

import streamlit as st
import pandas as pd
import sqlalchemy as sa
import math
import logging
from datetime import date
from pandas.tseries.offsets import BusinessDay
from sqlalchemy import func

# Configurar logging para debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar utilidades comunes
from ..common.constants import MIN_DATE, MAX_DATE, PHASE_ORDER
from ..common.date_utils import validate_date_range, safe_business_day_calculation
from ..common.ui_utils import setup_draggable_list


def safe_business_day_calculation_legacy(base_date: date, days_offset: int, context: str = "") -> date:
    """Calcula días hábiles de manera segura, evitando fechas fuera de rango"""
    try:
        # Validar fecha base
        base_date = validate_date_range(base_date, f"base_date in {context}")
        
        # Calcular nueva fecha
        result_timestamp = pd.Timestamp(base_date) + BusinessDay(days_offset)
        result_date = result_timestamp.date()
        
        # Validar resultado
        return validate_date_range(result_date, f"result in {context}")
        
    except Exception as e:
        logger.error(f"Error en cálculo de días hábiles en {context}: {e}")
        logger.error(f"  base_date: {base_date}, days_offset: {days_offset}")
        
        # Fallback seguro
        from datetime import timedelta
        fallback_date = base_date + timedelta(days=days_offset)
        return validate_date_range(fallback_date, f"fallback in {context}")
from ..common.db import (
    engine,
    projects_table,
    teams_table,
    project_team_assignments_table,
    tier_capacity_table
)



def render_monitoring():
    logger.info("🔍 DEBUG: INICIANDO render_monitoring()")
    st.header("Delivery Forecast")

    # Importar funciones del módulo simulation
    from ..simulation.simulation import render_simulation_for_monitoring
    logger.info("🔍 DEBUG: Importación de render_simulation_for_monitoring exitosa")
    
    # Verificar que hay proyectos
    df_proj = pd.read_sql(
        sa.select(
            projects_table.c.id.label("project_id"),
            projects_table.c.name.label("project_name"),
            projects_table.c.priority,
            projects_table.c.active
        ).order_by(projects_table.c.active.desc(), projects_table.c.priority),
        engine
    )
    if df_proj.empty:
        st.info("No projects to monitor.")
        return

    # Usar el módulo simulation para generar el cronograma con gestión de prioridades integrada
    
    
    # Ejecutar simulación integrada con gestión de prioridades
    _render_simulation_with_plans_integration()





def _get_current_priorities_from_db():
    """Obtiene las prioridades actuales desde la base de datos"""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                sa.select(
                    projects_table.c.id,
                    projects_table.c.priority
                ).order_by(projects_table.c.priority)
            ).fetchall()
            
            return {row.id: row.priority for row in result}
    except Exception as e:
        logger.error(f"Error obteniendo prioridades de DB: {e}")
        return {}






def _render_simulation_with_plans_integration():
    """Renderiza simulación integrada con funcionalidad de planes y persistencia"""
    logger.info("🔍 DEBUG: Iniciando _render_simulation_with_plans_integration")
    
    try:
        from ..simulation.simulation import render_simulation_for_monitoring
        logger.info("🔍 DEBUG: Importación exitosa de render_simulation_for_monitoring")
        
        # Ejecutar simulación usando la función pública del módulo simulation
        # Esta función renderiza directamente el contenido de la simulación
        logger.info("🔍 DEBUG: Llamando a render_simulation_for_monitoring()")
        simulation_result = render_simulation_for_monitoring()
        
        # Manejar el resultado correctamente
        if simulation_result is None or len(simulation_result) != 3:
            logger.info("🔍 DEBUG: render_simulation_for_monitoring retornó None o formato incorrecto")
            return
            
        result, simulation_input, priority_overrides = simulation_result
        logger.info(f"🔍 DEBUG: render_simulation_for_monitoring retornó: result={result is not None}, simulation_input={simulation_input is not None}, priority_overrides={priority_overrides is not None}")
        
        # Si hay resultados, mostrar la sección de guardado de planes
        if result is not None and simulation_input is not None:
            st.markdown("---")
            _render_simple_save_section(result, simulation_input, priority_overrides)
        # La sección de guardado ha sido removida para implementar el guardado automático.
        pass
            
    except Exception as e:
        logger.error(f"🔍 ERROR en _render_simulation_with_plans_integration: {e}")
        st.error(f"Error en simulación: {e}")
        return


def _render_simple_save_section(result, simulation_input, priority_overrides):
    """Renderiza una sección simplificada para guardar planes"""
    st.subheader("💾 Guardar Plan")
    
    has_priority_changes = _has_priority_changes(priority_overrides)
    
    if has_priority_changes:
        st.info("💡 **Cambios de prioridad detectados**. Estos cambios se guardarán permanentemente junto con el plan.")
    
    with st.form("save_plan_monitoring"):
        plan_name = st.text_input(
            "Nombre del plan:",
            value=f"Plan {date.today().strftime('%B %Y')}",
            placeholder="Ej: Plan Julio 2025",
            help="Nombre descriptivo para este cronograma"
        )
        
        plan_description = st.text_area(
            "Descripción (opcional):",
            placeholder="Describe las características de este plan...",
            help="Información adicional sobre este cronograma"
        )
        
        save_button = st.form_submit_button("💾 Guardar Plan", type="primary")
    
    if save_button:
        if plan_name.strip():
            # Si hay cambios de prioridad, se pasan a la función de guardado.
            # Si no, se pasa None. La persistencia es implícita.
            _save_monitoring_plan(plan_name.strip(), plan_description.strip(), result, priority_overrides if has_priority_changes else None)
        else:
            st.error("❌ El nombre del plan es obligatorio")


def _save_monitoring_plan(name, description, result, priority_overrides=None):
    """Guarda el cronograma de monitoring como plan y persiste prioridades si existen"""
    from ..common.plans_crud import save_plan
    
    try:
        # Si hay cambios de prioridad, persistirlos primero
        if priority_overrides:
            _persist_priority_changes(priority_overrides)
            st.success("✅ **Prioridades actualizadas en la base de datos**")
        
        # Guardar el plan usando las funciones de plans_crud
        plan = save_plan(
            result=result,
            name=name,
            description=description,
            set_as_active=True,
            current_priorities=priority_overrides
        )
        
        success_message = f"✅ **Plan '{name}' guardado exitosamente**"
        if priority_overrides:
            success_message += " (con cambios de prioridad persistidos)"
        
        st.success(success_message)
        st.info(f"📋 Plan ID: {plan.id} | Fecha: {plan.simulation_date}")
        st.info("💡 El plan está ahora activo y disponible para comparaciones futuras")
        
        if st.button("🔬 Ver en Módulo Simulación"):
            st.switch_page("pages/simulation.py")
        
    except Exception as e:
        logger.error(f"Error guardando plan desde monitoring: {e}")
        st.error(f"❌ **Error guardando plan**: {e}")


def _has_priority_changes(priority_overrides):
    """Verifica si hay cambios de prioridad respecto a la base de datos"""
    if not priority_overrides:
        return False
    
    try:
        current_priorities = _get_current_priorities_from_db()
        
        for project_id, new_priority in priority_overrides.items():
            if current_priorities.get(project_id) != new_priority:
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error verificando cambios de prioridad: {e}")
        return False


def _persist_priority_changes(priority_overrides):
    """Persiste los cambios de prioridad en la base de datos"""
    try:
        with engine.begin() as conn:
            for project_id, new_priority in priority_overrides.items():
                conn.execute(
                    projects_table.update()
                    .where(projects_table.c.id == project_id)
                    .values(priority=new_priority)
                )
        logger.info(f"Prioridades persistidas: {priority_overrides}")
    except Exception as e:
        logger.error(f"Error persistiendo prioridades: {e}")
        raise
