import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from .scheduler import ProjectScheduler
from .models import Team, Project, Assignment, SimulationInput

def render_simulation():
    """Renderiza la interfaz de simulación de scheduling APE"""
    
    st.header("🔬 Simulador de Scheduling APE")
    st.markdown("Visualiza cómo funciona el algoritmo de scheduling **under the hood** usando la estructura real de APE.")
    
    # Solo mostrar el constructor visual (eliminar pestañas)
    render_visual_builder()


def render_visual_builder():
    """Renderiza el constructor visual de casos de prueba"""
    from .test_case_builder import render_test_case_builder
    render_test_case_builder()