#!/usr/bin/env python3
"""
Script de debug para verificar el estado de los proyectos en la base de datos
"""

import os
import sys
sys.path.append('app')

from modules.common.projects_crud import read_all_projects
from modules.common.assignments_crud import read_all_assignments

def debug_projects():
    print("=== DEBUG: Estado de Proyectos ===")
    
    try:
        # Leer todos los proyectos
        projects = read_all_projects()
        print(f"\n📊 Total de proyectos encontrados: {len(projects)}")
        
        if not projects:
            print("❌ No se encontraron proyectos en la base de datos")
            return
        
        # Mostrar detalles de cada proyecto
        for project_id, project in projects.items():
            print(f"\n🎯 Proyecto ID: {project_id}")
            print(f"   Nombre: {project.name}")
            print(f"   Prioridad: {project.priority}")
            print(f"   Estado (phase): {project.phase}")
            print(f"   Estado display: {project.get_state_display()}")
            print(f"   Fecha inicio: {project.start_date}")
            print(f"   Fecha límite (sin QA): {project.due_date_wo_qa}")
            print(f"   Fecha límite (con QA): {project.due_date_with_qa}")
        
        # Verificar asignaciones
        assignments = read_all_assignments()
        print(f"\n👥 Total de asignaciones encontradas: {len(assignments)}")
        
        # Agrupar asignaciones por proyecto
        assignments_by_project = {}
        for assignment in assignments:
            project_id = assignment.project_id
            if project_id not in assignments_by_project:
                assignments_by_project[project_id] = []
            assignments_by_project[project_id].append(assignment)
        
        for project_id, project_assignments in assignments_by_project.items():
            if project_id in projects:
                project_name = projects[project_id].name
                print(f"\n   📋 Proyecto '{project_name}' tiene {len(project_assignments)} asignaciones:")
                for assignment in project_assignments:
                    print(f"      - {assignment.team_name}: {assignment.devs_assigned} devs, {assignment.estimated_hours} hrs")
    
    except Exception as e:
        print(f"❌ Error al leer proyectos: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_projects()