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

# Límites de fechas para evitar errores de rango
MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2100, 12, 31)


def validate_date_range(target_date: date, context: str = "") -> date:
    """Valida que una fecha esté en el rango válido de Python"""
    if target_date < MIN_DATE:
        logger.warning(f"Fecha {target_date} fuera de rango mínimo en {context}. Ajustando a {MIN_DATE}")
        return MIN_DATE
    if target_date > MAX_DATE:
        logger.error(f"Fecha {target_date} fuera de rango máximo en {context}. Ajustando a {MAX_DATE}")
        return MAX_DATE
    return target_date


def safe_business_day_calculation(base_date: date, days_offset: int, context: str = "") -> date:
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

PHASE_ORDER = ["Arch", "Model", "Dev", "Dqa"]

def render_monitoring():
    st.header("Delivery Forecast")

    # 1) Load ALL projects (active and paused) with effective priority
    df_proj = pd.read_sql(
        sa.select(
            projects_table.c.id.label("project_id"),
            projects_table.c.name.label("project_name"),
            projects_table.c.priority,
            projects_table.c.active
        ).order_by(projects_table.c.active.desc(), projects_table.c.priority),  # Active first, then by priority
        engine
    )
    if df_proj.empty:
        st.info("No projects to monitor.")
        return

    # Add drag and drop priority management
    _render_priority_management(df_proj)
    
    st.markdown("---")

    # 2) Load teams capacity
    df_teams = pd.read_sql(
        sa.select(
            teams_table.c.id,
            teams_table.c.total_devs,
            teams_table.c.busy_devs
        ),
        engine
    ).set_index("id")

    # 3) Load assignments + tier capacity
    assign_q = (
        sa.select(
            project_team_assignments_table.c.project_id.label("project_id"),
            projects_table.c.name         .label("project_name"),
            project_team_assignments_table.c.team_id,
            teams_table.c.name            .label("phase"),
            project_team_assignments_table.c.tier,
            project_team_assignments_table.c.devs_assigned,
            project_team_assignments_table.c.estimated_hours,
            tier_capacity_table.c.hours_per_person
        )
        .select_from(
            project_team_assignments_table
            .join(projects_table,
                  project_team_assignments_table.c.project_id == projects_table.c.id)
            .join(teams_table,
                  project_team_assignments_table.c.team_id    == teams_table.c.id)
            .join(tier_capacity_table,
                  sa.and_(
                      project_team_assignments_table.c.team_id == tier_capacity_table.c.team_id,
                      project_team_assignments_table.c.tier    == tier_capacity_table.c.tier
                  ))
        )
    )
    df_assign = pd.read_sql(assign_q, engine)
    if df_assign.empty:
        st.info("No assignments for monitoring.")
        return

    # 4) Prepare simulation structures
    active_by_team = {tid: [] for tid in df_teams.index}
    project_next_free = {}
    df = df_assign.merge(df_proj[["project_id", "priority"]], on="project_id", how="left")
    df["phase_order"] = df["phase"].map({p: i for i, p in enumerate(PHASE_ORDER)})
    df = df.sort_values(["priority", "phase_order"])

    records = []
    today = date.today()

    # 5) Simulate each assignment
    for r in df.itertuples():
        # always allow start no earlier than today
        ready = today

        pid        = r.project_id
        tid        = r.team_id
        total_devs = df_teams.loc[tid, "total_devs"]
        busy0      = df_teams.loc[tid, "busy_devs"]
        devs_req   = r.devs_assigned

        # hours needed: manual override or tier * devs
        if r.estimated_hours and r.estimated_hours > 0:
            hours_needed = r.estimated_hours
        else:
            hours_needed = r.hours_per_person * devs_req

        # respect project dependency
        if pid in project_next_free:
            ready = max(ready, project_next_free[pid])

        # compute days needed
        hours_per_day = devs_req * 8
        days_needed   = math.ceil(hours_needed / hours_per_day)

        def fits(s: date) -> bool:
            """Check that for each business day in [s, s+days_needed) capacity allows devs_req."""
            try:
                s = validate_date_range(s, f"fits() start date for team {tid}")
                for i in range(days_needed):
                    day = safe_business_day_calculation(s, i, f"fits() day {i} for team {tid}")
                    used = busy0 + sum(a["devs"] for a in active_by_team[tid]
                                       if a["start"] <= day <= a["end"])
                    if used + devs_req > total_devs:
                        return False
                return True
            except Exception as e:
                logger.error(f"Error en fits() para team {tid}: {e}")
                return False

        # find earliest start where it fits
        start_sim = validate_date_range(ready, f"initial start_sim for team {tid}")
        max_iterations = 180  # Límite para evitar bucles infinitos
        iterations = 0
        
        while not fits(start_sim) and iterations < max_iterations:
            iterations += 1
            logger.debug(f"Iteración {iterations} buscando slot para team {tid}, fecha actual: {start_sim}")
            
            try:
                # advance to the next free day for this team
                overlapping = [a["end"] for a in active_by_team[tid]
                               if a["start"] <= start_sim <= a["end"]]
                if overlapping:
                    min_end = min(overlapping)
                    start_sim = safe_business_day_calculation(min_end, 1, f"overlapping advance team {tid}")
                else:
                    start_sim = safe_business_day_calculation(start_sim, 1, f"normal advance team {tid}")
            except Exception as e:
                logger.error(f"Error avanzando fecha para team {tid}: {e}")
                # Fallback: usar fecha actual + 1 día
                from datetime import timedelta
                start_sim = validate_date_range(start_sim + timedelta(days=1), f"fallback advance team {tid}")
        
        if iterations >= max_iterations:
            logger.error(f"No se pudo encontrar slot para team {tid} después de {max_iterations} iteraciones")
            # Usar fecha de ready como fallback
            start_sim = validate_date_range(ready, f"max_iterations fallback team {tid}")

        # compute end date
        try:
            start_sim = validate_date_range(start_sim, f"final start_sim for team {tid}")
            end_ts = pd.Timestamp(start_sim) + BusinessDay(days_needed) - BusinessDay(1)
            end_sim = validate_date_range(end_ts.date(), f"end_sim for team {tid}")
            next_free = safe_business_day_calculation(end_sim, 1, f"project_next_free for project {pid}")
        except Exception as e:
            logger.error(f"Error calculando fechas de fin para team {tid}: {e}")
            # Fallback seguro
            from datetime import timedelta
            end_sim = validate_date_range(start_sim + timedelta(days=days_needed), f"fallback end_sim team {tid}")
            next_free = validate_date_range(end_sim + timedelta(days=1), f"fallback next_free project {pid}")

        # register this assignment
        active_by_team[tid].append({
            "start": start_sim,
            "end":   end_sim,
            "devs":  devs_req
        })
        project_next_free[pid] = next_free

        records.append({
            "project_id":   pid,
            "project_name": r.project_name,
            "phase":        r.phase,
            "start":        start_sim,
            "end":          end_sim
        })

    sched = pd.DataFrame(records)

    # 6) Summarize one row per project
    output = []
    for pid, grp in sched.groupby("project_id"):
        name = grp.iloc[0]["project_name"]
        arch = grp[grp.phase == "Arch"].iloc[0]
        dqa  = grp[grp.phase == "Dqa"].iloc[-1]

        start_date = arch["start"]
        est_end    = dqa["end"]

        # determine current state
        if today < start_date:
            state = "Not started"
        else:
            state = "Done" if today > est_end else "Waiting"
            for phase in PHASE_ORDER:
                ph = grp[grp.phase == phase]
                if not ph.empty:
                    s, e = ph.iloc[0][["start", "end"]]
                    if s <= today <= e:
                        state = phase
                        break

        output.append({
            "Project":  name,
            "State":    state,
            "Start":    start_date,
            "Est. End": est_end
        })

    st.table(pd.DataFrame(output))


