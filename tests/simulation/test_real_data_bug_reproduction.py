"""
Test para reproducir el bug usando los datos reales del usuario
"""
import pytest
from datetime import date
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestRealDataBugReproduction:
    
    def test_real_data_bug_with_zero_hours(self):
        """
        REPRODUCIR BUG con datos reales del usuario
        
        Datos clave identificados:
        - Team ID 2 = "Arch", Team ID 1 = "Devs", Team ID 4 = "Dqa", Team ID 3 = "Model"
        - Assignment con estimated_hours=0 (¡esto podría ser el problema!)
        - Proyectos "B" (priority=1) y "a" (priority=2)
        """
        
        # Setup equipos con IDs reales del usuario
        teams = {
            2: Team(id=2, name="Arch", total_devs=8, busy_devs=0, 
                   tier_capacities={1: 16, 2: 32, 3: 72, 4: 240}),
            1: Team(id=1, name="Devs", total_devs=1, busy_devs=0, 
                   tier_capacities={1: 16, 2: 40, 3: 80, 4: 120}),
            4: Team(id=4, name="Dqa", total_devs=1, busy_devs=0, 
                   tier_capacities={1: 8, 2: 24, 3: 40}),
            3: Team(id=3, name="Model", total_devs=1, busy_devs=0, 
                   tier_capacities={1: 16, 2: 40, 3: 80, 4: 120})
        }
        
        # Proyectos con IDs reales del usuario
        projects = {
            3: Project(id=3, name="B", priority=1,
                      start_date=date(2025, 6, 25),
                      due_date_wo_qa=date(2025, 6, 25),
                      due_date_with_qa=date(2025, 6, 25)),
            1: Project(id=1, name="a", priority=2,
                      start_date=date(2025, 6, 25),
                      due_date_wo_qa=date(2025, 6, 25),
                      due_date_with_qa=date(2025, 6, 25)),
            2: Project(id=2, name="project2", priority=3,
                      start_date=date(2025, 6, 25),
                      due_date_wo_qa=date(2025, 6, 25),
                      due_date_with_qa=date(2025, 6, 25))
        }
        
        # Asignaciones que incluyen el caso problemático: estimated_hours=0
        assignments = [
            # Proyecto B (priority=1, project_id=3) - CON HORAS CERO
            Assignment(
                id=9, project_id=3, project_name="B", project_priority=1,
                team_id=2, team_name="Arch", tier=4, devs_assigned=4.0, max_devs=4.0,
                estimated_hours=0,  # ¡PROBLEMA POTENCIAL!
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            Assignment(
                id=10, project_id=3, project_name="B", project_priority=1,
                team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=80,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            Assignment(
                id=11, project_id=3, project_name="B", project_priority=1,
                team_id=3, team_name="Model", tier=2, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=80,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            Assignment(
                id=12, project_id=3, project_name="B", project_priority=1,
                team_id=4, team_name="Dqa", tier=2, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=24,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            
            # Proyecto a (priority=2, project_id=1)
            Assignment(
                id=13, project_id=1, project_name="a", project_priority=2,
                team_id=2, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=16,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            Assignment(
                id=14, project_id=1, project_name="a", project_priority=2,
                team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=80,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            Assignment(
                id=15, project_id=1, project_name="a", project_priority=2,
                team_id=3, team_name="Model", tier=2, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=80,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            Assignment(
                id=16, project_id=1, project_name="a", project_priority=2,
                team_id=4, team_name="Dqa", tier=2, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=24,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            )
        ]
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación
        scheduler = ProjectScheduler()
        
        # Debug: Verificar las horas calculadas antes de la simulación
        print(f"\n🔍 DEBUG - HORAS CALCULADAS ANTES DE SIMULACIÓN:")
        for assignment in assignments:
            if assignment.project_name == "B":
                team = teams[assignment.team_id]
                hours_needed = assignment.get_hours_needed(team)
                print(f"  {assignment.team_name}: estimated_hours={assignment.estimated_hours}, hours_needed={hours_needed}")
        
        result = scheduler.simulate(simulation_input)
        
        print(f"\n🔍 RESULTADOS CON DATOS REALES (estimated_hours=0):")
        
        # Analizar proyecto B
        print(f"\n📋 Proyecto B (priority=1):")
        b_assignments = [a for a in result.assignments if a.project_name == "B"]
        for assignment in sorted(b_assignments, key=lambda x: x.team_name):
            print(f"  {assignment.team_name}: {assignment.calculated_start_date} a {assignment.calculated_end_date} (horas: {assignment.estimated_hours})")
        
        # Analizar proyecto a
        print(f"\n📋 Proyecto a (priority=2):")
        a_assignments = [a for a in result.assignments if a.project_name == "a"]
        for assignment in sorted(a_assignments, key=lambda x: x.team_name):
            print(f"  {assignment.team_name}: {assignment.calculated_start_date} a {assignment.calculated_end_date} (horas: {assignment.estimated_hours})")
        
        # Verificar si el problema está en las asignaciones con horas cero
        b_arch = next(a for a in result.assignments if a.project_name == "B" and a.team_name == "Arch")
        b_devs = next(a for a in result.assignments if a.project_name == "B" and a.team_name == "Devs")
        
        print(f"\n🔍 ANÁLISIS DEL PROBLEMA:")
        print(f"B-Arch (0 horas): {b_arch.calculated_start_date} a {b_arch.calculated_end_date}")
        print(f"B-Devs (80 horas): {b_devs.calculated_start_date} a {b_devs.calculated_end_date}")
        
        # VERIFICAR SI HAY PROBLEMA DE SECUENCIA
        # Con el fix aplicado, las asignaciones con 0 horas no afectan las dependencias
        # Devs puede empezar el mismo día que "termina" Arch (que es instantáneo)
        if b_devs.calculated_start_date < b_arch.calculated_start_date:
            print(f"🐛 BUG ENCONTRADO: Devs empieza ANTES que Arch")
            print(f"   Arch empieza: {b_arch.calculated_start_date}")
            print(f"   Devs empieza: {b_devs.calculated_start_date}")
            
            # Hacer que el test falle para mostrar el problema
            assert False, f"BUG: Devs no puede empezar antes que Arch. Arch empieza: {b_arch.calculated_start_date}, Devs empieza: {b_devs.calculated_start_date}"
        
        # Verificar que Arch con 0 horas usa tier capacity como default
        # Con estimated_hours=0, debería usar tier capacity (240 * 4 devs = 960 horas)
        expected_hours = 240 * 4  # tier 4 capacity * devs_assigned
        if b_arch.pending_hours != expected_hours:
            print(f"🐛 BUG: Arch con estimated_hours=0 debería usar tier capacity")
            assert False, f"Arch debería usar tier capacity. Expected: {expected_hours}, Got: {b_arch.pending_hours}"
        
        print(f"✅ Secuencia correcta mantenida a pesar de horas=0")