"""
Simulación de scheduling APE - Versión refactorizada
Eliminado código DEBUG y simplificadas las funciones complejas
"""

import streamlit as st
import pandas as pd
from datetime import date
from .scheduler import ProjectScheduler
from ..common.models import SimulationInput
import logging
from ..common.plans_crud import get_active_plan
from ..common.plan_utils import get_active_assignments, get_completed_phases

# Configurar logging
logger = logging.getLogger(__name__)

# Importar utilidades comunes
from ..common.ui_utils import DRAGGABLE_AVAILABLE, setup_draggable_list
from ..common.simulation_data_loader import load_simulation_input_from_db


def render_simulation():
    """Renderiza la interfaz de simulación de scheduling APE"""
    st.header("🔬 Simulador de Scheduling APE")
    st.markdown("Simula cronogramas usando **datos reales** de proyectos y equipos con capacidad de modificar prioridades temporalmente.")
    
    render_real_data_simulation()


def render_simulation_for_monitoring():
    """Renderiza simulación integrada para el módulo de monitoring"""
    # Cargar datos iniciales
    initial_data = _load_initial_data()
    if not initial_data:
        st.error("🔍 No se pudieron cargar los datos para la simulación")
        return None, None, None
    
    if not _validate_data(initial_data):
        st.error("🔍 Los datos no son válidos para ejecutar la simulación")
        return None, None, None
    
    # Controles de prioridad (solo para simulación, no afecta DB)
    st.markdown("### 🎯 Ajuste de Prioridades")
    st.info("💡 Arrastra los proyectos para cambiar su prioridad temporalmente. Los cambios solo afectan esta simulación hasta que decidas persistirlos.")
    
    priority_overrides = _render_priority_controls(initial_data)
    sim_start_date, auto_run = _render_simulation_config()
    
    # Determinar si ejecutar simulación
    should_run = _should_run_simulation(priority_overrides, auto_run)
    
    # Ejecutar simulación automáticamente la primera vez si no hay resultados
    if not should_run and not hasattr(st.session_state, 'simulation_result'):
        should_run = True
        st.info("🔄 Ejecutando simulación inicial...")
    
    if should_run:
        _execute_simulation(initial_data, priority_overrides, sim_start_date)
    
    # Mostrar resultados si existen
    if hasattr(st.session_state, 'simulation_result') and st.session_state.simulation_result is not None:
        result = st.session_state.simulation_result
        simulation_input = st.session_state.simulation_input_data
        
        # Renderizar el Gantt usando las funciones de simulation
        _render_gantt_chart(result, simulation_input)
        
        # Retornar los resultados para que monitoring pueda usarlos
        return result, simulation_input, priority_overrides
    else:
        st.info("🚀 Haz clic en 'Ejecutar Simulación' para generar el cronograma")
        return None, None, None


def render_real_data_simulation():
    """Renderiza simulación con datos reales de la DB con controles de prioridad"""
    # DEBUG: Log inicio de función
    logger.info("=== INICIANDO render_real_data_simulation ===")
    
    initial_data = _load_initial_data()
    if not initial_data:
        logger.error("❌ FALLO: _load_initial_data() retornó None - NO SE RENDERIZARÁN CONTROLES")
        st.error("🔍 DEBUG: Fallo en carga de datos iniciales - controles no disponibles")
        return
    
    logger.info("✅ ÉXITO: _load_initial_data() completado")
    
    if not _validate_data(initial_data):
        logger.error("❌ FALLO: _validate_data() retornó False - NO SE RENDERIZARÁN CONTROLES")
        st.error("🔍 DEBUG: Fallo en validación de datos - controles no disponibles")
        return
    
    logger.info("✅ ÉXITO: _validate_data() completado - RENDERIZANDO CONTROLES")
    
    # Control de prioridades y configuración
    priority_overrides = _render_priority_controls(initial_data)
    sim_start_date, auto_run = _render_simulation_config()
    
    # Determinar si ejecutar simulación
    should_run = _should_run_simulation(priority_overrides, auto_run)
    
    if should_run:
        _execute_simulation(initial_data, priority_overrides, sim_start_date)
    
    # Mostrar resultados si existen
    _render_simulation_results(priority_overrides)
    
    # Información de ayuda
    _render_help_section()


