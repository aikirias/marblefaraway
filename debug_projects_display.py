#!/usr/bin/env python3
"""
Script de diagnóstico para verificar por qué los proyectos no se muestran en la UI
"""

import os
import sys
from datetime import date

# Agregar el directorio app al path
sys.path.append('app')

from modules.common.projects_crud import read_all_projects
from modules.common.models import Project

def debug_projects_display():
    """Diagnosticar problemas de visualización de proyectos"""
    
    print("🔍 DIAGNÓSTICO: Visualización de Proyectos")
    print("=" * 50)
    
    try:
        # 1. Verificar lectura de proyectos desde DB
        print("1. Leyendo proyectos desde la base de datos...")
        projects = read_all_projects()
        
        if not projects:
            print("❌ ERROR: No se encontraron proyectos en la base de datos")
            return
        
        print(f"✅ Se encontraron {len(projects)} proyectos")
        
        # 2. Verificar estructura de cada proyecto
        print("\n2. Verificando estructura de proyectos:")
        for project_id, project in projects.items():
            print(f"\n📋 Proyecto ID {project_id}:")
            print(f"   - Nombre: {project.name}")
            print(f"   - Prioridad: {project.priority}")
            print(f"   - Activo: {project.active}")
            print(f"   - is_active(): {project.is_active()}")
            print(f"   - get_state_display(): {project.get_state_display()}")
            print(f"   - Horas trabajadas: {project.horas_trabajadas}")
            print(f"   - Fecha inicio: {project.start_date}")
            print(f"   - Fecha fin: {project.due_date_wo_qa}")
            print(f"   - Fecha inicio real: {project.fecha_inicio_real}")
        
        # 3. Simular filtros del Dashboard
        print("\n3. Simulando filtros del Dashboard:")
        
        # Filtro "Todos"
        filtered_all = list(projects.values())
        print(f"   - Filtro 'Todos': {len(filtered_all)} proyectos")
        
        # Filtro "Solo Activos"
        filtered_active = [p for p in projects.values() if p.is_active()]
        print(f"   - Filtro 'Solo Activos': {len(filtered_active)} proyectos")
        for p in filtered_active:
            print(f"     * {p.name} (Activo: {p.active})")
        
        # Filtro "Solo Inactivos"
        filtered_inactive = [p for p in projects.values() if not p.is_active()]
        print(f"   - Filtro 'Solo Inactivos': {len(filtered_inactive)} proyectos")
        for p in filtered_inactive:
            print(f"     * {p.name} (Activo: {p.active})")
        
        # 4. Verificar ordenamiento por prioridad
        print("\n4. Verificando ordenamiento por prioridad:")
        sorted_projects = sorted(projects.values(), key=lambda p: p.priority)
        for p in sorted_projects:
            print(f"   - Prioridad {p.priority}: {p.name}")
        
        # 5. Verificar métricas del Dashboard
        print("\n5. Verificando métricas del Dashboard:")
        active_count = sum(1 for p in projects.values() if p.is_active())
        inactive_count = len(projects) - active_count
        total_hours_worked = sum(p.horas_trabajadas for p in projects.values())
        
        print(f"   - Proyectos Activos: {active_count}")
        print(f"   - Proyectos Inactivos: {inactive_count}")
        print(f"   - Horas Trabajadas Total: {total_hours_worked}")
        
        print("\n✅ DIAGNÓSTICO COMPLETADO")
        print("Los datos parecen estar correctos en la base de datos.")
        print("El problema podría estar en el renderizado de Streamlit.")
        
    except Exception as e:
        print(f"❌ ERROR durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_projects_display()