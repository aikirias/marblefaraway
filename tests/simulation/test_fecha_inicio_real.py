"""
Test para verificar que el scheduler usa correctamente la fecha_inicio_real del proyecto
"""
import pytest
from datetime import date
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestFechaInicioReal:
    
    def test_scheduler_usa_fecha_inicio_real(self):
        """
        Verifica que el scheduler use la fecha_inicio_real del proyecto como fecha de inicio
        para la primera asignación del proyecto.
        
        Caso de prueba:
        - Proyecto A con fecha_inicio_real = 2025/06/29
        - Fecha de simulación = 2025/06/25 (anterior a la fecha_inicio_real)
        - Verificar que la primera asignación comience en 2025/06/29
        """
        
        # Setup equipos con IDs que coinciden con el orden en el scheduler
        # Según el scheduler: team_order = {2: 1, 1: 2, 3: 3, 4: 4}
        # Donde 2 = Arch, 1 = Devs, 3 = Model, 4 = Dqa
        teams = {
            2: Team(id=2, name="Arch", total_devs=2, busy_devs=0, 
                   tier_capacities={1: 50, 2: 100, 3: 150}),
            1: Team(id=1, name="Devs", total_devs=2, busy_devs=0, 
                   tier_capacities={1: 50, 2: 100, 3: 150}),
            3: Team(id=3, name="Model", total_devs=2, busy_devs=0, 
                   tier_capacities={1: 50, 2: 100, 3: 150}),
            4: Team(id=4, name="Dqa", total_devs=2, busy_devs=0, 
                   tier_capacities={1: 50, 2: 100, 3: 150})
        }
        
        # Fecha de inicio real del proyecto
        fecha_inicio_real = date(2025, 6, 29)
        
        # Proyecto con fecha_inicio_real
        projects = {
            1: Project(
                id=1, 
                name="Proyecto A", 
                priority=1,
                start_date=date(2025, 6, 25),  # Fecha de inicio planificada
                due_date_wo_qa=date(2025, 7, 15),
                due_date_with_qa=date(2025, 7, 20),
                fecha_inicio_real=fecha_inicio_real  # Fecha de inicio real
            )
        }
        
        # Asignaciones para el proyecto
        assignments = [
            # Primera asignación (Arch) - debería comenzar en fecha_inicio_real
            Assignment(
                id=1, project_id=1, project_name="Proyecto A", project_priority=1,
                team_id=2, team_name="Arch", tier=1, devs_assigned=2.0, max_devs=2.0,
                estimated_hours=50,  # 50 horas / (8 horas/día * 2 devs) = 3.125 días
                ready_to_start_date=date(2025, 6, 25),  # Fecha anterior a fecha_inicio_real
                assignment_start_date=date(2025, 6, 25)
            ),
            # Segunda asignación (Devs) - debería comenzar después de Arch
            Assignment(
                id=2, project_id=1, project_name="Proyecto A", project_priority=1,
                team_id=1, team_name="Devs", tier=2, devs_assigned=2.0, max_devs=2.0,
                estimated_hours=100,  # 100 horas / (8 horas/día * 2 devs) = 6.25 días
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            # Tercera asignación (Model)
            Assignment(
                id=3, project_id=1, project_name="Proyecto A", project_priority=1,
                team_id=3, team_name="Model", tier=1, devs_assigned=2.0, max_devs=2.0,
                estimated_hours=50,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            # Cuarta asignación (Dqa)
            Assignment(
                id=4, project_id=1, project_name="Proyecto A", project_priority=1,
                team_id=4, team_name="Dqa", tier=1, devs_assigned=2.0, max_devs=2.0,
                estimated_hours=50,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            )
        ]
        
        # Fecha de simulación anterior a fecha_inicio_real
        simulation_start_date = date(2025, 6, 25)
        
        simulation_input = SimulationInput(
            teams=teams, 
            projects=projects, 
            assignments=assignments,
            simulation_start_date=simulation_start_date
        )
        
        # Ejecutar simulación
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Obtener asignaciones ordenadas por equipo
        project_assignments = [a for a in result.assignments if a.project_id == 1]
        sorted_assignments = sorted(project_assignments, key=lambda x: x.team_id)
        
        # Imprimir resultados para debugging
        print("\n🔍 RESULTADOS DE LA SIMULACIÓN:")
        for assignment in sorted_assignments:
            print(f"  {assignment.team_name}: {assignment.calculated_start_date} a {assignment.calculated_end_date}")
        
        # Verificar que la primera asignación (Arch) comience en fecha_inicio_real
        arch_assignment = next(a for a in sorted_assignments if a.team_name == "Arch")
        
        print(f"\n🔍 VERIFICACIÓN DE FECHA DE INICIO REAL:")
        print(f"  Fecha de inicio real del proyecto: {fecha_inicio_real}")
        print(f"  Fecha de inicio calculada para Arch: {arch_assignment.calculated_start_date}")
        
        # La asignación de Arch debe comenzar exactamente en la fecha_inicio_real
        assert arch_assignment.calculated_start_date == fecha_inicio_real, \
            f"La asignación de Arch debería comenzar en la fecha_inicio_real ({fecha_inicio_real}), " \
            f"pero comienza en {arch_assignment.calculated_start_date}"
        
        # Verificar que las demás asignaciones respeten la secuencia
        devs_assignment = next(a for a in sorted_assignments if a.team_name == "Devs")
        assert devs_assignment.calculated_start_date >= arch_assignment.calculated_end_date, \
            f"La asignación de Devs debería comenzar después de que termine Arch"
        
        print("✅ El scheduler usa correctamente la fecha_inicio_real del proyecto")