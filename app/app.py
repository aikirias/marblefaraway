import streamlit as st
import logging
import os
from modules.teams.teams import render_teams
from modules.projects.projects import render_projects
from modules.monitoring.monitoring import render_monitoring
from modules.plans.plans import render_plans

from modules.active_projects.active_projects import render_active_projects


# Configurar logging para ver logs de debug
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

st.set_page_config(
    page_title="APE",
    page_icon="/app/assets/favicon.png",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("Automatic Project Estimator (APE)")

# Tabs for Teams and Projects
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Monitoring", "Proyectos Activos", "Planes Guardados", "Teams", "Projects"])

with tab1:
    render_monitoring()

with tab2:
    render_active_projects()

with tab3:
    render_plans()

with tab4:
    render_teams()

with tab5:
    render_projects()


