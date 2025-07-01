#!/usr/bin/env python3
"""
Script de debug para verificar el problema con los proyectos en Monitoring
"""

import sys
import os
sys.path.append('app')

from modules.common.projects_crud import read_all_projects

def debug_projects():
    """Debug de proyectos cargados"""
    print("=== DEBUG PROYECTOS MONITORING ===")
    
    try:
        projects = read_all_projects()
        print(f"Total proyectos cargados: {len(projects)}")
        
        if not projects:
            print("❌ No se encontraron proyectos")
            return
        
        print("\n=== DETALLE DE PROYECTOS ===")
        for project_id, project in projects.items():
            print(f"ID: {project_id}")
            print(f"  Nombre: {project.name}")
            print(f"  Prioridad: {project.priority}")
            print(f"  Activo: {project.active}")
            print(f"  Estado: {'Activo' if project.is_active() else 'Pausado'}")
            print(f"  Horas trabajadas: {project.horas_trabajadas}")
            print(f"  Horas totales: {project.horas_totales_estimadas}")
            print("---")
        
        # Verificar filtrado
        print("\n=== VERIFICAR FILTRADO ===")
        active_projects = [p for p in projects.values() if p.is_active()]
        inactive_projects = [p for p in projects.values() if not p.is_active()]
        
        print(f"Proyectos activos: {len(active_projects)}")
        for p in active_projects:
            print(f"  - {p.name} (Prioridad: {p.priority})")
        
        print(f"Proyectos pausados: {len(inactive_projects)}")
        for p in inactive_projects:
            print(f"  - {p.name} (Prioridad: {p.priority})")
        
        # Verificar prioridad efectiva
        print("\n=== PRIORIDAD EFECTIVA ===")
        all_projects = list(projects.values())
        def effective_priority(project):
            if project.is_active():
                return (0, project.priority)  # Activos primero
            else:
                return (1, project.priority)  # Pausados después
        
        sorted_projects = sorted(all_projects, key=effective_priority)
        for p in sorted_projects:
            state = "Activo" if p.is_active() else "Pausado"
            print(f"  {p.name} - {state} (Prioridad: {p.priority})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_projects()