def _render_priority_management(df_proj):
    """Renderiza interfaz de gestión de prioridades con drag and drop"""
    from st_draggable_list import DraggableList
    
    st.subheader("🔄 Gestión de Prioridades")
    
    # Preparar items para drag and drop con prioridad efectiva
    items = []
    for _, row in df_proj.iterrows():
        state_symbol = "🟢" if row.active else "⏸️"
        state_text = "Activo" if row.active else "Pausado"
        items.append({
            "id": row.project_id,
            "name": f"({row.priority}) {row.project_name} - {state_symbol} {state_text}"
        })
    
    new_order = DraggableList(items, text_key="name", key="monitoring_priority_sort")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Guardar Nuevo Orden", key="save_monitoring_priorities"):
            try:
                # Actualizar prioridades en la base de datos
                with engine.begin() as conn:
                    for idx, item in enumerate(new_order, start=1):
                        conn.execute(
                            projects_table.update()
                            .where(projects_table.c.id == item["id"])
                            .values(priority=idx)
                        )
                st.success("✅ Prioridades actualizadas en Monitoring.")
                st.rerun()
            except Exception as e:
                st.error(f"Error actualizando prioridades: {e}")
    
    with col2:
        st.info("💡 Arrastra los proyectos para cambiar su prioridad. Los activos siempre tienen prioridad sobre los pausados.")
