#!/usr/bin/env python3
"""
Script de prueba para verificar la generación automática de assignments
en el constructor de proyectos del simulador APE
"""

import sys
import os
from datetime import datetime, date

# Agregar el directorio app al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from modules.simulation.test_case_builder import TestCaseBuilder
from modules.simulation.models import Team

def test_automatic_assignment_generation():
    """Prueba la generación automática de assignments"""
    print("🧪 Probando generación automática de assignments...")
    
    # Crear builder
    builder = TestCaseBuilder()
    
    # Crear equipos de prueba
    teams = {
        1: Team(id=1, name="Arch", total_devs=2, busy_devs=0),
        2: Team(id=2, name="Model", total_devs=4, busy_devs=0),
        3: Team(id=3, name="Devs", total_devs=6, busy_devs=1),
        4: Team(id=4, name="Dqa", total_devs=3, busy_devs=0)
    }
    
    # Crear proyecto de prueba con tiers individuales por fase
    test_project = {
        "id": 1,
        "name": "TestProject",
        "priority": 1,
        "tier": "Mediano",
        "start_date": date.today(),
        "phases": ["Arch", "Model", "Devs", "Dqa"],
        "phase_tiers": {
            "Arch": 1,  # Arch siempre Tier 1
            "Model": 2, # Model Tier 2
            "Devs": 3,  # Dev siempre Tier 3
            "Dqa": 2    # DQA Tier 2
        }
    }
    
    # Generar assignments automáticamente
    assignments = builder.create_assignments_from_projects([test_project])
    
    print(f"\n✅ Generados {len(assignments)} assignments automáticamente:")
    print("-" * 60)
    
    for assignment in assignments:
        print(f"📋 {assignment.project_name} - {assignment.team_name}")
        print(f"   Team: {assignment.team_id} ({assignment.team_name})")
        print(f"   Tier: {assignment.tier}")
        print(f"   Devs: {assignment.devs_assigned}")
        print(f"   Horas: {assignment.estimated_hours}")
        print(f"   Prioridad: {assignment.project_priority}")
        print()</search>
</search_and_replace>
    
    # Verificar patrón APE
    print("🔍 Verificando patrón APE:")
    
    arch_assignment = next((a for a in assignments if a.phase == "Arch"), None)
    model_assignment = next((a for a in assignments if a.phase == "Model"), None)
    dev_assignment = next((a for a in assignments if a.phase == "Devs"), None)
    dqa_assignment = next((a for a in assignments if a.phase == "Dqa"), None)
    
    # Verificar Arch
    if arch_assignment:
        arch_tier = getattr(arch_assignment, 'tier', None)
        print(f"✅ Arch: Tier {arch_tier}, {arch_assignment.devs_assigned} devs - {'✓' if arch_tier == 1 and arch_assignment.devs_assigned == 2.0 else '✗'}")
    
    # Verificar Model
    if model_assignment:
        model_tier = getattr(model_assignment, 'tier', None)
        print(f"✅ Model: Tier {model_tier}, {model_assignment.devs_assigned} devs - {'✓' if model_tier == 2 and model_assignment.devs_assigned == 1.0 else '✗'}")
    
    # Verificar Dev
    if dev_assignment:
        dev_tier = getattr(dev_assignment, 'tier', None)
        print(f"✅ Dev: Tier {dev_tier}, {dev_assignment.devs_assigned} devs - {'✓' if dev_tier == 3 and dev_assignment.devs_assigned == 1.0 else '✗'}")
    
    # Verificar DQA
    if dqa_assignment:
        dqa_tier = getattr(dqa_assignment, 'tier', None)
        print(f"✅ DQA: Tier {dqa_tier}, {dqa_assignment.devs_assigned} devs - {'✓' if dqa_tier == 2 and dqa_assignment.devs_assigned == 1.0 else '✗'}")
    
    print("\n🎉 Prueba completada!")
    return assignments

def test_multiple_projects():
    """Prueba con múltiples proyectos"""
    print("\n🧪 Probando múltiples proyectos...")
    
    builder = TestCaseBuilder()
    
    # Crear múltiples proyectos
    projects = [
        {
            "id": 1,
            "name": "Alpha",
            "priority": 1,
            "tier": "Grande",
            "start_date": date.today(),
            "phases": ["Arch", "Model", "Devs", "Dqa"],
            "phase_tiers": {"Arch": 1, "Model": 4, "Devs": 3, "Dqa": 3}
        },
        {
            "id": 2,
            "name": "Beta",
            "priority": 2,
            "tier": "Pequeño",
            "start_date": date.today(),
            "phases": ["Arch", "Model", "Devs"],
            "phase_tiers": {"Arch": 1, "Model": 1, "Devs": 3}
        }
    ]
    
    assignments = builder.create_assignments_from_projects(projects)
    
    print(f"✅ Generados {len(assignments)} assignments para {len(projects)} proyectos:")
    
    for project_name in ["Alpha", "Beta"]:
        project_assignments = [a for a in assignments if a.project_name == project_name]
        print(f"\n📁 {project_name}: {len(project_assignments)} assignments")
        for assignment in project_assignments:
            tier = getattr(assignment, 'tier', 'N/A')
            print(f"   - {assignment.phase}: Tier {tier}, {assignment.devs_assigned} devs")
    
    return assignments

def test_scenarios():
    """Prueba los escenarios predefinidos"""
    print("\n🧪 Probando escenarios predefinidos...")
    
    builder = TestCaseBuilder()
    scenarios = builder.get_predefined_scenarios()
    
    for scenario_name, scenario_data in scenarios.items():
        print(f"\n📋 {scenario_name}:")
        print(f"   Descripción: {scenario_data['description']}")
        
        assignments = builder.create_assignments_from_projects(scenario_data['projects'])
        print(f"   Assignments generados: {len(assignments)}")
        
        # Contar por fase
        phase_counts = {}
        for assignment in assignments:
            phase = assignment.phase
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        print(f"   Distribución: {phase_counts}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de generación automática de assignments")
    print("=" * 60)
    
    try:
        # Prueba básica
        test_automatic_assignment_generation()
        
        # Prueba múltiples proyectos
        test_multiple_projects()
        
        # Prueba escenarios
        test_scenarios()
        
        print("\n🎉 ¡Todas las pruebas completadas exitosamente!")
        print("\n💡 Para probar la interfaz completa:")
        print("   1. Ejecuta: docker compose up --build")
        print("   2. Abre: http://localhost:8501")
        print("   3. Ve a la pestaña 'Simulation'")
        print("   4. Usa el 'Constructor Visual' para crear proyectos")
        print("   5. Los assignments se generarán automáticamente")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)