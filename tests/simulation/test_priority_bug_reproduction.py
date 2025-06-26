"""
Test para reproducir el bug de orden de prioridades que se ve en la UI
"""
import pytest
from datetime import date
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestPriorityBugReproduction:
    
    def test_priority_order_bug_reproduction(self):
        """
        REPRODUCIR BUG: Los proyectos no respetan el orden de prioridades
        
        Según la imagen del usuario:
        - Proyecto B (prioridad 1)
        - Proyecto a (prioridad 2) 
        - Proyecto project2 (prioridad 3)
        
        Pero en el Gantt se ven ejecutándose en paralelo en lugar de secuencialmente
        """
        
        # Setup equipos con capacidad SUFICIENTE - aquí está el bug
        # Con capacidad suficiente, los proyectos se ejecutan en paralelo ignorando prioridades
        teams = {
            1: Team(id=1, name="Arch", total_devs=5, tier_capacities={1: 16}),  # 5 devs - suficiente para todos
            2: Team(id=2, name="Model", total_devs=5, tier_capacities={2: 80}),  # 5 devs - suficiente para todos
            3: Team(id=3, name="Devs", total_devs=5, tier_capacities={3: 80}),  # 5 devs - suficiente para todos
            4: Team(id=4, name="Dqa", total_devs=5, tier_capacities={2: 24})   # 5 devs - suficiente para todos
        }
        
        # Proyectos con prioridades diferentes (como en la imagen)
        projects = {
            1: Project(id=1, name="B", priority=1,  # Prioridad más alta
                      start_date=date(2025, 6, 26),
                      due_date_wo_qa=date(2025, 9, 1),
                      due_date_with_qa=date(2025, 9, 15)),
            2: Project(id=2, name="a", priority=2,  # Prioridad media
                      start_date=date(2025, 6, 26),
                      due_date_wo_qa=date(2025, 9, 1),
                      due_date_with_qa=date(2025, 9, 15)),
            3: Project(id=3, name="project2", priority=3,  # Prioridad más baja
                      start_date=date(2025, 6, 26),
                      due_date_wo_qa=date(2025, 9, 1),
                      due_date_with_qa=date(2025, 9, 15))
        }
        
        # Asignaciones para todos los proyectos (misma configuración)
        assignments = []
        assignment_id = 1
        
        for project_id, project in projects.items():
            # Arch
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project.name, 
                project_priority=project.priority, team_id=1, team_name="Arch", 
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=16,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
            
            # Devs
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project.name,
                project_priority=project.priority, team_id=3, team_name="Devs",
                tier=3, devs_assigned=1.0, max_devs=1.0, estimated_hours=80,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
            
            # Model
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project.name,
                project_priority=project.priority, team_id=2, team_name="Model",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=80,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
            
            # Dqa
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project.name,
                project_priority=project.priority, team_id=4, team_name="Dqa",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=24,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Obtener asignaciones por proyecto y equipo
        project_b_arch = next(a for a in result.assignments if a.project_name == "B" and a.team_name == "Arch")
        project_a_arch = next(a for a in result.assignments if a.project_name == "a" and a.team_name == "Arch")
        project2_arch = next(a for a in result.assignments if a.project_name == "project2" and a.team_name == "Arch")
        
        print(f"\n🔍 RESULTADOS DEL SCHEDULER:")
        print(f"Proyecto B (prioridad 1) - Arch: {project_b_arch.calculated_start_date} a {project_b_arch.calculated_end_date}")
        print(f"Proyecto a (prioridad 2) - Arch: {project_a_arch.calculated_start_date} a {project_a_arch.calculated_end_date}")
        print(f"Proyecto project2 (prioridad 3) - Arch: {project2_arch.calculated_start_date} a {project2_arch.calculated_end_date}")
        
        # VERIFICAR QUE SE RESPETE EL ORDEN DE PRIORIDADES
        # BUG: Con capacidad suficiente, los proyectos se ejecutan en paralelo ignorando prioridades
        
        # Proyecto B (prioridad 1) debe empezar primero
        assert project_b_arch.calculated_start_date == date(2025, 6, 26), "Proyecto B debe empezar el 26/06"
        
        # BUG REPRODUCIDO: Proyecto a (prioridad 2) debe empezar DESPUÉS que termine B
        # Pero con capacidad suficiente, empieza al mismo tiempo
        try:
            assert project_a_arch.calculated_start_date > project_b_arch.calculated_end_date, \
                f"Proyecto a debe empezar después que termine B. B termina: {project_b_arch.calculated_end_date}, a empieza: {project_a_arch.calculated_start_date}"
            
            # Si llegamos aquí, el bug no se reprodujo
            print("❌ BUG NO REPRODUCIDO - Las prioridades se respetan incorrectamente")
            
        except AssertionError as e:
            print(f"✅ BUG REPRODUCIDO - {str(e)}")
            print("🐛 PROBLEMA: El scheduler permite ejecución en paralelo cuando hay capacidad suficiente")
            print("🎯 SOLUCIÓN NECESARIA: Forzar secuencialidad por prioridades independientemente de la capacidad")
            
            # Hacer que el test falle para mostrar el problema
            raise AssertionError(f"BUG CONFIRMADO: {str(e)}")
        
        # Este assert también debería fallar por el mismo motivo
        assert project2_arch.calculated_start_date > project_a_arch.calculated_end_date, \
            f"Proyecto project2 debe empezar después que termine a. a termina: {project_a_arch.calculated_end_date}, project2 empieza: {project2_arch.calculated_start_date}"
        
        print(f"✅ Test pasó - Las prioridades se respetan correctamente")