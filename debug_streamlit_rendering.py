#!/usr/bin/env python3
"""
Script para agregar logs de diagnóstico al renderizado de Streamlit
"""

import os
import sys

# Agregar el directorio app al path
sys.path.append('app')

def add_debug_logs_to_projects():
    """Agregar logs de diagnóstico al archivo projects.py"""
    
    projects_file = 'app/modules/projects/projects.py'
    
    # Leer el archivo actual
    with open(projects_file, 'r') as f:
        content = f.read()
    
    # Agregar logs de diagnóstico
    debug_content = content.replace(
        '    # Mostrar proyectos con controles simples\n    for project in filtered_projects:\n        render_simple_project_card(project)',
        '''    # Mostrar proyectos con controles simples
    st.write(f"🔍 DEBUG: Intentando renderizar {len(filtered_projects)} proyectos")
    for i, project in enumerate(filtered_projects):
        st.write(f"🔍 DEBUG: Renderizando proyecto {i+1}: {project.name}")
        try:
            render_simple_project_card(project)
            st.write(f"✅ DEBUG: Proyecto {project.name} renderizado exitosamente")
        except Exception as e:
            st.error(f"❌ DEBUG: Error renderizando {project.name}: {e}")
            import traceback
            st.code(traceback.format_exc())'''
    )
    
    debug_content = debug_content.replace(
        'def render_simple_project_card(project: Project):\n    """Renderiza una tarjeta simple de proyecto con control de activación"""',
        '''def render_simple_project_card(project: Project):
    """Renderiza una tarjeta simple de proyecto con control de activación"""
    st.write(f"🔍 DEBUG: Iniciando render_simple_project_card para {project.name}")'''
    )
    
    # Escribir el archivo modificado
    with open(projects_file, 'w') as f:
        f.write(debug_content)
    
    print("✅ Logs de diagnóstico agregados a projects.py")
    print("🔄 Reinicia la aplicación Streamlit para ver los logs")

if __name__ == "__main__":
    add_debug_logs_to_projects()