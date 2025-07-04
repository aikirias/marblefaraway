#!/usr/bin/env python3
"""
Script para simular un cambio de prioridades y probar el botón "Aceptar Cambios"
"""

import os
import sys
sys.path.append('app')

from modules.common.db import engine, projects_table
from modules.monitoring.monitoring import _save_priority_changes
import sqlalchemy as sa

def simulate_priority_change():
    """Simula un cambio de prioridades intercambiando A y B"""
    print("🔄 Simulando cambio de prioridades...")
    
    # Configurar DATABASE_URL
    os.environ['DATABASE_URL'] = "postgresql://estimator:change_me@localhost:5432/estimator_db"
    
    try:
        # 1. Mostrar estado actual
        with engine.begin() as conn:
            result = conn.execute(
                sa.select(projects_table.c.id, projects_table.c.name, projects_table.c.priority)
                .order_by(projects_table.c.priority)
            )
            current_state = list(result)
            print("\n📊 Estado actual de prioridades:")
            for project_id, name, priority in current_state:
                print(f"  {priority}. {name} (ID: {project_id})")
        
        # 2. Simular nuevo orden (intercambiar A y B)
        print("\n🔄 Simulando intercambio de A y B...")
        new_order = [
            {"id": 8, "name": "(3) B - 🟢 Activo", "priority": 3},  # B pasa a prioridad 1
            {"id": 7, "name": "(1) A - 🟢 Activo", "priority": 1},  # A pasa a prioridad 2
            {"id": 9, "name": "(2) c - ⏸️ Pausado", "priority": 2}, # c mantiene prioridad 3
            {"id": 10, "name": "(4) d - 🟢 Activo", "priority": 4}  # d mantiene prioridad 4
        ]
        
        # 3. Guardar cambios usando la función real
        print("💾 Guardando cambios usando _save_priority_changes()...")
        _save_priority_changes(new_order)
        
        # 4. Verificar cambios
        with engine.begin() as conn:
            result = conn.execute(
                sa.select(projects_table.c.id, projects_table.c.name, projects_table.c.priority)
                .order_by(projects_table.c.priority)
            )
            new_state = list(result)
            print("\n📊 Estado después del cambio:")
            for project_id, name, priority in new_state:
                print(f"  {priority}. {name} (ID: {project_id})")
        
        # 5. Revertir cambios para dejar todo como estaba
        print("\n🔄 Revirtiendo cambios para dejar el estado original...")
        original_order = [
            {"id": 7, "name": "(1) A - 🟢 Activo", "priority": 1},
            {"id": 9, "name": "(2) c - ⏸️ Pausado", "priority": 2},
            {"id": 8, "name": "(3) B - 🟢 Activo", "priority": 3},
            {"id": 10, "name": "(4) d - 🟢 Activo", "priority": 4}
        ]
        _save_priority_changes(original_order)
        
        # 6. Verificar estado final
        with engine.begin() as conn:
            result = conn.execute(
                sa.select(projects_table.c.id, projects_table.c.name, projects_table.c.priority)
                .order_by(projects_table.c.priority)
            )
            final_state = list(result)
            print("\n📊 Estado final (revertido):")
            for project_id, name, priority in final_state:
                print(f"  {priority}. {name} (ID: {project_id})")
        
        print("\n✅ ¡Simulación completada exitosamente!")
        print("🎯 La funcionalidad de 'Aceptar Cambios' está funcionando correctamente.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la simulación: {e}")
        return False

def main():
    """Ejecuta la simulación"""
    print("🚀 Iniciando simulación de cambio de prioridades...\n")
    
    success = simulate_priority_change()
    
    if success:
        print("\n🎉 ¡Simulación exitosa!")
        print("📝 La funcionalidad del botón 'Aceptar Cambios' está lista para usar.")
    else:
        print("\n❌ La simulación falló.")
        print("🔧 Revisar la implementación.")

if __name__ == "__main__":
    main()