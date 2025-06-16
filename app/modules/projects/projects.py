import streamlit as st
import pandas as pd
import sqlalchemy as sa
from modules.common.db import engine, projects_table, run
from st_draggable_list import DraggableList

# Render Projects tab UI
def render_projects():
    st.header("Project Management")

    # Create New Project
    st.subheader("Create New Project")
    pname = st.text_input("Project Name", key="proj_name")
    phase = st.selectbox(
        "Phase",
        ["Arch", "Model", "Development", "QA"],
        key="proj_phase"
    )
    start = st.date_input("Start Date", key="proj_start")
    due_wo_qa = st.date_input("Due Date (without QA)", key="proj_due_wo_qa")
    due_with_qa = st.date_input("Due Date (with QA)", key="proj_due_with_qa")

    if st.button("Create Project") and pname:
        # Determinar la próxima prioridad de forma segura
        df_prio = pd.read_sql(
            sa.select(projects_table.c.priority),
            engine
        )
        max_prio = df_prio['priority'].max()
        if pd.isna(max_prio):
            next_prio = 1
        else:
            next_prio = int(max_prio) + 99

        run(
            projects_table.insert().values(
                name=pname,
                priority=next_prio,
                phase=phase,
                start_date=start,
                due_date_wo_qa=due_wo_qa,
                due_date_with_qa=due_with_qa
            )
        )
        st.success(f"Project '{pname}' created with priority {next_prio}.")

    # Reorder Projects
    st.subheader("Reorder Projects")
    df = pd.read_sql(
        sa.select(
            projects_table.c.id,
            projects_table.c.name,
            projects_table.c.priority
        ).order_by(projects_table.c.priority),
        engine
    )
    if df.empty:
        st.info("No projects to display.")
        return

    # Construir lista draggable
    items = [
        {"id": r.id, "name": f"({r.priority}) {r.name}"}
        for r in df.itertuples()
    ]
    new_order = DraggableList(items, text_key="name", key="proj_sort")

    # Guardar nuevo orden
    if st.button("Save Order"):
        for idx, itm in enumerate(new_order, start=1):
            run(
                projects_table.update()
                              .where(projects_table.c.id == itm["id"])
                              .values(priority=idx)
            )
        st.success("Project priorities updated.")
