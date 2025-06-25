"""
Script de prueba para verificar que el simulador funciona con los modelos actualizados
"""

from datetime import date, timedelta
from .models import Team, Project, Assignment, SimulationInput
from .scheduler import ProjectScheduler


def test_updated_simulation():
    """Prueba el simulador con los modelos actualizados"""
    
    print("🔬 Probando simulador con modelos actualizados de APE")
    print("=" * 60)
    
    # Fecha de inicio
    start_date = date(2025, 6, 16)
    
    # Teams con tier capacities (basado en datos reales)
    teams = {
        1: Team(
            id=1, 
            name="Arch", 
            total_devs=2, 
            busy_devs=0,
            tier_capacities={1: 16, 2: 32, 3: 72, 4: 240}
        ),
        2: Team(
            id=2, 
            name="Model", 
            total_devs=4, 
            busy_devs=0,
            tier_capacities={1: 40, 2: 80, 3: 120, 4: 160}
        ),
        3: Team(
            id=3, 
            name="Devs", 
            total_devs=6, 
            busy_devs=1,
            tier_capacities={1: 16, 2: 40, 3: 80, 4: 120}
        ),
        4: Team(
            id=4, 
            name="Dqa", 
            total_devs=3, 
            busy_devs=0,
            tier_capacities={1: 8, 2: 24, 3: 40}
        )
    }
    
    # Projects
    projects = {
        1: Project(
            id=1,
            name="Alpha",
            priority=1,
            start_date=start_date,
            due_date_wo_qa=start_date + timedelta(days=30),
            due_date_with_qa=start_date + timedelta(days=35)
        ),
        2: Project(
            id=2,
            name="Beta",
            priority=2,
            start_date=start_date,
            due_date_wo_qa=start_date + timedelta(days=25),
            due_date_with_qa=start_date + timedelta(days=30)
        )
    }
    
    # Assignments con diferentes tiers
    assignments = [
        # Alpha - Tier 2
        Assignment(
            id=1, project_id=1, project_name="Alpha", project_priority=1,
            team_id=1, team_name="Arch", tier=2, devs_assigned=1.0, max_devs=1.0,
            estimated_hours=0, ready_to_start_date=start_date, assignment_start_date=start_date
        ),
        Assignment(
            id=2, project_id=1, project_name="Alpha", project_priority=1,
            team_id=2, team_name="Model", tier=2, devs_assigned=1.0, max_devs=1.0,
            estimated_hours=0, ready_to_start_date=start_date, assignment_start_date=start_date
        ),
        Assignment(
            id=3, project_id=1, project_name="Alpha", project_priority=1,
            team_id=3, team_name="Devs", tier=2, devs_assigned=1.0, max_devs=1.0,
            estimated_hours=0, ready_to_start_date=start_date, assignment_start_date=start_date
        ),
        Assignment(
            id=4, project_id=1, project_name="Alpha", project_priority=1,
            team_id=4, team_name="Dqa", tier=2, devs_assigned=1.0, max_devs=1.0,
            estimated_hours=0, ready_to_start_date=start_date, assignment_start_date=start_date
        ),
        
        # Beta - Tier 1 (más rápido)
        Assignment(
            id=5, project_id=2, project_name="Beta", project_priority=2,
            team_id=1, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0,
            estimated_hours=0, ready_to_start_date=start_date, assignment_start_date=start_date
        ),
        Assignment(
            id=6, project_id=2, project_name="Beta", project_priority=2,
            team_id=2, team_name="Model", tier=1, devs_assigned=1.0, max_devs=1.0,
            estimated_hours=0, ready_to_start_date=start_date, assignment_start_date=start_date
        ),
    ]
    
    # Crear input de simulación
    simulation_input = SimulationInput(
        teams=teams,
        projects=projects,
        assignments=assignments,
        simulation_start_date=start_date
    )
    
    print("📋 DATOS DE ENTRADA:")
    print("\nEquipos:")
    for team in teams.values():
        print(f"  {team.name}: {team.get_available_devs()}/{team.total_devs} devs disponibles")
        for tier, hours in team.tier_capacities.items():
            print(f"    Tier {tier}: {hours} horas/persona")
    
    print("\nProyectos:")
    for proj in projects.values():
        print(f"  {proj.name}: Prioridad {proj.priority}, Due: {proj.due_date_wo_qa}")
    
    print("\nAsignaciones:")
    for assignment in assignments:
        print(f"  {assignment.project_name}-{assignment.team_name}: Tier {assignment.tier}")
    
    # Ejecutar simulación
    print("\n🚀 EJECUTANDO SIMULACIÓN...")
    scheduler = ProjectScheduler()
    
    try:
        result = scheduler.simulate(simulation_input)
        
        print("\n✅ RESULTADOS:")
        print("\nCronograma calculado:")
        for assignment in result.assignments:
            if assignment.calculated_start_date and assignment.calculated_end_date:
                hours = assignment.pending_hours
                days = (assignment.calculated_end_date - assignment.calculated_start_date).days + 1
                print(f"  {assignment.project_name}-{assignment.team_name}:")
                print(f"    Tier {assignment.tier} -> {hours}h en {days} días")
                print(f"    {assignment.calculated_start_date} a {assignment.calculated_end_date}")
            else:
                print(f"  {assignment.project_name}-{assignment.team_name}: No programado")
        
        print("\nResumen de proyectos:")
        for summary in result.project_summaries:
            print(f"  {summary['project_name']}:")
            print(f"    Estado: {summary['state']}")
            print(f"    Horas totales: {summary['total_hours']}")
            if summary.get('calculated_end_date'):
                print(f"    Fin calculado: {summary['calculated_end_date']}")
                if summary['delay_days'] > 0:
                    print(f"    Retraso: {summary['delay_days']} días")
        
        print("\n🎉 Simulación completada exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en la simulación: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_updated_simulation()