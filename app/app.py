import streamlit as st
from modules.teams.teams import render_teams
from modules.projects.projects import render_projects

st.set_page_config(
    page_title="APE",
    page_icon="/app/assets/favicon.png",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("Automatic Project Estimator (APE)")

# Tabs for Teams and Projects
tab1, tab2 = st.tabs(["Teams", "Projects"])
with tab1:
    st.title("Teams Management")
    render_teams()
with tab2:
    render_projects()