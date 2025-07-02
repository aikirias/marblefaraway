"""
Tests de casos críticos de simulación APE
"""

import pytest
from datetime import date
from app.modules.common.models import Team, Project, Assignment, SimulationInput
from app.modules.simulation.scheduler import ProjectScheduler


class TestSimulationScenarios:
    """Tests para casos críticos del algoritmo de scheduling"""
    
    def test_simple_project_sequential_phases(self):
        """
        CASO CRÍTICO 1: Proyecto simple con 4 fases secuenciales
        Verificar que Arch → Devs → Model → Dqa se ejecutan en orden correcto
        """
        # Setup: 1 proyecto, 4 equipos, 4 asignaciones secuenciales
        # Setup equipos con IDs que coinciden con el orden en el scheduler
        # Según el scheduler: team_order = {2: 1, 1: 2, 3: 3, 4: 4}
        # Donde 2 = Arch, 1 = Devs, 3 = Model, 4 = Dqa
        teams = {
            2: Team(id=2, name="Arch", total_devs=2, tier_capacities={1: 16}),
            1: Team(id=1, name="Devs", total_devs=3, tier_capacities={3: 80}),
            3: Team(id=3, name="Model", total_devs=2, tier_capacities={2: 80}),
            4: Team(id=4, name="Dqa", total_devs=2, tier_capacities={2: 24})
        }
        
        projects = {
            1: Project(id=1, name="Simple Project", priority=1,
                      start_date=date(2025, 1, 1),
                      due_date_wo_qa=date(2025, 3, 1),
                      due_date_with_qa=date(2025, 3, 15))
        }
        
        assignments = [
            Assignment(id=1, project_id=1, project_name="Simple Project", project_priority=1,
                      team_id=2, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=2.0,
                      estimated_hours=16, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            Assignment(id=2, project_id=1, project_name="Simple Project", project_priority=1,
                      team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=3.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            Assignment(id=3, project_id=1, project_name="Simple Project", project_priority=1,
                      team_id=3, team_name="Model", tier=2, devs_assigned=1.0, max_devs=2.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            Assignment(id=4, project_id=1, project_name="Simple Project", project_priority=1,
                      team_id=4, team_name="Dqa", tier=2, devs_assigned=1.0, max_devs=2.0,
                      estimated_hours=24, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1))
        ]
        
        simulation_input = SimulationInput(
            teams=teams,
            projects=projects,
            assignments=assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        
        # Ejecutar simulación
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Verificaciones críticas
        arch_assignment = next(a for a in result.assignments if a.team_name == "Arch")
        model_assignment = next(a for a in result.assignments if a.team_name == "Model")
        devs_assignment = next(a for a in result.assignments if a.team_name == "Devs")
        dqa_assignment = next(a for a in result.assignments if a.team_name == "Dqa")
        
        # Verificar orden secuencial correcto: Arch → Devs → Model → Dqa
        assert arch_assignment.calculated_end_date < devs_assignment.calculated_start_date
        assert devs_assignment.calculated_end_date < model_assignment.calculated_start_date
        assert model_assignment.calculated_end_date < dqa_assignment.calculated_start_date
        
        # Verificar cálculo correcto de fechas
        assert arch_assignment.calculated_start_date == date(2025, 1, 1)
        # Arch: 16h / (1 dev * 8h/día) = 2 días → termina 1 día después del inicio
        # 2025-01-01 es miércoles, así que debería terminar el jueves 2025-01-02
        # Pero con el cálculo corregido, 2 días de trabajo terminan el día siguiente
        expected_end = date(2025, 1, 2)  # 1 día hábil después
        assert arch_assignment.calculated_end_date == expected_end
        
        # Devs empieza el día siguiente a que termina Arch
        assert devs_assignment.calculated_start_date == date(2025, 1, 3)
    
    def test_multiple_projects_priority_handling(self):
        """
        CASO CRÍTICO 2: Múltiples proyectos con diferentes prioridades
        Verificar que prioridad 1 se ejecuta antes que prioridad 2
        """
        teams = {
            1: Team(id=1, name="Devs", total_devs=1, tier_capacities={3: 80})  # Solo 1 dev para forzar secuencialidad
        }
        
        projects = {
            1: Project(id=1, name="High Priority", priority=1,
                      start_date=date(2025, 1, 1),
                      due_date_wo_qa=date(2025, 2, 1),
                      due_date_with_qa=date(2025, 2, 15)),
            2: Project(id=2, name="Low Priority", priority=2,
                      start_date=date(2025, 1, 1),
                      due_date_wo_qa=date(2025, 2, 1),
                      due_date_with_qa=date(2025, 2, 15))
        }
        
        assignments = [
            Assignment(id=1, project_id=1, project_name="High Priority", project_priority=1,
                      team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=2.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            Assignment(id=2, project_id=2, project_name="Low Priority", project_priority=2,
                      team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=2.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1))
        ]
        
        simulation_input = SimulationInput(
            teams=teams,
            projects=projects,
            assignments=assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        high_priority = next(a for a in result.assignments if a.project_priority == 1)
        low_priority = next(a for a in result.assignments if a.project_priority == 2)
        
        # Verificar que alta prioridad termina antes que baja prioridad empiece
        assert high_priority.calculated_end_date < low_priority.calculated_start_date
        assert high_priority.calculated_start_date == date(2025, 1, 1)
    
    def test_limited_capacity_no_parallelism(self):
        """
        CASO CRÍTICO 3: Capacidad limitada impide paralelismo
        Equipo con 1 dev, 2 proyectos → no pueden ejecutarse en paralelo
        """
        teams = {
            1: Team(id=1, name="Devs", total_devs=1, tier_capacities={3: 80})
        }
        
        projects = {
            1: Project(id=1, name="Project A", priority=1,
                      start_date=date(2025, 1, 1),
                      due_date_wo_qa=date(2025, 2, 1),
                      due_date_with_qa=date(2025, 2, 15)),
            2: Project(id=2, name="Project B", priority=2,
                      start_date=date(2025, 1, 1),
                      due_date_wo_qa=date(2025, 2, 1),
                      due_date_with_qa=date(2025, 2, 15))
        }
        
        assignments = [
            Assignment(id=1, project_id=1, project_name="Project A", project_priority=1,
                      team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=1.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            Assignment(id=2, project_id=2, project_name="Project B", project_priority=2,
                      team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=1.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1))
        ]
        
        simulation_input = SimulationInput(
            teams=teams,
            projects=projects,
            assignments=assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        project_a = next(a for a in result.assignments if a.project_name == "Project A")
        project_b = next(a for a in result.assignments if a.project_name == "Project B")
        
        # Verificar que NO hay solapamiento (paralelismo imposible)
        assert not (project_a.calculated_start_date <= project_b.calculated_start_date <= project_a.calculated_end_date)
        assert not (project_b.calculated_start_date <= project_a.calculated_start_date <= project_b.calculated_end_date)
        
        # Verificar que Project A (prioridad 1) va primero
        assert project_a.calculated_start_date < project_b.calculated_start_date
    
    def test_ready_to_start_date_constraint(self):
        """
        CASO CRÍTICO 4: Restricción de ready_to_start_date
        Proyecto no puede empezar antes de fecha mínima
        """
        teams = {
            1: Team(id=1, name="Devs", total_devs=5, tier_capacities={3: 80})
        }
        
        projects = {
            1: Project(id=1, name="Future Project", priority=1,
                      start_date=date(2025, 1, 1),
                      due_date_wo_qa=date(2025, 3, 1),
                      due_date_with_qa=date(2025, 3, 15))
        }
        
        # Assignment que no puede empezar hasta febrero
        assignments = [
            Assignment(id=1, project_id=1, project_name="Future Project", project_priority=1,
                      team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=5.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 2, 1),  # Constraint
                      assignment_start_date=date(2025, 1, 1))
        ]
        
        simulation_input = SimulationInput(
            teams=teams,
            projects=projects,
            assignments=assignments,
            simulation_start_date=date(2025, 1, 1)  # Simulación empieza en enero
        )
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        assignment = result.assignments[0]
        
        # Verificar que respeta la fecha mínima
        assert assignment.calculated_start_date >= date(2025, 2, 1)
        assert assignment.calculated_start_date == date(2025, 2, 1)  # Debe empezar exactamente en la fecha mínima
    
    def test_full_ape_workflow_sequence(self):
        """
        CASO CRÍTICO 5: Flujo completo APE con dependencias secuenciales
        Arch → Devs → Model → Dqa con cálculos reales
        """
        # Setup equipos especializados según arquitectura APE
        # Setup equipos con IDs que coinciden con el orden en el scheduler
        # Según el scheduler: team_order = {2: 1, 1: 2, 3: 3, 4: 4}
        # Donde 2 = Arch, 1 = Devs, 3 = Model, 4 = Dqa
        teams = {
            2: Team(id=2, name="Arch", total_devs=2, tier_capacities={1: 16, 2: 32, 3: 72, 4: 240}),
            1: Team(id=1, name="Devs", total_devs=6, tier_capacities={1: 16, 2: 40, 3: 80, 4: 120}),
            3: Team(id=3, name="Model", total_devs=4, tier_capacities={1: 40, 2: 80, 3: 120, 4: 160}),
            4: Team(id=4, name="Dqa", total_devs=3, tier_capacities={1: 8, 2: 24, 3: 40})  # Sin Tier 4
        }
        
        projects = {
            1: Project(id=1, name="Full APE Project", priority=1, start_date=date(2025, 1, 1),
                      due_date_wo_qa=date(2025, 3, 1), due_date_with_qa=date(2025, 3, 15))
        }
        
        # Asignaciones según patrón APE real con IDs correctos
        assignments = [
            # Arch: Tier 1, 1 dev (team_id=2)
            Assignment(id=1, project_id=1, project_name="Full APE Project", project_priority=1,
                      team_id=2, team_name="Arch", tier=1, devs_assigned=1.0, max_devs=2.0,
                      estimated_hours=16, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            # Devs: Tier 3, 2 devs (team_id=1)
            Assignment(id=2, project_id=1, project_name="Full APE Project", project_priority=1,
                      team_id=1, team_name="Devs", tier=3, devs_assigned=2.0, max_devs=6.0,
                      estimated_hours=160, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            # Model: Tier 2, 1 dev (team_id=3)
            Assignment(id=3, project_id=1, project_name="Full APE Project", project_priority=1,
                      team_id=3, team_name="Model", tier=2, devs_assigned=1.0, max_devs=4.0,
                      estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1)),
            # Dqa: Tier 2, 1 dev (team_id=4)
            Assignment(id=4, project_id=1, project_name="Full APE Project", project_priority=1,
                      team_id=4, team_name="Dqa", tier=2, devs_assigned=1.0, max_devs=3.0,
                      estimated_hours=24, ready_to_start_date=date(2025, 1, 1),
                      assignment_start_date=date(2025, 1, 1))
        ]
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 1, 1)
        )
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Obtener asignaciones por equipo
        arch = next(a for a in result.assignments if a.team_name == "Arch")
        model = next(a for a in result.assignments if a.team_name == "Model")
        devs = next(a for a in result.assignments if a.team_name == "Devs")
        dqa = next(a for a in result.assignments if a.team_name == "Dqa")
        
        # Verificar secuencia estricta: Arch → Devs → Model → Dqa
        assert arch.calculated_start_date == date(2025, 1, 1)
        assert arch.calculated_end_date < devs.calculated_start_date
        assert devs.calculated_end_date < model.calculated_start_date
        assert model.calculated_end_date < dqa.calculated_start_date
        
        # Verificar cálculos específicos
        # Arch: 16h / (1 dev * 8h/día) = 2 días → termina 02/01
        assert arch.calculated_end_date == date(2025, 1, 2)
        
        # Devs empieza después de Arch: 160h / (2 devs * 8h/día) = 10 días → 03/01 a 16/01
        assert devs.calculated_start_date == date(2025, 1, 3)
        assert devs.calculated_end_date == date(2025, 1, 16)
        
        # Model empieza después de Devs: 80h / (1 dev * 8h/día) = 10 días → 17/01 a 30/01
        assert model.calculated_start_date == date(2025, 1, 17)
        assert model.calculated_end_date == date(2025, 1, 30)
        
        # Dqa empieza después de Model: 24h / (1 dev * 8h/día) = 3 días → 31/01 a 04/02
        assert dqa.calculated_start_date == date(2025, 1, 31)
        assert dqa.calculated_end_date == date(2025, 2, 4)
        
        # Dqa empieza día siguiente
        assert dqa.calculated_start_date == date(2025, 1, 31)
        # Dqa: 24h / (1 dev * 8h/día) = 3 días
        assert dqa.calculated_end_date == date(2025, 2, 4)
    
    def test_project_summaries_generation(self):
        """Test que se generan correctamente los resúmenes de proyecto"""
        teams = {1: Team(id=1, name="Devs", total_devs=3, tier_capacities={3: 80})}
        projects = {1: Project(id=1, name="Test Project", priority=1, start_date=date(2025, 1, 1),
                              due_date_wo_qa=date(2025, 2, 1), due_date_with_qa=date(2025, 2, 15))}
        assignments = [Assignment(id=1, project_id=1, project_name="Test Project", project_priority=1,
                                 team_id=1, team_name="Devs", tier=3, devs_assigned=1.0, max_devs=3.0,
                                 estimated_hours=80, ready_to_start_date=date(2025, 1, 1),
                                 assignment_start_date=date(2025, 1, 1))]
        
        simulation_input = SimulationInput(teams=teams, projects=projects, assignments=assignments,
                                         simulation_start_date=date(2025, 1, 1))
        
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Verificar que se generó el resumen
        assert len(result.project_summaries) == 1
        summary = result.project_summaries[0]
        
        assert summary['project_id'] == 1
        assert summary['project_name'] == "Test Project"
        assert summary['priority'] == 1
        assert summary['total_assignments'] == 1
        assert summary['total_hours'] == 80
        assert 'calculated_start_date' in summary
        assert 'calculated_end_date' in summary