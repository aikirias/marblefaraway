"""
Utilidades de interfaz de usuario para APE
Consolida funciones de UI comunes y drag & drop
"""
import streamlit as st
from typing import List, Dict, Any, Optional

# Configuración global de drag & drop
try:
    from st_draggable_list import DraggableList
    DRAGGABLE_AVAILABLE = True
except ImportError:
    DRAGGABLE_AVAILABLE = False


def setup_draggable_list(items: List[Dict], text_key: str, key: str) -> Optional[List[Dict]]:
    """
    Configura lista draggable con fallback si no está disponible
    Args:
        items: Lista de elementos a mostrar
        text_key: Clave del texto a mostrar en cada elemento
        key: Clave única para el componente Streamlit
    Returns:
        Lista reordenada o None si no hay cambios
    """
    if DRAGGABLE_AVAILABLE:
        try:
            return DraggableList(
                items,
                text_key=text_key,
                key=key
            )
        except Exception as e:
            st.warning(f"Error con drag & drop: {e}. Usando lista estática.")
            return None
    else:
        st.info("📝 Drag & drop no disponible. Mostrando lista estática.")
        return None


def render_project_state_display(project) -> str:
    """Renderiza estado del proyecto de forma consistente"""
    if hasattr(project, 'is_active') and callable(project.is_active):
        if project.is_active():
            return "🟢 Activo"
        else:
            return "⏸️ Pausado"
    else:
        return "❓ Estado desconocido"


def render_metrics_row(metrics: Dict[str, Any], columns: int = 4):
    """
    Renderiza fila de métricas de forma consistente
    Args:
        metrics: Diccionario con métricas {nombre: valor}
        columns: Número de columnas a usar
    """
    cols = st.columns(columns)
    
    for i, (name, value) in enumerate(metrics.items()):
        with cols[i % columns]:
            st.metric(name, value)


def format_hours_display(hours: float) -> str:
    """Formatea horas para mostrar de forma consistente"""
    if hours == 0:
        return "0h"
    elif hours < 1:
        return f"{hours:.1f}h"
    elif hours == int(hours):
        return f"{int(hours)}h"
    else:
        return f"{hours:.1f}h"


def render_progress_bar(current: float, total: float, label: str = "") -> None:
    """Renderiza barra de progreso consistente"""
    if total > 0:
        progress = min(current / total, 1.0)
        st.progress(progress, text=f"{label} {current:.1f}/{total:.1f}h ({progress:.1%})")
    else:
        st.progress(0, text=f"{label} Sin datos")


def show_info_expandable(title: str, content: str, expanded: bool = False):
    """Muestra información en un expandable consistente"""
    with st.expander(title, expanded=expanded):
        st.info(content)