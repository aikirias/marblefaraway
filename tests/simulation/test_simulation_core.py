"""
Tests consolidados de simulación APE - Casos críticos y bugs reproducidos
Consolida: test_phase_sequence_bug.py, test_priority_bug_reproduction.py, 
test_phase_sequence_bug_forced.py, test_phase_sequence_bug_realistic.py
"""

import pytest
from datetime import date
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestSimulationCore:
    """Tests consolidados para casos críticos del algoritmo de scheduling"""
    
    def test_phase_sequence_within_project(self):
        """
        CASO CRÍTICO: Las fases dentro de un proyecto deben seguir el orden secuencial
        Orden CORRECTO: Arch → Devs → Model → Dqa
        """
        # Setup equipos con capacidad suficiente
        teams = {
            1: Team(id=1, name="Arch", total_devs=5, tier_capacities={1: 16}),
            2: Team(id=2, name="Model", total_devs=5, tier_capacities={2: 80}),
            3: Team(id=3, name="Devs", total_devs=5, tier_capacities={3: 80}),
            4: Team(id=4, name="Dqa", total_devs=5, tier_capacities={2: 24})
        }
        
        # Un solo proyecto para enfocarnos en la secuencia de fases
        projects = {
            1: Project(id=1, name="TestProject", priority=1,
                      start_date=date(2025, 6, 26),
                      due_date_wo_qa=date(2025, 9, 1),
                      due_date_with_qa=date(2025, 9, 15))
        }
        
        # Asignaciones para todas las fases del proyecto
        assignments = [
            # Arch - debe ser la primera fase
            Assignment(
                id=1, project_id=1, project_name="TestProject", 
                project_priority=1, team_id=1, team_name="Arch", 
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=160,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            ),
            # Devs - debe empezar DESPUÉS que termine Arch
            Assignment(
                id=2, project_id=1, project_name="TestProject",
                project_priority=1, team_id=3, team_name="Devs",
                tier=3, devs_assigned=1.0, max_devs=1.0, estimated_hours=80,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            ),
            # Model - debe empezar DESPUÉS que termine Devs
            Assignment(
                id=3, project_id=1, project_name="TestProject",
                project_priority=1, team_id=2, team_name="Model",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=80,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            ),
            # Dqa - debe empezar DESPUÉS que termine Model
            Assignment(
                id=4, project_id=1, project_name="TestProject",
                project_priority=1, team_id=4, team_name="Dqa",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=24,
                ready_to_start_date=date(2025, 6, 26), assignment_start_date=date(2025, 6, 26)
            )
        ]
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Obtener asignaciones por fase
        arch_assignment = next(a for a in result.assignments if a.team_name == "Arch")
        devs_assignment = next(a for a in result.assignments if a.team_name == "Devs")
        model_assignment = next(a for a in result.assignments if a.team_name == "Model")
        dqa_assignment = next(a for a in result.assignments if a.team_name == "Dqa")
        
        # VERIFICAR SECUENCIA CORRECTA: Arch → Devs → Model → Dqa
        assert devs_assignment.calculated_start_date > arch_assignment.calculated_end_date, \
            f"Devs debe empezar después que termine Arch. Arch termina: {arch_assignment.calculated_end_date}, Devs empieza: {devs_assignment.calculated_start_date}"
        
        assert model_assignment.calculated_start_date > devs_assignment.calculated_end_date, \
            f"Model debe empezar después que termine Devs. Devs termina: {devs_assignment.calculated_end_date}, Model empieza: {model_assignment.calculated_start_date}"
        
        assert dqa_assignment.calculated_start_date > model_assignment.calculated_end_date, \
            f"Dqa debe empezar después que termine Model. Model termina: {model_assignment.calculated_end_date}, Dqa empieza: {dqa_assignment.calculated_start_date}"
    
    def test_priority_order_with_sufficient_capacity(self):
        """
        CASO CRÍTICO: Los proyectos deben respetar el orden de prioridades
        incluso cuando hay capacidad suficiente para ejecutarlos en paralelo
        """
        # Setup equipos con capacidad SUFICIENTE
        teams = {
            1: Team(id=1, name="Arch", total_devs=5, tier_capacities={1: 16}),
            2: Team(id=2, name="Model", total_devs=5, tier_capacities={2: 80}),
            3: Team(id=3, name="Devs", total_devs=5, tier_capacities={3: 80}),
            4: Team(id=4, name="Dqa", total_devs=5, tier_capacities={2: 24})
        }
        
        # Proyectos con prioridades diferentes
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
            # Solo Arch para simplificar el test
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project.name, 
                project_priority=project.priority, team_id=1, team_name="Arch", 
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=16,
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
        
        # Obtener asignaciones por proyecto
        project_b_arch = next(a for a in result.assignments if a.project_name == "B")
        project_a_arch = next(a for a in result.assignments if a.project_name == "a")
        project2_arch = next(a for a in result.assignments if a.project_name == "project2")
        
        # VERIFICAR QUE SE RESPETE EL ORDEN DE PRIORIDADES
        # Proyecto B (prioridad 1) debe empezar primero
        assert project_b_arch.calculated_start_date == date(2025, 6, 26), "Proyecto B debe empezar el 26/06"
        
        # Proyecto a (prioridad 2) debe empezar DESPUÉS que termine B
        assert project_a_arch.calculated_start_date > project_b_arch.calculated_end_date, \
            f"Proyecto a debe empezar después que termine B. B termina: {project_b_arch.calculated_end_date}, a empieza: {project_a_arch.calculated_start_date}"
        
        # Proyecto project2 (prioridad 3) debe empezar DESPUÉS que termine a
        assert project2_arch.calculated_start_date > project_a_arch.calculated_end_date, \
            f"Proyecto project2 debe empezar después que termine a. a termina: {project_a_arch.calculated_end_date}, project2 empieza: {project2_arch.calculated_start_date}"
    
    def test_phase_sequence_with_different_ready_dates(self):
        """
        CASO CRÍTICO: Cuando las fases tienen diferentes ready_to_start_date,
        deben respetar la secuencia correcta Arch → Devs → Model → Dqa
        """
        # Setup equipos
        teams = {
            1: Team(id=1, name="Arch", total_devs=5, tier_capacities={1: 16}),
            2: Team(id=2, name="Model", total_devs=5, tier_capacities={2: 80}),
            3: Team(id=3, name="Devs", total_devs=5, tier_capacities={3: 80}),
            4: Team(id=4, name="Dqa", total_devs=5, tier_capacities={2: 24})
        }
        
        # Un proyecto
        projects = {
            1: Project(id=1, name="ProblematicProject", priority=1,
                      start_date=date(2025, 6, 26),
                      due_date_wo_qa=date(2025, 11, 1),
                      due_date_with_qa=date(2025, 11, 15))
        }
        
        # Asignaciones con ready_to_start_date diferentes
        assignments = [
            # Arch - ready para empezar tarde (septiembre)
            Assignment(
                id=1, project_id=1, project_name="ProblematicProject", 
                project_priority=1, team_id=1, team_name="Arch", 
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=320,
                ready_to_start_date=date(2025, 9, 4),  # Ready tarde
                assignment_start_date=date(2025, 6, 26)
            ),
            # Devs - ready para empezar temprano (julio)
            Assignment(
                id=2, project_id=1, project_name="ProblematicProject",
                project_priority=1, team_id=3, team_name="Devs",
                tier=3, devs_assigned=1.0, max_devs=1.0, estimated_hours=160,
                ready_to_start_date=date(2025, 7, 17),  # Ready temprano
                assignment_start_date=date(2025, 6, 26)
            ),
            # Model - ready para empezar en agosto
            Assignment(
                id=3, project_id=1, project_name="ProblematicProject",
                project_priority=1, team_id=2, team_name="Model",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=200,
                ready_to_start_date=date(2025, 8, 7),  # Ready en agosto
                assignment_start_date=date(2025, 6, 26)
            ),
            # Dqa - ready para empezar en octubre
            Assignment(
                id=4, project_id=1, project_name="ProblematicProject",
                project_priority=1, team_id=4, team_name="Dqa",
                tier=2, devs_assigned=1.0, max_devs=1.0, estimated_hours=48,
                ready_to_start_date=date(2025, 10, 16),  # Ready tarde
                assignment_start_date=date(2025, 6, 26)
            )
        ]
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Obtener asignaciones por fase
        arch_assignment = next(a for a in result.assignments if a.team_name == "Arch")
        devs_assignment = next(a for a in result.assignments if a.team_name == "Devs")
        model_assignment = next(a for a in result.assignments if a.team_name == "Model")
        dqa_assignment = next(a for a in result.assignments if a.team_name == "Dqa")
        
        # VERIFICAR SECUENCIA CORRECTA: Arch → Devs → Model → Dqa
        # Incluso con ready_dates diferentes, la secuencia debe respetarse
        assert devs_assignment.calculated_start_date > arch_assignment.calculated_end_date, \
            f"Devs debe empezar después que termine Arch. Arch termina: {arch_assignment.calculated_end_date}, Devs empieza: {devs_assignment.calculated_start_date}"
        
        assert model_assignment.calculated_start_date > devs_assignment.calculated_end_date, \
            f"Model debe empezar después que termine Devs. Devs termina: {devs_assignment.calculated_end_date}, Model empieza: {model_assignment.calculated_start_date}"
        
        assert dqa_assignment.calculated_start_date > model_assignment.calculated_end_date, \
            f"Dqa debe empezar después que termine Model. Model termina: {model_assignment.calculated_end_date}, Dqa empieza: {dqa_assignment.calculated_start_date}"
    
    def test_multiple_projects_with_limited_resources(self):
        """
        CASO CRÍTICO: Múltiples proyectos con recursos limitados
        Debe manejar correctamente la competencia por recursos
        """
        # Setup equipos con capacidad limitada
        teams = {
            1: Team(id=1, name="Arch", total_devs=1, tier_capacities={1: 16}),
            2: Team(id=2, name="Model", total_devs=1, tier_capacities={2: 80}),
            3: Team(id=3, name="Devs", total_devs=1, tier_capacities={3: 80}),
            4: Team(id=4, name="Dqa", total_devs=1, tier_capacities={2: 24})
        }
        
        # Múltiples proyectos
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
        
        # Asignaciones para ambos proyectos
        assignments = []
        assignment_id = 1
        
        for project_id in [1, 2]:
            project_name = f"Project{'A' if project_id == 1 else 'B'}"
            priority = project_id
            
            # Solo Arch para simplificar
            assignments.append(Assignment(
                id=assignment_id, project_id=project_id, project_name=project_name,
                project_priority=priority, team_id=1, team_name="Arch",
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=160,
                ready_to_start_date=date(2025, 6, 26),
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
        
        # Obtener asignaciones
        project_a_arch = next(a for a in result.assignments if a.project_name == "ProjectA")
        project_b_arch = next(a for a in result.assignments if a.project_name == "ProjectB")
        
        # Verificar que NO hay solapamiento (recursos limitados)
        assert not (project_a_arch.calculated_start_date <= project_b_arch.calculated_start_date <= project_a_arch.calculated_end_date), \
            "No debe haber solapamiento con recursos limitados"
        
        # Verificar que ProjectA (prioridad 1) va primero
        assert project_a_arch.calculated_start_date < project_b_arch.calculated_start_date, \
            "ProjectA debe empezar antes que ProjectB por prioridad"