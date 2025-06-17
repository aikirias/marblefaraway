# app/modules/monitoring/monitoring.py

import streamlit as st
import pandas as pd
import sqlalchemy as sa
import math
from datetime import date
from pandas.tseries.offsets import BusinessDay
from sqlalchemy import func
from modules.common.db import (
    engine,
    projects_table,
    teams_table,
    project_team_assignments_table,
    tier_capacity_table
)

# Define the order of phases
PHASE_ORDER = ["Arch", "Model", "Dev", "Dqa"]

def render_monitoring():
    st.header("Delivery Forecast")

    # 1) Load projects ordered by priority
    df_proj = pd.read_sql(
        sa.select(
            projects_table.c.id.label("project_id"),
            projects_table.c.name.label("project_name"),
            projects_table.c.priority
        ).order_by(projects_table.c.priority),
        engine
    )
    if df_proj.empty:
        st.info("No projects to monitor.")
        return

    # 2) Load assignments + tier capacity
    assign_q = (
        sa.select(
            project_team_assignments_table.c.project_id.label("project_id"),
            projects_table.c.name.label("project_name"),
            project_team_assignments_table.c.team_id,
            teams_table.c.name.label("phase"),
            project_team_assignments_table.c.tier,
            project_team_assignments_table.c.devs_assigned,
            project_team_assignments_table.c.estimated_hours,
            project_team_assignments_table.c.ready_to_start_date,
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

    # Convert ready_to_start_date to pure date to avoid Timestamp vs date comparisons
    df_assign["ready_to_start_date"] = (
        pd.to_datetime(df_assign["ready_to_start_date"])
          .dt.date
    )

    # 3) Simulate schedule
    team_next_free = {}    # team_id -> next free date (datetime.date)
    project_next_free = {} # project_id -> next free date

    # Merge priority and sort by priority + phase order
    df = df_assign.merge(
        df_proj[["project_id", "priority"]],
        on="project_id",
        how="left"
    )
    df["phase_order"] = df["phase"].map({p: i for i, p in enumerate(PHASE_ORDER)})
    df = df.sort_values(["priority", "phase_order"])

    records = []
    today = date.today()

    for r in df.itertuples():
        ready = r.ready_to_start_date           # already a datetime.date
        pid   = r.project_id
        tid   = r.team_id

        # Determine hours_needed
        if r.estimated_hours and r.estimated_hours > 0:
            hours_needed = r.estimated_hours
        else:
            hours_needed = r.hours_per_person * r.devs_assigned

        # Compute start date
        team_avail = team_next_free.get(tid, ready)
        proj_avail = project_next_free.get(pid, ready)
        start_sim = max(ready, team_avail, proj_avail)

        # Compute end date
        hours_per_day = r.devs_assigned * 8
        days_needed = math.ceil(hours_needed / hours_per_day)
        # BusinessDay arithmetic returns Timestamp, convert back to date
        end_ts = pd.Timestamp(start_sim) + BusinessDay(days_needed) - BusinessDay(1)
        end_sim = end_ts.date()

        # Update next free dates
        next_free = (end_ts + BusinessDay(1)).date()
        team_next_free[tid]    = next_free
        project_next_free[pid] = next_free

        records.append({
            "project_id":   pid,
            "project_name": r.project_name,
            "phase":        r.phase,
            "start":        start_sim,
            "end":          end_sim
        })

    sched = pd.DataFrame(records)

    # 4) Build summary: one row per project
    output = []
    for pid, grp in sched.groupby("project_id"):
        name = grp.iloc[0]["project_name"]
        arch = grp[grp.phase == "Arch"].iloc[0]
        dqa  = grp[grp.phase == "Dqa"].iloc[-1]

        start_date = arch["start"]
        est_end    = dqa["end"]

        # Determine current state
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

    df_out = pd.DataFrame(output)
    st.table(df_out)
