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

PHASE_ORDER = ["Arch", "Model", "Dev", "Dqa"]

def render_monitoring():
    st.header("Delivery Forecast")

    # 1) Load projects by priority
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
            for i in range(days_needed):
                day = (pd.Timestamp(s) + BusinessDay(i)).date()
                used = busy0 + sum(a["devs"] for a in active_by_team[tid]
                                   if a["start"] <= day <= a["end"])
                if used + devs_req > total_devs:
                    return False
            return True

        # find earliest start where it fits
        start_sim = ready
        while not fits(start_sim):
            # advance to the next free day for this team
            overlapping = [a["end"] for a in active_by_team[tid]
                           if a["start"] <= start_sim <= a["end"]]
            if overlapping:
                start_sim = (pd.Timestamp(min(overlapping)) + BusinessDay(1)).date()
            else:
                start_sim = (pd.Timestamp(start_sim) + BusinessDay(1)).date()

        # compute end date
        end_ts = pd.Timestamp(start_sim) + BusinessDay(days_needed) - BusinessDay(1)
        end_sim = end_ts.date()

        # register this assignment
        active_by_team[tid].append({
            "start": start_sim,
            "end":   end_sim,
            "devs":  devs_req
        })
        project_next_free[pid] = (end_ts + BusinessDay(1)).date()

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
