"""
Configuraciones específicas de Plotly para las vistas del cronograma de Gantt
Maneja la configuración visual y de interactividad para cada tipo de vista
"""

import plotly.express as px
import pandas as pd
from datetime import date
from typing import Dict, Optional
from .gantt_views import PHASE_COLORS, PROJECT_COLORS




def _configure_detailed_gantt_layout(fig, gantt_df: pd.DataFrame) -> None:
    """
    Configura el layout del gráfico Gantt para vista detallada
    
    Args:
        fig: Figura de Plotly
        gantt_df: DataFrame con datos del Gantt
    """
    # Configuración básica
    fig.update_yaxes(
        autorange="reversed", 
        title="Projects and Phases",
        tickfont=dict(size=10)
    )
    
    fig.update_xaxes(
        title="Timeline", 
        showgrid=True,
        gridcolor="lightgray",
        gridwidth=1
    )
    
    # Layout general
    fig.update_layout(
        title={
            'text': "🔍 Detailed View - Timeline by Project-Phase",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#2E86AB'}
        },
        showlegend=True,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(size=10)
        ),
        margin=dict(l=250, r=50, t=100, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(500, len(gantt_df) * 35)
    )


def configure_consolidated_gantt(fig, gantt_df: pd.DataFrame, phase_colors: Dict[str, str]) -> None:
    """
    Configura el gráfico Gantt para vista consolidada
    
    Args:
        fig: Figura de Plotly
        gantt_df: DataFrame con datos del Gantt
        phase_colors: Mapa de colores por fase
    """
    # Configuración básica
    fig.update_yaxes(
        autorange="reversed", 
        title="Proyectos",
        tickfont=dict(size=12)
    )
    
    fig.update_xaxes(
        title="Timeline del Proyecto", 
        showgrid=True,
        gridcolor="lightgray",
        gridwidth=1
    )
    
    # Layout general
    fig.update_layout(
        title={
            'text': "📈 Consolidated View - Timeline by Project",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#2E86AB'}
        },
        showlegend=True,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(size=10),
            title="Project Phases"
        ),
        margin=dict(l=200, r=50, t=100, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(400, gantt_df['Project'].nunique() * 60)
    )
    
    # Hover personalizado para vista consolidada
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>" +
                     "Fase: %{fullData.name}<br>" +
                     "Inicio: %{x}<br>" +
                     "Fin: %{x2}<br>" +
                     "Duración: %{customdata[2]} días<br>" +
                     "Horas: %{customdata[3]}<br>" +
                     "Devs: %{customdata[4]}<br>" +
                     "Prioridad: %{customdata[1]}<br>" +
                     "<extra></extra>"
    )


def create_detailed_gantt(gantt_df: pd.DataFrame, project_colors: Dict[str, str]):
    """
    Crea el gráfico Gantt para vista detallada
    
    Args:
        gantt_df: DataFrame con datos formateados
        project_colors: Mapa de colores por proyecto
        
    Returns:
        Figura de Plotly configurada
    """
    if gantt_df.empty:
        return None
    
    fig = px.timeline(
        gantt_df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Project",
        hover_data=["Team", "Priority", "Tier", "Devs", "Hours"],
        color_discrete_map=project_colors
    )

    # Use custom hover text
    fig.update_traces(
        hovertemplate='%{customdata}<extra></extra>',
        customdata=gantt_df['HoverText']
    )

    # Apply layout configuration
    _configure_detailed_gantt_layout(fig, gantt_df)
    return fig


