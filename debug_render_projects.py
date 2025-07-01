#!/usr/bin/env python3
"""
Script de debug para verificar el renderizado de proyectos
"""

import sys
import os
sys.path.append('app')

from modules.common.projects_crud import read_all_projects

def debug_render_logic():
    """Debug de la lógica de renderizado"""
    print("=== DEBUG RENDER LOGIC ===")
    
    try:
        projects = read_all_projects()
        print(f"Total proyectos cargados: {len(projects)}")
        
        if not projects:
            print("❌ No hay proyectos creados")
            return
        
        # Simular la lógica de _render_filtered_projects
        print("\n=== SIMULANDO _render_filtered_projects ===")
        
        # Filtros disponibles
        filters = ["Todos", "Solo Activos", "Solo Inactivos"]
        
        for filter_type in filters:
            print(f"\n--- Filtro: {filter_type} ---")
            
            # Simular _filter_projects
            filtered = list(projects.values())
            
            if filter_type == "Solo Activos":
                filtered = [p for p in filtered if p.is_active()]
            elif filter_type == "Solo Inactivos":
                filtered = [p for p in filtered if not p.is_active()]
            
            # Implementar prioridad efectiva
            def effective_priority(project):
                if project.is_active():
                    return (0, project.priority)  # Activos primero
                else:
                    return (1, project.priority)  # Pausados después
            
            sorted_projects = sorted(filtered, key=effective_priority)
            
            print(f"Proyectos filtrados: {len(sorted_projects)}")
            
            if not sorted_projects:
                print(f"❌ No hay proyectos para mostrar con el filtro '{filter_type}'")
                continue
            
            for project in sorted_projects:
                state = "Activo" if project.is_active() else "Pausado"
                print(f"  ✅ {project.name} - {state} (Prioridad: {project.priority})")
        
        # Verificar si hay algún problema con las fechas
        print("\n=== VERIFICAR FECHAS ===")
        for project_id, project in projects.items():
            print(f"Proyecto {project.name}:")
            print(f"  start_date: {project.start_date} (tipo: {type(project.start_date)})")
            print(f"  due_date_with_qa: {project.due_date_with_qa} (tipo: {type(project.due_date_with_qa)})")
            
            # Verificar si las fechas pueden causar problemas
            try:
                date_str = f"{project.start_date} → {project.due_date_with_qa}"
                print(f"  ✅ Formato de fecha OK: {date_str}")
            except Exception as e:
                print(f"  ❌ Error con fechas: {e}")
        
        # Verificar métodos del modelo Project
        print("\n=== VERIFICAR MÉTODOS PROJECT ===")
        sample_project = list(projects.values())[0]
        try:
            print(f"get_state_display(): {sample_project.get_state_display()}")
            print(f"is_active(): {sample_project.is_active()}")
            print(f"get_progreso_display(): {sample_project.get_progreso_display()}")
            print(f"get_horas_faltantes(): {sample_project.get_horas_faltantes()}")
            print("✅ Todos los métodos funcionan correctamente")
        except Exception as e:
            print(f"❌ Error en métodos del proyecto: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_render_logic()