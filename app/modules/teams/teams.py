import streamlit as st
from modules.common.models import Team
from modules.common.teams_crud import create_team, read_all_teams, read_team, update_team, delete_team

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
            new_team = Team(
                id=0,  # Se asignará en DB
                name=team_name,
                total_devs=int(total),
                busy_devs=0,
                tier_capacities={}
            )
            team_id = create_team(new_team)
            st.success(f"Team '{team_name}' created with ID {team_id} and {int(total)} devs.")

    # Edit/Delete existing teams
    teams = read_all_teams()
    if teams:
        team_names = [team.name for team in teams.values()]
        sel = st.selectbox("Select Team", team_names, key="sel_team")
        
        # Find selected team
        selected_team = None
        for team in teams.values():
            if team.name == sel:
                selected_team = team
                break
        
        if selected_team:
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("New Name", value=selected_team.name, key="upd_team_name")
            with col2:
                new_total = st.number_input(
                    "Total Devs", min_value=0, value=selected_team.total_devs, key="upd_team_total"
                )
            with col3:
                if st.button("Update Team"):
                    updated_team = Team(
                        id=selected_team.id,
                        name=new_name,
                        total_devs=int(new_total),
                        busy_devs=selected_team.busy_devs,
                        tier_capacities=selected_team.tier_capacities
                    )
                    update_team(updated_team)
                    st.success("Team updated.")
            if st.button("Delete Team"):
                delete_team(selected_team.id)
                st.success("Team deleted.")

    # --- Tier Capacity Configuration ---
    st.subheader("Tier Capacity per Team")
    # Refresh team list
    teams = read_all_teams()
    if teams:
        team_names = [team.name for team in teams.values()]
        sel_team = st.selectbox("Team for Tiers", team_names, key="tier_team_select")
        
        # Find selected team
        selected_team = None
        for team in teams.values():
            if team.name == sel_team:
                selected_team = team
                break
        
        if selected_team:
            # Show existing tiers
            if selected_team.tier_capacities:
                tier_data = []
                for tier, hours in sorted(selected_team.tier_capacities.items()):
                    tier_data.append({"Tier": tier, "Hours/Person": hours})
                st.table(tier_data)
            else:
                st.info("No tier capacities configured for this team.")

            # Add or update tier
            with st.expander("Add/Update Tier"):
                tw_tier = st.number_input("Tier Level", min_value=1, step=1, key="tier_level")
                tw_hours = st.number_input("Hours per Person", min_value=0, step=1, key="tier_hours")
                if st.button("Save Tier"):
                    # Update tier capacities
                    updated_tier_capacities = selected_team.tier_capacities.copy()
                    updated_tier_capacities[int(tw_tier)] = int(tw_hours)
                    
                    updated_team = Team(
                        id=selected_team.id,
                        name=selected_team.name,
                        total_devs=selected_team.total_devs,
                        busy_devs=selected_team.busy_devs,
                        tier_capacities=updated_tier_capacities
                    )
                    update_team(updated_team)
                    
                    if tw_tier in selected_team.tier_capacities:
                        st.success(f"Tier {tw_tier} updated to {tw_hours} hrs.")
                    else:
                        st.success(f"Tier {tw_tier} added with {tw_hours} hrs.")
    else:
        st.info("No teams available. Create a team first.")