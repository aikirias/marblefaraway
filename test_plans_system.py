#!/usr/bin/env python3
"""
Script de prueba para el sistema de planes persistentes
Verifica funcionalidad básica de guardado, recuperación y comparación
"""

import sys
import os
from datetime import date, datetime

# Agregar el directorio de la aplicación al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.modules.common.models import (
    Team, Project, Assignment, ScheduleResult, SimulationInput, Plan, PlanAssignment
)
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.plans_crud import (
    save_plan, get_active_plan, compare_plans, list_plans, set_active_plan
)

def create_test_data():
    """Crea datos de prueba para la simulación"""
    
    # Crear equipos
    teams = {
        1: Team(id=1, name="Arch", total_devs=2, busy_devs=0, tier_capacities={1: 40, 2: 80}),
        2: Team(id=2, name="Devs", total_devs=4, busy_devs=0, tier_capacities={1: 20, 2: 40}),
    }
    
    # Crear proyectos
    projects = {
        1: Project(
            id=1, name="Proyecto Test 1", priority=1,
            start_date=date.today(), 
            due_date_wo_qa=date(2025, 2, 15),
            due_date_with_qa=date(2025, 2, 28),
            active=True
        ),
        2: Project(
            id=2, name="Proyecto Test 2", priority=2,
            start_date=date.today(),
            due_date_wo_qa=date(2025, 3, 15),
            due_date_with_qa=date(2025, 3, 31),
            active=True
        )
    }
    
    # Crear asignaciones
    assignments = [
        Assignment(
            id=1, project_id=1, project_name="Proyecto Test 1", project_priority=1,
            team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=40, ready_to_start_date=date.today(),
            assignment_start_date=date.today()
        ),
        Assignment(
            id=2, project_id=1, project_name="Proyecto Test 1", project_priority=1,
            team_id=2, team_name="Devs", tier=2, devs_assigned=2.0, max_devs=4.0,
            estimated_hours=80, ready_to_start_date=date.today(),
            assignment_start_date=date.today()
        ),
        Assignment(
            id=3, project_id=2, project_name="Proyecto Test 2", project_priority=2,
            team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=2.0,
            estimated_hours=40, ready_to_start_date=date.today(),
            assignment_start_date=date.today()
        )
    ]
    
    return SimulationInput(
        teams=teams,
        projects=projects,
        assignments=assignments,
        simulation_start_date=date.today()
    )

def test_plan_creation():
    """Prueba creación de planes desde ScheduleResult"""
    print("=== Prueba: Creación de Plan ===")
    
    # Crear datos de prueba
    simulation_input = create_test_data()
    
    # Ejecutar simulación
    scheduler = ProjectScheduler()
    result = scheduler.simulate(simulation_input)
    
    print(f"Simulación completada: {len(result.assignments)} asignaciones")
    print(f"Checksum generado: {result.checksum[:16]}...")
    print(f"Tiene cambios: {result.has_changes}")
    
    # Crear plan desde resultado
    plan = Plan.from_schedule_result(result, "Plan de Prueba", "Plan creado para testing")
    print(f"Plan creado: {plan.name}")
    print(f"Checksum del plan: {plan.checksum[:16]}...")
    print(f"Total asignaciones: {plan.total_assignments}")
    print(f"Total proyectos: {plan.total_projects}")
    
    return result, plan

def test_plan_persistence():
    """Prueba guardado y recuperación de planes"""
    print("\n=== Prueba: Persistencia de Planes ===")
    
    try:
        # Crear y simular
        simulation_input = create_test_data()
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Guardar plan
        print("Guardando plan...")
        saved_plan = save_plan(result, "Plan Persistente Test", "Plan guardado en BD")
        print(f"Plan guardado con ID: {saved_plan.id}")
        print(f"Activo: {saved_plan.is_active}")
        
        # Recuperar plan activo
        print("Recuperando plan activo...")
        active_plan = get_active_plan()
        if active_plan:
            print(f"Plan activo encontrado: {active_plan.name} (ID: {active_plan.id})")
            print(f"Asignaciones cargadas: {len(active_plan.assignments)}")
        else:
            print("No se encontró plan activo")
        
        # Listar planes
        print("Listando todos los planes...")
        all_plans = list_plans(10)
        for plan in all_plans:
            status = "🟢 ACTIVO" if plan.is_active else "⚪ Inactivo"
            print(f"  - {plan.name} ({status}) - {plan.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        return saved_plan
        
    except Exception as e:
        print(f"Error en prueba de persistencia: {e}")
        return None

def test_plan_comparison():
    """Prueba comparación de planes"""
    print("\n=== Prueba: Comparación de Planes ===")
    
    try:
        # Crear primera simulación
        simulation_input = create_test_data()
        scheduler = ProjectScheduler()
        result1 = scheduler.simulate(simulation_input)
        
        # Guardar como plan activo
        plan1 = save_plan(result1, "Plan Original", "Primer plan para comparación")
        print(f"Plan original guardado: {plan1.checksum[:16]}...")
        
        # Crear segunda simulación (idéntica)
        result2 = scheduler.simulate(simulation_input)
        
        # Comparar
        comparison = compare_plans(result2)
        print(f"Comparación completada:")
        print(f"  - Tiene cambios: {comparison['has_changes']}")
        print(f"  - Checksum nuevo: {comparison['new_checksum'][:16]}...")
        print(f"  - Checksum activo: {comparison['active_checksum'][:16] if comparison['active_checksum'] else 'N/A'}...")
        print(f"  - Cambios detectados: {comparison['changes_detected']}")
        
        # Modificar datos y comparar nuevamente
        print("\nModificando datos para generar cambios...")
        simulation_input.assignments[0].estimated_hours = 60  # Cambiar horas estimadas
        result3 = scheduler.simulate(simulation_input)
        
        comparison2 = compare_plans(result3)
        print(f"Segunda comparación:")
        print(f"  - Tiene cambios: {comparison2['has_changes']}")
        print(f"  - Cambios detectados: {comparison2['changes_detected']}")
        
    except Exception as e:
        print(f"Error en prueba de comparación: {e}")

def main():
    """Función principal de pruebas"""
    print("🧪 INICIANDO PRUEBAS DEL SISTEMA DE PLANES")
    print("=" * 50)
    
    try:
        # Prueba 1: Creación de planes
        result, plan = test_plan_creation()
        
        # Prueba 2: Persistencia
        saved_plan = test_plan_persistence()
        
        # Prueba 3: Comparación
        test_plan_comparison()
        
        print("\n✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()