import streamlit as st
from modules.teams.teams import render_teams
from modules.projects.projects import render_projects
from modules.monitoring.monitoring import render_monitoring
from modules.simulation.simulation import render_simulation

st.set_page_config(
    page_title="APE",
    page_icon="/app/assets/favicon.png",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("Automatic Project Estimator (APE)")

# Tabs for Teams and Projects
tab1, tab2, tab3, tab4 = st.tabs(["Simulation","Teams", "Projects", "Monitoring"])

with tab1:
    render_simulation()

with tab2:
    render_teams()

with tab3:
    render_projects()

with tab4:
    render_monitoring()

