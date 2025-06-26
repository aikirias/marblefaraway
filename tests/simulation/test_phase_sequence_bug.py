"""
Test para reproducir el bug de secuencia de fases dentro del proyecto
Las fases deben seguir el orden: Arch → Devs → Model → Dqa
"""
import pytest
from datetime import date
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestPhaseSequenceBug:
    
    def test_phase_sequence_within_project_bug(self):
        """
        REPRODUCIR BUG: Las fases dentro de un proyecto no respetan el orden secuencial
        
        Orden CORRECTO: Arch → Devs → Model → Dqa
        BUG: Devs y Model empiezan antes que termine Arch
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
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=160,  # Más horas para que dure más
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
        
        print(f"\n🔍 SECUENCIA DE FASES CALCULADA:")
        print(f"Arch:  {arch_assignment.calculated_start_date} a {arch_assignment.calculated_end_date}")
        print(f"Devs:  {devs_assignment.calculated_start_date} a {devs_assignment.calculated_end_date}")
        print(f"Model: {model_assignment.calculated_start_date} a {model_assignment.calculated_end_date}")
        print(f"Dqa:   {dqa_assignment.calculated_start_date} a {dqa_assignment.calculated_end_date}")
        
        # VERIFICAR SECUENCIA CORRECTA: Arch → Devs → Model → Dqa
        
        # Devs debe empezar DESPUÉS que termine Arch
        assert devs_assignment.calculated_start_date > arch_assignment.calculated_end_date, \
            f"Devs debe empezar después que termine Arch. Arch termina: {arch_assignment.calculated_end_date}, Devs empieza: {devs_assignment.calculated_start_date}"
        
        # Model debe empezar DESPUÉS que termine Devs
        assert model_assignment.calculated_start_date > devs_assignment.calculated_end_date, \
            f"Model debe empezar después que termine Devs. Devs termina: {devs_assignment.calculated_end_date}, Model empieza: {model_assignment.calculated_start_date}"
        
        # Dqa debe empezar DESPUÉS que termine Model
        assert dqa_assignment.calculated_start_date > model_assignment.calculated_end_date, \
            f"Dqa debe empezar después que termine Model. Model termina: {model_assignment.calculated_end_date}, Dqa empieza: {dqa_assignment.calculated_start_date}"
        
        print(f"✅ Secuencia de fases correcta: Arch → Devs → Model → Dqa")