# ============================================================================
# FUNCIONES PRIVADAS DE UTILIDAD
# ============================================================================

def _load_initial_data():
    """Carga datos iniciales desde la base de datos"""
    logger.info("🔍 DEBUG: Iniciando _load_initial_data()")
    try:
        with st.spinner("Cargando datos desde la base de datos..."):
            logger.info("🔍 DEBUG: Llamando a load_simulation_input_from_db()")
            initial_data = load_simulation_input_from_db(date.today())
            
            if initial_data is None:
                logger.error("🔍 ERROR: load_simulation_input_from_db() retornó None")
                st.error("Error: No se pudieron cargar los datos desde la base de datos")
                return None
            
            logger.info(f"🔍 DEBUG: Datos cargados exitosamente - proyectos: {len(initial_data.projects)}, equipos: {len(initial_data.teams)}, asignaciones: {len(initial_data.assignments)}")
            return initial_data
    except Exception as e:
        logger.error(f"🔍 ERROR en _load_initial_data(): {e}")
        st.error(f"Error cargando datos: {str(e)}")
        return None


def _validate_data(initial_data):
    """Valida que los datos necesarios estén presentes"""
    if not initial_data.teams:
        st.error("No hay equipos en la base de datos. Crea equipos primero en la pestaña Teams.")
        return False
    
    if not initial_data.projects:
        st.error("No hay proyectos en la base de datos. Crea proyectos primero en la pestaña Projects.")
        return False
    
    if not initial_data.assignments:
        st.error("No hay asignaciones en la base de datos. Los proyectos necesitan asignaciones de equipos.")
        return False
    
    return True


def _render_priority_controls(initial_data):
    """Renderiza controles de prioridad para proyectos con lista draggable"""
    # No renderizar subheader aquí, se maneja desde la función que llama
    st.markdown("**Arrastra los proyectos para cambiar su prioridad y ver el impacto en el cronograma:**")
    
    priority_overrides = {}
    
    # CORRECCIÓN: Aplicar prioridad efectiva - activos primero, luego pausados
    def effective_priority(project):
        if project.is_active():
            return (0, project.priority)  # Activos primero
        else:
            return (1, project.priority)  # Pausados después
    
    projects_list = sorted(initial_data.projects.values(), key=effective_priority)
    
    if not DRAGGABLE_AVAILABLE:
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
        return priority_overrides
    
    # Preparar items para la lista draggable
    items = []
    for project in projects_list:
        state_symbol = "🟢" if project.is_active() else "⏸️"
        state_text = "Activo" if project.is_active() else "Pausado"
        items.append({
            "id": project.id,
            "name": f"({project.priority}) {project.name} - {state_symbol} {state_text}",
            "original_priority": project.priority
        })
    
    # Renderizar lista draggable
    new_order = setup_draggable_list(items, text_key="name", key="sim_priority_sort")
    
    # DEBUG: Validar que new_order no sea None
    logger.info(f"setup_draggable_list returned: {type(new_order)}, value: {new_order}")
    
    # CORRECCIÓN: Manejar caso donde setup_draggable_list devuelve None
    if new_order is None:
        logger.warning("setup_draggable_list returned None, using original items order")
        new_order = items
    
    # Calcular cambios de prioridad basados en el nuevo orden
    for idx, item in enumerate(new_order, start=1):
        original_priority = item["original_priority"]
        if idx != original_priority:
            priority_overrides[item["id"]] = idx
    
    # Mostrar información sobre cambios
    if priority_overrides:
        st.info(f"📝 Se detectaron {len(priority_overrides)} cambios de prioridad. La simulación se ejecutará automáticamente.")
    
    return priority_overrides


def _render_simulation_config():
    """Renderiza configuración de simulación"""
    logger.info("Iniciando renderizado de configuración de simulación")
    
    # Usar fecha actual como inicio de simulación
    sim_start_date = date.today()
    
    auto_run = st.checkbox("🔄 Ejecutar automáticamente al cambiar prioridades", value=True)
    
    return sim_start_date, auto_run