def create_consolidated_gantt(gantt_df: pd.DataFrame, phase_colors: Dict[str, str] = None):
    """
    Crea el gráfico Gantt para vista consolidada usando Scatter con timeline correcto
    
    Args:
        gantt_df: DataFrame con datos formateados
        phase_colors: Mapa de colores por fase
        
    Returns:
        Figura de Plotly configurada
    """
    if gantt_df.empty:
        return None
    
    if phase_colors is None:
        phase_colors = PHASE_COLORS
    
    import plotly.graph_objects as go
    import pandas as pd
    
    fig = go.Figure()

    max_traces_per_project = 10  # Limit phases per project to avoid rendering issues

    for idx, row in gantt_df.iterrows():
        project_name = row['Task']
        phases_info = row['PhasesInfo']

        # Limit phases if there are too many
        if len(phases_info) > max_traces_per_project:
            phases_info = phases_info[:max_traces_per_project]

        # Create a scatter trace for each phase
        for phase_info in phases_info:
            phase_name = phase_info['name']
            phase_color = phase_colors.get(phase_name, '#CCCCCC')
            
            # Convert dates to timestamps
            # For Scatter visualization: end_date represents the last day of work (inclusive)
            # We add 1 day so the rectangle visually covers the entire end_date day
            start_date = pd.Timestamp(phase_info['start'])
            end_date = pd.Timestamp(phase_info['end'])

            # Visual end: add 1 day so bar extends to end of last day
            # This ensures no gaps between consecutive phases
            end_date_visual = end_date + pd.Timedelta(days=1)

            # Display end date + 1 calendar day in hover (cosmetic change)
            from datetime import timedelta
            end_date_display = phase_info['end'] + timedelta(days=1)

            # Generate phase-specific hover text (showing end date + 1 calendar day)
            hover_text = (
                f"<b>{project_name.replace('📋 ', '')} - {phase_name}</b><br>"
                f"Start: {phase_info['start'].strftime('%d/%m/%Y')}<br>"
                f"End: {end_date_display.strftime('%d/%m/%Y')}<br>"
                f"Hours: {phase_info['hours']}h<br>"
                f"Devs: {phase_info['devs']}<br>"
                f"Tier: {phase_info['tier']}"
            )
            # Create rectangle using Scatter with fill
            # Define the 4 corners of the rectangle for this phase
            x_coords = [start_date, end_date_visual, end_date_visual, start_date, start_date]
            y_coords = [idx - 0.4, idx - 0.4, idx + 0.4, idx + 0.4, idx - 0.4]
            
            # Agregar traza de Scatter para esta fase
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                fill='toself',
                fillcolor=phase_color,
                line=dict(color=phase_color, width=1),
                mode='lines',
                name=phase_name,
                hovertemplate=hover_text + "<extra></extra>",
                showlegend=phase_name not in [trace.name for trace in fig.data if hasattr(trace, 'name')],
                legendgroup=phase_name,
                # Usar el centro del rectángulo para el hover
                hoverinfo='text',
                text=hover_text
            ))
    
    # Configurar el layout
    fig.update_layout(
        title={
            'text': "📈 Consolidated View - Timeline by Project",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#2E86AB'}
        },
        xaxis_title="Project Timeline",
        yaxis_title="Projects",
        showlegend=True,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(size=10),
            title="Project Phases"
        ),
        margin=dict(l=200, r=50, t=100, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(400, len(gantt_df) * 80)
    )
    
    # Configurar ejes
    fig.update_yaxes(
        autorange="reversed", 
        tickfont=dict(size=12),
        tickmode='array',
        tickvals=list(range(len(gantt_df))),
        ticktext=[row['Task'] for _, row in gantt_df.iterrows()],
        showgrid=False
    )
    
    fig.update_xaxes(
        showgrid=True, 
        gridcolor="lightgray", 
        gridwidth=1,
        type='date',
        tickformat='%Y-%m-%d'
    )
    
    return fig


