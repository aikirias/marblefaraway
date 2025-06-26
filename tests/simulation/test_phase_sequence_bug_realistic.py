"""
Test para reproducir el bug de secuencia de fases con datos más realistas
Basado en el ejemplo del usuario donde Devs empieza antes que Arch
"""
import pytest
from datetime import date
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestPhaseSequenceBugRealistic:
    
    def test_phase_sequence_bug_with_different_ready_dates(self):
        """
        REPRODUCIR BUG: Cuando las fases tienen diferentes ready_to_start_date,
        puede que no respeten la secuencia correcta Arch → Devs → Model → Dqa
        
        Escenario problemático del usuario:
        - Arch: 2025-09-04 a 2025-10-15
        - Devs: 2025-07-17 a 2025-08-06 ← ¡Empieza ANTES que Arch!
        - Model: 2025-08-07 a 2025-09-03 ← También antes que termine Arch
        - Dqa: 2025-10-16 a 2025-10-22
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
        
        # Asignaciones con ready_to_start_date diferentes que podrían causar el problema
        assignments = [
            # Arch - ready para empezar tarde (septiembre)
            Assignment(
                id=1, project_id=1, project_name="ProblematicProject", 
                project_priority=1, team_id=1, team_name="Arch", 
                tier=1, devs_assigned=1.0, max_devs=1.0, estimated_hours=320,  # Muchas horas
                ready_to_start_date=date(2025, 9, 4),  # Ready tarde
                assignment_start_date=date(2025, 6, 26)
            ),
            # Devs - ready para empezar temprano (julio) - ESTO PODRÍA CAUSAR EL BUG
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
        
        print(f"\n🔍 SECUENCIA DE FASES CON READY_DATES DIFERENTES:")
        print(f"Arch:  {arch_assignment.calculated_start_date} a {arch_assignment.calculated_end_date} (ready: {arch_assignment.ready_to_start_date})")
        print(f"Devs:  {devs_assignment.calculated_start_date} a {devs_assignment.calculated_end_date} (ready: {devs_assignment.ready_to_start_date})")
        print(f"Model: {model_assignment.calculated_start_date} a {model_assignment.calculated_end_date} (ready: {model_assignment.ready_to_start_date})")
        print(f"Dqa:   {dqa_assignment.calculated_start_date} a {dqa_assignment.calculated_end_date} (ready: {dqa_assignment.ready_to_start_date})")
        
        # VERIFICAR SI SE REPRODUCE EL BUG
        # El bug sería que Devs empiece antes que termine Arch
        if devs_assignment.calculated_start_date <= arch_assignment.calculated_end_date:
            print(f"🐛 BUG REPRODUCIDO: Devs empieza antes/durante Arch")
            print(f"   Arch termina: {arch_assignment.calculated_end_date}")
            print(f"   Devs empieza: {devs_assignment.calculated_start_date}")
            
            # Hacer que el test falle para mostrar el problema
            assert False, f"BUG: Devs no puede empezar antes que termine Arch. Arch termina: {arch_assignment.calculated_end_date}, Devs empieza: {devs_assignment.calculated_start_date}"
        
        # VERIFICAR SECUENCIA CORRECTA: Arch → Devs → Model → Dqa
        assert devs_assignment.calculated_start_date > arch_assignment.calculated_end_date, \
            f"Devs debe empezar después que termine Arch. Arch termina: {arch_assignment.calculated_end_date}, Devs empieza: {devs_assignment.calculated_start_date}"
        
        assert model_assignment.calculated_start_date > devs_assignment.calculated_end_date, \
            f"Model debe empezar después que termine Devs. Devs termina: {devs_assignment.calculated_end_date}, Model empieza: {model_assignment.calculated_start_date}"
        
        assert dqa_assignment.calculated_start_date > model_assignment.calculated_end_date, \
            f"Dqa debe empezar después que termine Model. Model termina: {model_assignment.calculated_end_date}, Dqa empieza: {dqa_assignment.calculated_start_date}"
        
        print(f"✅ Secuencia de fases correcta: Arch → Devs → Model → Dqa")