def _should_run_simulation(priority_overrides, auto_run):
    """Determina si debe ejecutarse la simulación"""
    manual_run = st.button("🚀 Ejecutar Simulación", key="run_real_sim")
    
    # Detectar cambios en prioridades
    last_overrides = st.session_state.get('last_priority_overrides', {})
    priorities_changed = priority_overrides != last_overrides
    
    # Ejecutar si es manual o automático con cambios
    should_run = manual_run or (auto_run and priorities_changed)
    
    if should_run:
        st.session_state['last_priority_overrides'] = priority_overrides.copy()
    
    return should_run


def _execute_simulation(initial_data, priority_overrides, sim_start_date):
    """Ejecuta la simulación con los parámetros dados"""
    try:
        # Preparar datos de simulación usando la fecha actual
        simulation_input = load_simulation_input_from_db(date.today())
        
        # Aplicar overrides de prioridad
        _apply_priority_overrides(simulation_input, priority_overrides)

        # --- NUEVA LÓGICA PARA AJUSTAR HORAS POR PLAN ACTIVO ---
        active_plan = get_active_plan()
        if active_plan:
            logger.info(f"Plan activo encontrado: '{active_plan.name}'. Ajustando horas de la simulación.")
            
            # Obtener el progreso de las asignaciones activas en el plan
            progress_info = get_active_assignments(active_plan, date.today())
            
            if progress_info:
                # Crear un mapa de project_id y team_id a horas restantes para búsqueda rápida
                progress_map = {
                    (p['assignment'].project_id, p['assignment'].team_id, p['assignment'].tier): p['remaining_hours']
                    for p in progress_info
                }
                
                logger.info(f"Progreso encontrado para {len(progress_map)} asignaciones activas.")

                # Actualizar las horas en simulation_input.assignments
                assignments_updated = 0
                for assignment in simulation_input.assignments:
                    key = (assignment.project_id, assignment.team_id, assignment.tier)
                    if key in progress_map:
                        remaining_hours = progress_map[key]
                        if remaining_hours < assignment.estimated_hours:
                            logger.info(f"  - Ajustando asignación: Proyecto {assignment.project_name} (Tier {assignment.tier})")
                            logger.info(f"    Horas originales: {assignment.estimated_hours}, Horas restantes: {remaining_hours}")
                            assignment.estimated_hours = remaining_hours
                            assignments_updated += 1
                
                if assignments_updated > 0:
                    st.success(f"Se ajustaron las horas de {assignments_updated} fases de proyecto según el progreso del plan activo.")
        # --- FIN DE LA NUEVA LÓGICA ---
        
        # Usar fecha actual como referencia temporal para el scheduler
        # CORRECCIÓN: Asegurar que la fecha de simulación no interfiera con fecha_inicio_real
        simulation_input.simulation_start_date = date.today()
        
        # Agregar logs para verificar fechas de inicio real
        logger.info("🔍 DEBUG FECHAS DE INICIO REAL EN PROYECTOS:")
        for project_id, project in simulation_input.projects.items():
            if project.fecha_inicio_real:
                logger.info(f"  - Proyecto {project.name} (ID: {project_id}): fecha_inicio_real = {project.fecha_inicio_real}")
            else:
                logger.info(f"  - Proyecto {project.name} (ID: {project_id}): SIN fecha_inicio_real")
        
        # Obtener fases completadas para anclarlas en la simulación
        completed_phases = get_completed_phases()
        # Ejecutar simulación
        with st.spinner("Ejecutando simulación..."):
            scheduler = ProjectScheduler()
            result = scheduler.simulate(simulation_input, completed_phases=completed_phases)
        
        # Guardar resultados
        st.session_state.simulation_result = result
        st.session_state.simulation_input_data = simulation_input
        
        st.success(f"✅ Simulación completada con {len(result.assignments)} asignaciones")
        
        
    except Exception as e:
        st.error(f"❌ Error ejecutando simulación: {str(e)}")
        st.session_state.simulation_result = None
        st.session_state.simulation_input_data = None


