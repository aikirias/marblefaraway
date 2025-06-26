import streamlit as st
import pandas as pd
import sqlalchemy as sa
from modules.common.db import engine, teams_table, tier_capacity_table, run

# Render Teams tab UI
def render_teams():
    st.header("Teams Management")

    # --- Teams Configuration ---
    st.subheader("Configure Teams")
    # Add new team
    with st.expander("Add New Team"):
        team_name = st.text_input("Team Name", key="new_team_name")
        total = st.number_input("Total Devs", min_value=0, step=1, key="new_team_total")
        if st.button("Create Team") and team_name:
            run(teams_table.insert().values(name=team_name, total_devs=int(total), busy_devs=0))
            st.success(f"Team '{team_name}' created with {int(total)} devs.")
            #st.experimental_rerun()

    # Edit/Delete existing teams
    df_teams = pd.read_sql(teams_table.select().order_by(teams_table.c.name), engine)
    if not df_teams.empty:
        sel = st.selectbox("Select Team", df_teams['name'], key="sel_team")
        row = df_teams[df_teams['name'] == sel].iloc[0]
        team_id = int(row['id'])
        col1, col2, col3 = st.columns(3)
        with col1:
            new_name = st.text_input("New Name", value=row['name'], key="upd_team_name")
        with col2:
            new_total = st.number_input(
                "Total Devs", min_value=0, value=int(row['total_devs']), key="upd_team_total"
            )
        with col3:
            if st.button("Update Team"):
                run(
                    teams_table.update()
                               .where(teams_table.c.id == team_id)
                               .values(name=new_name, total_devs=int(new_total))
                )
                st.success("Team updated.")
                #st.experimental_rerun()
        if st.button("Delete Team"):
            run(teams_table.delete().where(teams_table.c.id == team_id))
            st.success("Team deleted.")
            #st.experimental_rerun()

    # --- Tier Capacity Configuration ---
    st.subheader("Tier Capacity per Team")
    # Refresh team list
    df_teams = pd.read_sql(teams_table.select().order_by(teams_table.c.name), engine)
    team_opts = df_teams['name'].tolist()
    sel_team = st.selectbox("Team for Tiers", team_opts, key="tier_team_select")
    team_id = int(df_teams[df_teams['name'] == sel_team]['id'].iloc[0])

    # Show existing tiers
    tier_q = sa.select(
        tier_capacity_table.c.id,
        tier_capacity_table.c.tier,
        tier_capacity_table.c.hours_per_person
    ).where(tier_capacity_table.c.team_id == team_id).order_by(tier_capacity_table.c.tier)
    df_tiers = pd.read_sql(tier_q, engine)
    st.table(
        df_tiers[['tier', 'hours_per_person']]
        .rename(columns={'tier':'Tier','hours_per_person':'Hours/Person'})
    )

    # Add or update tier
    with st.expander("Add/Update Tier"):
        tw_tier = st.number_input("Tier Level", min_value=1, step=1, key="tier_level")
        tw_hours = st.number_input("Hours per Person", min_value=0, step=1, key="tier_hours")
        if st.button("Save Tier"):
            exists = df_tiers['tier'].tolist()
            if tw_tier in exists:
                run(
                    tier_capacity_table.update()
                                       .where(tier_capacity_table.c.team_id == team_id)
                                       .where(tier_capacity_table.c.tier == int(tw_tier))
                                       .values(hours_per_person=int(tw_hours))
                )
                st.success(f"Tier {tw_tier} updated to {tw_hours} hrs.")
            else:
                run(
                    tier_capacity_table.insert().values(
                        team_id=team_id,
                        tier=int(tw_tier),
                        hours_per_person=int(tw_hours)
                    )
                )
                st.success(f"Tier {tw_tier} added with {tw_hours} hrs.")
            #st.experimental_rerun()