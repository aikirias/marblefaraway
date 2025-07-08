"""
Constantes del sistema APE
Consolida todas las constantes dispersas en el proyecto
"""
from datetime import date

# Límites de fechas seguros para evitar errores de rango
MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2100, 12, 31)

# Orden de fases APE
PHASE_ORDER = ["Arch", "Model", "Devs", "Dqa"]
PHASE_ORDER_MAP = {"Arch": 1, "Model": 2, "Devs": 3, "Dqa": 4}

# Colores para Gantt
PHASE_COLORS = {
    "Arch": "#FF6B6B",      # Rojo coral - Arquitectura
    "Model": "#45B7D1",     # Azul - Modelado
    "Dev": "#4ECDC4",       # Turquesa - Desarrollo  
    "Dqa": "#96CEB4"        # Verde - QA
}

PROJECT_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
    '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
]

# Configuraciones de UI
DEFAULT_GANTT_HEIGHT = 500
MAX_GANTT_TRACES = 100