def _apply_priority_overrides(simulation_input, priority_overrides):
    """Aplica los cambios de prioridad a los datos de simulación"""
    for project_id, new_priority in priority_overrides.items():
        if project_id in simulation_input.projects:
            # Actualizar prioridad en project
            simulation_input.projects[project_id].priority = new_priority
            
            # Actualizar project_priority en assignments
            for assignment in simulation_input.assignments:
                if assignment.project_id == project_id:
                    assignment.project_priority = new_priority


def _render_simulation_results(priority_overrides):
    """Renderiza los resultados de la simulación"""
    if not hasattr(st.session_state, 'simulation_result') or st.session_state.simulation_result is None:
        return
    
    result = st.session_state.simulation_result
    simulation_input = st.session_state.simulation_input_data
    
    _render_metrics(simulation_input, result, priority_overrides)
    _render_gantt_chart(result, simulation_input)
    _render_detailed_results(result, simulation_input)


def _render_metrics(simulation_input, result, priority_overrides):
    """Renderiza métricas generales de la simulación"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Proyectos", len(simulation_input.projects))
    with col2:
        st.metric("👥 Equipos", len(simulation_input.teams))
    with col3:
        st.metric("🎯 Asignaciones", len(result.assignments))
    with col4:
        changes = len(priority_overrides)
        st.metric("🔄 Cambios de Prioridad", changes, delta=changes if changes > 0 else None)
    
    with col5:
        st.metric("📅 Fecha Base", "Hoy")


def _render_gantt_chart(result, simulation_input):
    """Renderiza el gráfico Gantt con vistas duales"""
    st.subheader("📅 Cronograma de Proyectos")
    
    # Control de vista
    view_type = st.radio(
        "📊 Tipo de Vista",
        options=["consolidated", "detailed"],
        format_func=lambda x: "📈 Vista Consolidada" if x == "consolidated" else "🔍 Vista Detallada",
        horizontal=True,
        key="gantt_view_type",
        help="Vista Consolidada: Timeline continuo por proyecto | Vista Detallada: Una línea por proyecto-fase"
    )
    
    try:
        from .gantt_views import prepare_gantt_data, get_project_colors_map, get_gantt_metrics
        from .gantt_config import get_gantt_figure
        
        # Preparar y mostrar datos
        gantt_df = prepare_gantt_data(result, view_type, simulation_input)
        
        if not gantt_df.empty:
            # DEBUG: Mostrar la tabla de datos del Gantt
            with st.expander("Ver datos de la simulación (Debug)"):
                st.dataframe(gantt_df)

            project_colors = get_project_colors_map(simulation_input.projects)
            # Usar fecha actual para el Gantt
            fig = get_gantt_figure(gantt_df, view_type, project_colors=project_colors, add_markers=True)
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                _render_gantt_metrics(gantt_df, view_type)
            else:
                st.warning("⚠️ No se pudo generar el gráfico Gantt")
        else:
            st.warning("⚠️ No hay datos suficientes para mostrar el cronograma")
            
    except Exception as e:
        st.error(f"❌ Error generando el cronograma: {str(e)}")


def _render_gantt_metrics(gantt_df, view_type):
    """Renderiza métricas específicas del Gantt"""
    from .gantt_views import get_gantt_metrics
    
    metrics = get_gantt_metrics(gantt_df, view_type)
    if not metrics:
        return
    
def _render_detailed_results(result, simulation_input):
    """Renderiza resultados detallados por proyecto"""
    st.subheader("📋 Resultado Detallado por Proyecto")
    
    for project_id, project in sorted(simulation_input.projects.items(), key=lambda x: x[1].priority):
        project_assignments = result.get_assignments_by_project(project_id)
        if not project_assignments:
            continue
        
        with st.expander(f"🏷️ {project.name} (Prioridad {project.priority})", expanded=True):
            _render_project_details(result, project, project_id, project_assignments)


def _render_project_details(result, project, project_id, project_assignments):
    """Renderiza detalles de un proyecto específico"""
    # Métricas del proyecto
    col1, col2, col3 = st.columns(3)
    
    project_start = result.get_project_start_date(project_id)
    project_end = result.get_project_end_date(project_id)
    
    with col1:
        start_text = project_start.strftime("%Y-%m-%d") if project_start else "No calculado"
        st.metric("📅 Inicio", start_text)
    
    with col2:
        end_text = project_end.strftime("%Y-%m-%d") if project_end else "No calculado"
        st.metric("🏁 Fin", end_text)
    
    with col3:
        if project_start and project_end:
            duration = (project_end - project_start).days
            st.metric("⏱️ Duración", f"{duration} días")
        else:
            st.metric("⏱️ Duración", "No calculado")
    
    # Estado del proyecto
    if project_end and project.due_date_with_qa:
        if project_end <= project.due_date_with_qa:
            days_early = (project.due_date_with_qa - project_end).days
            st.success(f"✅ A tiempo - Termina {days_early} días antes")
        else:
            delay_days = (project_end - project.due_date_with_qa).days
            st.error(f"⚠️ Con retraso - {delay_days} días de retraso")
    
    # Tabla de asignaciones
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





def _render_help_section():
    """Renderiza sección de ayuda"""
    with st.expander("ℹ️ Cómo usar la Simulación"):
        st.markdown("""
        **🎯 Control de Prioridades:**
        - Modifica las prioridades de los proyectos usando los controles numéricos
        - Los cambios son temporales y solo afectan la simulación
        - Prioridad 1 = Más alta, Prioridad 10 = Más baja
        
        **📅 Cronograma de Gantt:**
        - **Vista Consolidada** (por defecto): Muestra un timeline continuo por proyecto con fases en colores
        - **Vista Detallada**: Muestra una línea por cada proyecto-fase
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


