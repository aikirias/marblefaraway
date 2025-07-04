#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de gestión de prioridades
"""

import os
import sys
sys.path.append('app')

from modules.common.db import engine, projects_table
from modules.monitoring.monitoring import _detect_priority_changes, _save_priority_changes
import sqlalchemy as sa

def test_priority_detection():
    """Prueba la detección de cambios en prioridades"""
    print("🧪 Probando detección de cambios en prioridades...")
    
    # Simular items originales
    original_items = [
        {"id": 7, "name": "(1) A - 🟢 Activo", "priority": 1},
        {"id": 8, "name": "(3) B - 🟢 Activo", "priority": 3},
        {"id": 10, "name": "(4) d - 🟢 Activo", "priority": 4},
        {"id": 9, "name": "(2) c - ⏸️ Pausado", "priority": 2}
    ]
    
    # Simular nuevo orden (B y A intercambiados)
    new_order = [
        {"id": 8, "name": "(3) B - 🟢 Activo", "priority": 3},
        {"id": 7, "name": "(1) A - 🟢 Activo", "priority": 1},
        {"id": 10, "name": "(4) d - 🟢 Activo", "priority": 4},
        {"id": 9, "name": "(2) c - ⏸️ Pausado", "priority": 2}
    ]
    
    # Probar detección de cambios
    has_changes = _detect_priority_changes(original_items, new_order)
    print(f"✅ Cambios detectados: {has_changes}")
    
    # Probar sin cambios
    no_changes = _detect_priority_changes(original_items, original_items)
    print(f"✅ Sin cambios detectados: {not no_changes}")
    
    return has_changes and not no_changes

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("🧪 Probando conexión a la base de datos...")
    
    try:
        with engine.begin() as conn:
            result = conn.execute(sa.text("SELECT COUNT(*) FROM projects"))
            count = result.scalar()
            print(f"✅ Conexión exitosa. Proyectos en DB: {count}")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_priority_save():
    """Prueba el guardado de prioridades (sin modificar realmente)"""
    print("🧪 Probando guardado de prioridades...")
    
    try:
        # Obtener estado actual
        with engine.begin() as conn:
            result = conn.execute(
                sa.select(projects_table.c.id, projects_table.c.priority)
                .order_by(projects_table.c.priority)
            )
            current_priorities = list(result)
            print(f"✅ Prioridades actuales: {current_priorities}")
            
        return True
    except Exception as e:
        print(f"❌ Error al leer prioridades: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas de gestión de prioridades...\n")
    
    # Configurar DATABASE_URL si no está configurado
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = "postgresql://estimator:change_me@localhost:5432/estimator_db"
        print("📝 DATABASE_URL configurado")
    
    tests = [
        ("Detección de cambios", test_priority_detection),
        ("Conexión a DB", test_database_connection),
        ("Lectura de prioridades", test_priority_save)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR en {test_name}: {e}")
            results.append((test_name, False))
    
    print(f"\n{'='*50}")
    print("📊 RESUMEN DE PRUEBAS:")
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La funcionalidad está lista.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisar implementación.")

if __name__ == "__main__":
    main()