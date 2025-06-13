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
    prio = st.number_input("Priority (temporary)", min_value=1, step=1, key="proj_prio")
    start = st.date_input("Start Date", key="proj_start")
    due = st.date_input("Due Date", key="proj_due")
    if st.button("Create Project") and pname:
        run(
            projects_table.insert().values(
                name=pname,
                priority=prio,
                start_date=start,
                due_date=due
            )
        )
        st.success(f"Project '{pname}' created with priority {prio}.")
        #st.experimental_rerun()

    # Display and reorder Projects
    st.subheader("Reorder Projects")
    df = pd.read_sql(
        sa.select(projects_table).order_by(projects_table.c.priority),
        engine
    )
    if df.empty:
        st.info("No projects to display.")
        return

    # Prepare data for draggable list
    items = [
        {"id": row.id, "order": row.priority, "name": row.name}
        for row in df.itertuples()
    ]
    # Render draggable list
    new_order = DraggableList(items, key="sortable_projects")

    # Save new order
    if st.button("Save Order"):
        for idx, itm in enumerate(new_order, start=1):
            run(
                projects_table.update()
                .where(projects_table.c.id == itm['id'])
                .values(priority=idx)
            )
        st.success("Project priorities updated.")
        #st.experimental_rerun()