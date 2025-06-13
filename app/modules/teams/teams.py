import streamlit as st
import pandas as pd
import sqlalchemy as sa
from modules.common.db import engine, areas_table, people_table, run

# Render Teams tab UI
def render_teams():
    st.header("Team Configuration")

    # Areas Management
    st.subheader("Areas Management")
    with st.expander("Add New Area"):
        name = st.text_input("Area Name", key="new_area")
        if st.button("Create Area") and name:
            run(areas_table.insert().values(name=name))
            st.success(f"Area '{name}' created.")
            #st.experimental_rerun()

    df_a = pd.read_sql(areas_table.select(), engine)
    if not df_a.empty:
        sel = st.selectbox("Select Area", df_a['name'], key="sel_area")
        newname = st.text_input("New Name", value=sel, key="upd_area")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Update Area"):
                run(areas_table.update().where(areas_table.c.name==sel).values(name=newname))
                st.success("Area updated.")
                #st.experimental_rerun()
        with c2:
            if st.button("Delete Area"):
                run(areas_table.delete().where(areas_table.c.name==sel))
                st.success("Area deleted.")
                #st.experimental_rerun()

    # People Management
    st.subheader("People Management")
    with st.expander("Add New Person"):
        pname = st.text_input("Person Name", key="new_person")
        parea = st.selectbox("Area", df_a['name'], key="new_person_area")
        pavail = st.selectbox("Availability (FTE)", [0.25,0.5,0.75,1.0], key="new_person_avail")
        if st.button("Add Person") and pname:
            aid = int(df_a[df_a['name']==parea]['id'].iloc[0])
            run(people_table.insert().values(name=pname, area_id=aid, availability=pavail))
            st.success(f"Person '{pname}' added to '{parea}'.")
            #st.experimental_rerun()

    peo_q = sa.select(
        people_table.c.id, people_table.c.name,
        areas_table.c.name.label('area'), people_table.c.availability
    ).select_from(
        people_table.join(areas_table, people_table.c.area_id==areas_table.c.id)
    )
    df_p = pd.read_sql(peo_q, engine)
    if not df_p.empty:
        opts = [f"{r.name} ({r.area})" for r in df_p.itertuples()]
        selp = st.selectbox("Select Person", opts, key="sel_person")
        idx = opts.index(selp)
        pid = df_p.iloc[idx]['id']
        newp = st.text_input("New Name", value=df_p.iloc[idx]['name'], key="upd_person_name")
        narea = st.selectbox("New Area", df_a['name'], key="upd_person_area")
        navail = st.selectbox("New Availability", [0.25,0.5,0.75,1.0], index=[0.25,0.5,0.75,1.0].index(df_p.iloc[idx]['availability']), key="upd_person_avail")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Update Person"):
                aid = int(df_a[df_a['name']==narea]['id'].iloc[0])
                run(people_table.update().where(people_table.c.id==pid).values(name=newp, area_id=aid, availability=navail))
                st.success("Person updated.")
                #st.experimental_rerun()
        with c2:
            if st.button("Delete Person"):
                run(people_table.delete().where(people_table.c.id==pid))
                st.success("Person deleted.")
                #st.experimental_rerun()