def add_timeline_markers(fig, gantt_df: pd.DataFrame, show_today: bool = True, show_months: bool = False):
    """
    Agrega marcadores temporales al gráfico Gantt
    
    Args:
        fig: Figura de Plotly
        gantt_df: DataFrame con datos del Gantt
        show_today: Si mostrar línea de "hoy"
        show_months: Si mostrar líneas de inicio de mes
    """
    if gantt_df.empty:
        return
    
    from datetime import date
    import pandas as pd
    
    try:
        min_date = gantt_df['Start'].min()
        max_date = gantt_df['Finish'].max()
        
        # Línea vertical para "hoy" si está en el rango
        if show_today:
            today = date.today()
            if min_date.date() <= today <= max_date.date():
                fig.add_shape(
                    type="line",
                    x0=today, x1=today,
                    y0=0, y1=1,
                    yref="paper",
                    line=dict(
                        color="red",
                        width=2,
                        dash="dash"
                    ),
                    opacity=0.7
                )
                
                # Agregar anotación para "HOY"
                fig.add_annotation(
                    x=today,
                    y=1,
                    yref="paper",
                    text="HOY",
                    showarrow=False,
                    font=dict(color="red", size=10),
                    yshift=10
                )
        
        # Líneas verticales para inicio de mes
        if show_months:
            month_range = pd.date_range(start=min_date.replace(day=1), end=max_date, freq='MS')
            for month_start in month_range:
                fig.add_shape(
                    type="line",
                    x0=month_start, x1=month_start,
                    y0=0, y1=1,
                    yref="paper",
                    line=dict(
                        color="gray",
                        width=1,
                        dash="dot"
                    ),
                    opacity=0.4
                )
                
                # Agregar anotación para el mes
                fig.add_annotation(
                    x=month_start,
                    y=1,
                    yref="paper",
                    text=month_start.strftime("%b"),
                    showarrow=False,
                    font=dict(color="gray", size=8),
                    yshift=10
                )
    except Exception as e:
        # Si hay error con los marcadores, simplemente no los agregamos
        pass


def add_weekend_shading(fig, start_date, end_date):
    """
    Agrega sombreado para los fines de semana (sábado y domingo) en el gráfico.

    Args:
        fig: Figura de Plotly.
        start_date: Fecha de inicio del rango a sombrear.
        end_date: Fecha de fin del rango a sombrear.
    """
    from datetime import timedelta
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 5:  # Es sábado
            fig.add_shape(
                type="rect",
                xref="x",
                yref="paper",
                x0=current_date,
                y0=0,
                x1=current_date + timedelta(days=2),
                y1=1,
                fillcolor="rgba(200, 200, 200, 0.2)",
                line_width=0,
                layer="below"
            )
        current_date += timedelta(days=1)


def get_gantt_figure(gantt_df: pd.DataFrame, view_type: str, project_colors: Dict[str, str] = None, 
                     phase_colors: Dict[str, str] = None, add_markers: bool = True):
    """
    Función principal para crear figuras de Gantt según el tipo de vista
    
    Args:
        gantt_df: DataFrame con datos del Gantt
        view_type: "detailed" | "consolidated"
        project_colors: Colores por proyecto (para vista detallada)
        phase_colors: Colores por fase (para vista consolidada)
        add_markers: Si agregar marcadores temporales
        
    Returns:
        Figura de Plotly configurada
    """
    if gantt_df.empty:
        return None
    
    if view_type == "detailed":
        if project_colors is None:
            # Generar colores por defecto si no se proporcionan
            unique_projects = gantt_df['Project'].unique()
            project_colors = {
                project: PROJECT_COLORS[i % len(PROJECT_COLORS)] 
                for i, project in enumerate(unique_projects)
            }
        fig = create_detailed_gantt(gantt_df, project_colors)
        
    elif view_type == "consolidated":
        if phase_colors is None:
            phase_colors = PHASE_COLORS
        fig = create_consolidated_gantt(gantt_df, phase_colors)
        
    else:
        raise ValueError(f"Tipo de vista no válido: {view_type}")
    
    if fig:
        # Determinar el rango de fechas del gráfico para el sombreado
        min_date = pd.to_datetime(gantt_df['Start'].min()).date()
        max_date = pd.to_datetime(gantt_df['Finish'].max()).date()
        
        # Agregar sombreado de fines de semana
        add_weekend_shading(fig, min_date, max_date)
        
        # Agregar marcadores de tiempo si es necesario
        if add_markers:
            add_timeline_markers(fig, gantt_df, show_today=True, show_months=False)
    
    return fig