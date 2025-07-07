"""
Utilidades de interfaz de usuario para APE
Consolida funciones de UI comunes y drag & drop
"""
import streamlit as st
from typing import List, Dict, Any, Optional

# Configuración global de drag & drop
try:
    from streamlit_sortables import sort_items
    DRAGGABLE_AVAILABLE = True
except ImportError:
    DRAGGABLE_AVAILABLE = False


def setup_draggable_list(items: List[Dict], text_key: str, key: str) -> List[Dict]:
    """
    Configura lista draggable con fallback si no está disponible
    Args:
        items: Lista de elementos a mostrar
        text_key: Clave del texto a mostrar en cada elemento
        key: Clave única para el componente Streamlit
    Returns:
        Lista reordenada (siempre devuelve una lista)
    """
    if DRAGGABLE_AVAILABLE:
        try:
            # CSS para que los elementos de la lista no parezcan botones
            # Se aplica un fondo transparente, sin bordes y color de texto claro
            st.markdown("""
                <style>
                    div[data-stale="false"] > div[data-testid="stVerticalBlock"] .stButton > button {
                        background-color: transparent;
                        border: none;
                        color: #fafafa; /* Color de texto para tema oscuro de Streamlit */
                        text-align: left !important;
                        display: block;
                        width: 100%;
                    }
                    div[data-stale="false"] > div[data-testid="stVerticalBlock"] .stButton > button:hover {
                        background-color: rgba(255, 255, 255, 0.1); /* Feedback visual al pasar el mouse */
                        color: #fafafa;
                    }
                </style>
            """, unsafe_allow_html=True)

            # Preparar items para streamlit-sortables
            sortable_items = [item[text_key] for item in items]
            
            # Usar sort_items para crear la interfaz drag & drop
            sorted_items = sort_items(
                sortable_items,
                key=key,
                direction="vertical"
            )
            
            # Crear un mapeo de texto a item original
            text_to_item = {item[text_key]: item for item in items}
            # Reconstruir lista en el nuevo orden
            return [text_to_item[text] for text in sorted_items if text in text_to_item]
                
        except Exception as e:
            st.warning(f"Error con drag & drop: {e}. Usando controles numéricos.")
            # Fallback a controles numéricos - no mostrar lista estática
            return items
    else:
        # No mostrar mensaje, solo retornar items para que se usen controles numéricos
        return items


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