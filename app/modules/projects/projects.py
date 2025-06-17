import streamlit as st
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import func
from modules.common.db import (
    engine,
    projects_table,
    teams_table,
    project_team_assignments_table,
    tier_capacity_table,
    run
)
from st_draggable_list import DraggableList

def render_projects():
    st.header("Project Management")

    # ————————————————————————————————
    # 1) Create New Project (with default assignments)
    # ————————————————————————————————
    st.subheader("Create New Project")
    pname = st.text_input("Project Name", key="proj_name")
    start = st.date_input("Start Date", key="proj_start")

    if st.button("Create Project") and pname:
        # Abrimos UNA transacción para todo el proceso
        with engine.begin() as conn:
            # 1. Insert project y recuperar su ID
            result = conn.execute(
                sa.insert(projects_table)
                .values(
                    name=pname,
                    priority=int(
                        conn.execute(
                            sa.select(func.coalesce(func.max(projects_table.c.priority), 0))
                        ).scalar()
                    ) + 1,
                    phase="",               # opcional si ya no lo usas
                    start_date=start,
                    due_date_wo_qa=start,
                    due_date_with_qa=start
                )
                .returning(projects_table.c.id)
            )
            proj_id = result.scalar()

            # 2. Para cada equipo, insertar assignment con defaults
            team_ids = conn.execute(
                sa.select(teams_table.c.id)
            ).scalars().all()

            for team_id in team_ids:
                max_tier = conn.execute(
                    sa.select(func.max(tier_capacity_table.c.tier))
                    .where(tier_capacity_table.c.team_id == team_id)
                ).scalar() or 1

                conn.execute(
                    project_team_assignments_table.insert().values(
                        project_id=proj_id,
                        team_id=team_id,
                        tier=int(max_tier),
                        devs_assigned=1,
                        max_devs=1,
                        estimated_hours=0,
                        start_date=start,
                        ready_to_start_date=start,
                        paused_on=None,
                        pending_hours=0,
                        status="Not Started"
                    )
                )

        st.success(f"Project '{pname}' created with ID {proj_id} y default assignments.")



    # --------------------------------------------
    # 2) Reorder Projects
    # --------------------------------------------
    st.subheader("Reorder Projects")
    df_proj = pd.read_sql(
        sa.select(
            projects_table.c.id,
            projects_table.c.name,
            projects_table.c.priority
        ).order_by(projects_table.c.priority),
        engine
    )
    if df_proj.empty:
        st.info("No projects to display.")
        return

    items = [{"id": r.id, "name": f"({r.priority}) {r.name}"} for r in df_proj.itertuples()]
    new_order = DraggableList(items, text_key="name", key="proj_sort")
    if st.button("Save Order"):
        for idx, itm in enumerate(new_order, start=1):
            run(
                projects_table.update()
                              .where(projects_table.c.id == itm["id"])
                              .values(priority=idx)
            )
        st.success("Project priorities updated.")

    # --------------------------------------------
    # 3) Edit Team Assignments
    # --------------------------------------------
    st.subheader("Edit Team Assignments")
    selected_name = st.selectbox(
        "Select Project to Edit",
        df_proj["name"].tolist(),
        key="sel_proj_edit"
    )
    proj_id = int(df_proj[df_proj["name"] == selected_name]["id"].iloc[0])

    # Leer asignaciones existentes
    assign_q = (
        sa.select(
            project_team_assignments_table.c.id,
            project_team_assignments_table.c.team_id,
            teams_table.c.name.label("team_name"),
            project_team_assignments_table.c.tier,
            project_team_assignments_table.c.devs_assigned,
            project_team_assignments_table.c.max_devs,
            project_team_assignments_table.c.estimated_hours,
            project_team_assignments_table.c.ready_to_start_date,
            project_team_assignments_table.c.start_date.label("assignment_start")
        )
        .select_from(
            project_team_assignments_table.join(
                teams_table,
                project_team_assignments_table.c.team_id == teams_table.c.id
            )
        )
        .where(project_team_assignments_table.c.project_id == proj_id)
    )
    df_assign = pd.read_sql(assign_q, engine)

    if df_assign.empty:
        st.info("No assignments for this project.")
        return

    # Para cada asignación, un expander con campos editables
    for row in df_assign.itertuples():
        with st.expander(row.team_name):
            # Tier: opciones filtradas por team_id
            tiers_df = pd.read_sql(
                sa.select(
                    tier_capacity_table.c.tier
                )
                .where(tier_capacity_table.c.team_id == row.team_id)
                .order_by(tier_capacity_table.c.tier),
                engine
            )
            tier_opts = tiers_df["tier"].tolist()
            new_tier = st.selectbox(
                "Tier",
                tier_opts,
                index=tier_opts.index(row.tier) if row.tier in tier_opts else 0,
                key=f"tier_{row.id}"
            )

            # Devs assigned / max devs
            new_assigned = st.number_input(
                "Devs Assigned",
                min_value=0.25,
                max_value=100.0,
                step=0.25,
                value=float(row.devs_assigned),
                key=f"assigned_{row.id}"
            )
            new_max = st.number_input(
                "Max Devs",
                min_value=0.25,
                max_value=100.0,
                step=0.25,
                value=float(row.max_devs),
                key=f"max_{row.id}"
            )

            # Estimated hours
            new_hours = st.number_input(
                "Estimated Hours",
                min_value=0,
                value=int(row.estimated_hours),
                key=f"hours_{row.id}"
            )

            # Ready to start date
            new_ready = st.date_input(
                "Ready to Start Date",
                value=row.ready_to_start_date or row.assignment_start,
                key=f"ready_{row.id}"
            )

            # Guardar cambios
            if st.button("Update Assignment", key=f"save_{row.id}"):
                run(
                    project_team_assignments_table.update()
                    .where(project_team_assignments_table.c.id == row.id)
                    .values(
                        tier=int(new_tier),
                        devs_assigned=new_assigned,
                        max_devs=new_max,
                        estimated_hours=new_hours,
                        ready_to_start_date=new_ready
                    )
                )
                st.success(f"Assignment for {row.team_name} updated.")
                #st.experimental_rerun()
