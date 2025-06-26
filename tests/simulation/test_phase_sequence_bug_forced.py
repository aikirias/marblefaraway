"""
Test para forzar la reproducción del bug de secuencia de fases
Simula el caso donde las dependencias entre fases no se respetan
"""
import pytest
from datetime import date
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestPhaseSequenceBugForced:
    
    def test_phase_sequence_bug_forced_reproduction(self):
        """
        FORZAR BUG: Crear un escenario donde las fases no respeten la secuencia
        
        Voy a crear asignaciones que, si no se manejan las dependencias correctamente,
        resultarían en el orden incorrecto que viste en la imagen.
        """
        
        # Setup equipos
        teams = {
            1: Team(id=1, name="Arch", total_devs=1, tier_capacities={1: 16}),    # Capacidad limitada
            2: Team(id=2, name="Model", total_devs=1, tier_capacities={2: 80}),   # Capacidad limitada
            3: Team(id=3, name="Devs", total_devs=1, tier_capacities={3: 80}),    # Capacidad limitada
            4: Team(id=4, name="Dqa", total_devs=1, tier_capacities={2: 24})      # Capacidad limitada
        }
        
        # Múltiples proyectos para crear competencia por recursos
        projects = {
            1: Project(id=1, name="ProjectA", priority=1,
                      start_date=date(2025, 6, 26),
                      due_date_wo_qa=date(2025, 11, 1),
                      due_date_with_qa=date(2025, 11, 15)),
            2: Project(id=2, name="ProjectB", priority=2,
                      start_date=date(2025, 6, 26),
                      due_date_wo_qa=date(2025, 11, 1),
                      due_date_with_qa=date(2025, 11, 15))
        }
        
        # Asignaciones que podrían causar el problema si no se manejan bien las dependencias
        assignments = []
        assignment_id = 1
        
        # Proyecto A - con fechas ready que podrían causar problemas
        for project_id in [1, 2]:
            project_name = f"Project{'A' if project_id == 1 else 'B'}"
            priority = project_id
            
            # Arch - ready tarde
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project_name,
                project_priority=priority, team_id=1, team_name="Arch",
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=320,  # Muchas horas
                ready_to_start_date=date(2025, 9, 4),  # Ready muy tarde
                assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
            
            # Devs - ready temprano
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project_name,
                project_priority=priority, team_id=3, team_name="Devs",
                tier=3, devs_assigned=1.0, max_devs=1.0, estimated_hours=160,
                ready_to_start_date=date(2025, 7, 17),  # Ready temprano
                assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
            
            # Model - ready medio
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project_name,
                project_priority=priority, team_id=2, team_name="Model",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=200,
                ready_to_start_date=date(2025, 8, 7),  # Ready medio
                assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
            
            # Dqa - ready tarde
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project_name,
                project_priority=priority, team_id=4, team_name="Dqa",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=48,
                ready_to_start_date=date(2025, 10, 16),  # Ready tarde
                assignment_start_date=date(2025, 6, 26)
            ))
            assignment_id += 1
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        print(f"\n🔍 RESULTADOS CON MÚLTIPLES PROYECTOS Y RECURSOS LIMITADOS:")
        
        # Analizar cada proyecto
        for project_id in [1, 2]:
            project_name = f"Project{'A' if project_id == 1 else 'B'}"
            print(f"\n📋 {project_name}:")
            
            # Obtener asignaciones por fase
            arch_assignment = next(a for a in result.assignments if a.project_id == project_id and a.team_name == "Arch")
            devs_assignment = next(a for a in result.assignments if a.project_id == project_id and a.team_name == "Devs")
            model_assignment = next(a for a in result.assignments if a.project_id == project_id and a.team_name == "Model")
            dqa_assignment = next(a for a in result.assignments if a.project_id == project_id and a.team_name == "Dqa")
            
            print(f"  Arch:  {arch_assignment.calculated_start_date} a {arch_assignment.calculated_end_date}")
            print(f"  Devs:  {devs_assignment.calculated_start_date} a {devs_assignment.calculated_end_date}")
            print(f"  Model: {model_assignment.calculated_start_date} a {model_assignment.calculated_end_date}")
            print(f"  Dqa:   {dqa_assignment.calculated_start_date} a {dqa_assignment.calculated_end_date}")
            
            # Verificar si hay problemas de secuencia
            issues = []
            
            if devs_assignment.calculated_start_date <= arch_assignment.calculated_end_date:
                issues.append(f"Devs empieza antes/durante Arch ({devs_assignment.calculated_start_date} <= {arch_assignment.calculated_end_date})")
            
            if model_assignment.calculated_start_date <= devs_assignment.calculated_end_date:
                issues.append(f"Model empieza antes/durante Devs ({model_assignment.calculated_start_date} <= {devs_assignment.calculated_end_date})")
            
            if dqa_assignment.calculated_start_date <= model_assignment.calculated_end_date:
                issues.append(f"Dqa empieza antes/durante Model ({dqa_assignment.calculated_start_date} <= {model_assignment.calculated_end_date})")
            
            if issues:
                print(f"  🐛 PROBLEMAS DE SECUENCIA:")
                for issue in issues:
                    print(f"    - {issue}")
                
                # Hacer que el test falle si hay problemas
                assert False, f"Problemas de secuencia en {project_name}: {'; '.join(issues)}"
            else:
                print(f"  ✅ Secuencia correcta: Arch → Devs → Model → Dqa")
        
        print(f"\n✅ Todos los proyectos respetan la secuencia de fases correcta")