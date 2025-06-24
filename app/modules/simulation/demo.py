"""
Demo simple del módulo de simulación
Ejecutar: python -m modules.simulation.demo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import date
from modules.simulation import ProjectScheduler, Assignment, Team


def run_demo():
    """Demo del caso Alpha-Beta"""
    
    print("🔬 DEMO: Simulador de Scheduling APE")
    print("="*50)
    
    # Configurar equipos
    teams = {
        2: Team(id=2, name="Arch", total_devs=2, busy_devs=0),
        3: Team(id=3, name="Model", total_devs=4, busy_devs=0)
    }
    
    # Configurar asignaciones
    assignments = [
        Assignment(
            project_id=1, project_name="Alpha", phase="Arch", phase_order=0,
            team_id=2, priority=1, devs_assigned=1, hours_needed=16,
            ready_date=date(2025, 6, 16)
        ),
        Assignment(
            project_id=1, project_name="Alpha", phase="Model", phase_order=1,
            team_id=3, priority=1, devs_assigned=1, hours_needed=40,
            ready_date=date(2025, 6, 16)
        ),
        Assignment(
            project_id=2, project_name="Beta", phase="Arch", phase_order=0,
            team_id=2, priority=2, devs_assigned=1, hours_needed=16,
            ready_date=date(2025, 6, 16)
        )
    ]
    
    # Ejecutar simulación
    scheduler = ProjectScheduler()
    result = scheduler.simulate(assignments, teams, today=date(2025, 6, 16))
    
    # Mostrar resultados
    print("CRONOGRAMA DETALLADO:")
    print("-" * 30)
    for assignment in result.assignments:
        duration = (assignment.end_date - assignment.start_date).days + 1
        print(f"{assignment.project_name:6} | {assignment.phase:5} | "
              f"{assignment.start_date} → {assignment.end_date} | "
              f"{duration:2}d | {assignment.devs_assigned}dev")
    
    print("\nRESUMEN POR PROYECTO:")
    print("-" * 30)
    for summary in result.project_summaries:
        duration = (summary['end_date'] - summary['start_date']).days + 1
        print(f"{summary['project_name']:6} | {summary['state']:11} | "
              f"{summary['start_date']} → {summary['end_date']} | {duration:2}d")
    
    print("\nVALIDACIÓN:")
    print("-" * 30)
    
    # Verificar paralelismo
    alpha_arch = next(a for a in result.assignments if a.project_name == "Alpha" and a.phase == "Arch")
    beta_arch = next(a for a in result.assignments if a.project_name == "Beta" and a.phase == "Arch")
    
    if alpha_arch.start_date == beta_arch.start_date:
        print("✅ Alpha-Arch y Beta-Arch ejecutan en paralelo")
    else:
        print("❌ Alpha-Arch y Beta-Arch NO ejecutan en paralelo")
    
    # Verificar dependencia
    alpha_model = next(a for a in result.assignments if a.project_name == "Alpha" and a.phase == "Model")
    
    if alpha_model.start_date > alpha_arch.end_date:
        print("✅ Alpha-Model espera a que termine Alpha-Arch")
    else:
        print("❌ Alpha-Model NO respeta dependencia de Alpha-Arch")
    
    # Verificar duración
    expected_alpha_arch_days = 3  # 16h / 8h = 2 días de trabajo, termina al día siguiente
    actual_alpha_arch_days = (alpha_arch.end_date - alpha_arch.start_date).days + 1
    
    if actual_alpha_arch_days == expected_alpha_arch_days:
        print("✅ Duración de Alpha-Arch correcta (3 días)")
    else:
        print(f"❌ Duración de Alpha-Arch incorrecta: {actual_alpha_arch_days} días")
    
    print("\n🎉 Demo completado!")


if __name__ == "__main__":
    run_demo()