def _render_save_plan_section(result, simulation_input):
    """Renderiza la sección para guardar el plan actual"""
    from ..common.plans_crud import save_plan, compare_plans, get_active_plan
    from datetime import date
    
    st.markdown("---")
    st.subheader("💾 Gestión de Planes")
    
    # Comparar con plan activo
    try:
        comparison = compare_plans(result)
        
        if comparison['has_changes']:
            if comparison['active_checksum'] is None:
                st.info("📝 No hay plan activo. Este será el primer plan guardado.")
            else:
                st.warning("⚠️ Se detectaron cambios respecto al plan activo.")
                for change in comparison['changes_detected']:
                    st.write(f"• {change}")
        else:
            st.success("✅ Sin cambios respecto al plan activo.")
    except Exception as e:
        st.error(f"Error comparando planes: {e}")
    
    # Formulario para guardar plan
    with st.form("save_plan_form"):
        st.markdown("#### Guardar Nuevo Plan")
        
        # Generar nombre automático basado en fecha
        default_name = f"Plan {date.today().strftime('%Y-%m-%d')}"
        
        plan_name = st.text_input(
            "Nombre del plan:", 
            value=default_name,
            help="Nombre descriptivo para identificar este plan"
        )
        
        plan_description = st.text_area(
            "Descripción (opcional):",
            help="Descripción detallada de los cambios o características de este plan"
        )
        
        set_as_active = st.checkbox(
            "Marcar como plan activo", 
            value=True,
            help="El plan activo se usa como referencia para comparaciones futuras"
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            save_button = st.form_submit_button("💾 Guardar Plan", type="primary")
        
        with col2:
            if save_button:
                if not plan_name.strip():
                    st.error("❌ El nombre del plan es obligatorio")
                else:
                    try:
                        with st.spinner("Guardando plan..."):
                            saved_plan = save_plan(
                                result=result,
                                name=plan_name.strip(),
                                description=plan_description.strip(),
                                set_as_active=set_as_active
                            )
                        
                        st.success(f"✅ Plan guardado exitosamente con ID: {saved_plan.id}")
                        st.info(f"📊 Plan contiene {saved_plan.total_assignments} asignaciones de {saved_plan.total_projects} proyectos")
                        
                        # Rerun para actualizar la comparación
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error guardando plan: {e}")
    
    # Mostrar información del plan activo
    try:
        active_plan = get_active_plan()
        if active_plan:
            st.markdown("#### 📋 Plan Activo Actual")
            st.info(f"**{active_plan.name}** (ID: {active_plan.id}) - Creado: {active_plan.created_at.strftime('%Y-%m-%d %H:%M')}")
            if active_plan.description:
                st.write(f"*{active_plan.description}*")
    except Exception as e:
        st.warning(f"No se pudo obtener información del plan activo: {e}")