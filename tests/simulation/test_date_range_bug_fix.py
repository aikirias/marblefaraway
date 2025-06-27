"""
Test específico para validar la corrección del bug de fechas fuera de rango
"""
import pytest
from datetime import date, timedelta
from app.modules.simulation.scheduler import ProjectScheduler, validate_date_range, MIN_DATE, MAX_DATE
from app.modules.common.models import Team, Project, Assignment, SimulationInput


class TestDateRangeBugFix:
    
    def test_validate_date_range_function(self):
        """Test de la función de validación de fechas"""
        
        # Fecha normal - debe pasar sin cambios
        normal_date = date(2025, 6, 26)
        assert validate_date_range(normal_date, "test") == normal_date
        
        # Fecha muy antigua - debe ajustarse al mínimo
        ancient_date = date(1800, 1, 1)
        result = validate_date_range(ancient_date, "ancient")
        assert result == MIN_DATE
        
        # Fecha muy futura - debe ajustarse al máximo
        # No podemos crear directamente date(10000, 1, 1) porque Python lo rechaza
        # Pero podemos simular el escenario usando una fecha válida que exceda nuestro MAX_DATE
        future_date = date(2150, 1, 1)  # Fecha que excede nuestro MAX_DATE (2100-12-31)
        result = validate_date_range(future_date, "future")
        assert result == MAX_DATE
        
        print(f"✅ Validación de fechas funciona correctamente")
        print(f"  Fecha antigua {ancient_date} → {result}")
        print(f"  Fecha futura {future_date} → {result}")
    
    def test_extreme_date_scenario(self):
        """Test con escenario que podría generar fechas extremas"""
        
        # Setup con datos que podrían causar el problema
        teams = {
            1: Team(id=1, name="TestTeam", total_devs=1, busy_devs=0, 
                   tier_capacities={1: 8})
        }
        
        projects = {
            1: Project(id=1, name="TestProject", priority=1,
                      start_date=date(2025, 6, 25),
                      due_date_wo_qa=date(2025, 6, 25),
                      due_date_with_qa=date(2025, 6, 25))
        }
        
        # Asignación con muchas horas que podría causar fechas extremas
        assignments = [
            Assignment(
                id=1, project_id=1, project_name="TestProject", project_priority=1,
                team_id=1, team_name="TestTeam", tier=1, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=100000,  # Muchas horas para forzar fechas futuras
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            )
        ]
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación - no debe fallar
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Verificar que las fechas están en rango válido
        for assignment in result.assignments:
            if assignment.calculated_start_date:
                assert MIN_DATE <= assignment.calculated_start_date <= MAX_DATE
                print(f"✅ Fecha de inicio válida: {assignment.calculated_start_date}")
            
            if assignment.calculated_end_date:
                assert MIN_DATE <= assignment.calculated_end_date <= MAX_DATE
                print(f"✅ Fecha de fin válida: {assignment.calculated_end_date}")
    
    def test_monitoring_module_safety(self):
        """Test para verificar que el módulo de monitoring maneja fechas extremas"""
        from app.modules.monitoring.monitoring import safe_business_day_calculation
        
        # Test con fecha normal
        normal_date = date(2025, 6, 26)
        result = safe_business_day_calculation(normal_date, 1, "test")
        assert MIN_DATE <= result <= MAX_DATE
        print(f"✅ Cálculo normal: {normal_date} + 1 día = {result}")
        
        # Test con fecha extrema que causaría el error original
        extreme_date = date(9999, 12, 31)
        result = safe_business_day_calculation(extreme_date, 1, "extreme_test")
        assert MIN_DATE <= result <= MAX_DATE
        print(f"✅ Cálculo extremo: {extreme_date} + 1 día = {result}")
        
        # Test con offset grande
        normal_date = date(2025, 6, 26)
        result = safe_business_day_calculation(normal_date, 10000, "large_offset")
        assert MIN_DATE <= result <= MAX_DATE
        print(f"✅ Offset grande: {normal_date} + 10000 días = {result}")
    
    def test_scheduler_robustness_with_bad_data(self):
        """Test de robustez del scheduler con datos problemáticos"""
        
        teams = {
            1: Team(id=1, name="TestTeam", total_devs=1, busy_devs=0, 
                   tier_capacities={1: 8})
        }
        
        projects = {
            1: Project(id=1, name="TestProject", priority=1,
                      start_date=date(2025, 6, 25),
                      due_date_wo_qa=date(2025, 6, 25),
                      due_date_with_qa=date(2025, 6, 25))
        }
        
        # Múltiples asignaciones problemáticas
        assignments = [
            # Asignación con 0 horas
            Assignment(
                id=1, project_id=1, project_name="TestProject", project_priority=1,
                team_id=1, team_name="TestTeam", tier=1, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=0,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            # Asignación con muchas horas
            Assignment(
                id=2, project_id=1, project_name="TestProject", project_priority=1,
                team_id=1, team_name="TestTeam", tier=1, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=50000,
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            ),
            # Asignación con fecha de inicio extrema
            Assignment(
                id=3, project_id=1, project_name="TestProject", project_priority=1,
                team_id=1, team_name="TestTeam", tier=1, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=100,
                ready_to_start_date=date(2099, 12, 31),  # Fecha muy futura
                assignment_start_date=date(2099, 12, 31)
            )
        ]
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación - debe completarse sin errores
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Verificar que todas las fechas están en rango válido
        for assignment in result.assignments:
            if assignment.calculated_start_date:
                assert MIN_DATE <= assignment.calculated_start_date <= MAX_DATE
            if assignment.calculated_end_date:
                assert MIN_DATE <= assignment.calculated_end_date <= MAX_DATE
        
        print(f"✅ Scheduler maneja datos problemáticos sin fallar")
        print(f"  Procesadas {len(assignments)} asignaciones problemáticas")
        print(f"  Todas las fechas están en rango válido")
    
    def test_original_error_scenario(self):
        """Test que reproduce el escenario específico del error original"""
        
        # Simular el escenario que causaba year 10000 is out of range
        teams = {
            1: Team(id=1, name="TestTeam", total_devs=1, busy_devs=1,  # Team ocupado
                   tier_capacities={1: 8})
        }
        
        projects = {
            1: Project(id=1, name="TestProject", priority=1,
                      start_date=date(2025, 6, 25),
                      due_date_wo_qa=date(2025, 6, 25),
                      due_date_with_qa=date(2025, 6, 25))
        }
        
        # Asignación que requiere buscar muy lejos en el futuro
        assignments = [
            Assignment(
                id=1, project_id=1, project_name="TestProject", project_priority=1,
                team_id=1, team_name="TestTeam", tier=1, devs_assigned=1.0, max_devs=1.0,
                estimated_hours=8000,  # Muchas horas
                ready_to_start_date=date(2025, 6, 25),
                assignment_start_date=date(2025, 6, 25)
            )
        ]
        
        simulation_input = SimulationInput(
            teams=teams, projects=projects, assignments=assignments,
            simulation_start_date=date(2025, 6, 26)
        )
        
        # Ejecutar simulación - antes fallaba con year 10000 error
        scheduler = ProjectScheduler()
        result = scheduler.simulate(simulation_input)
        
        # Verificar que se completó sin error
        assert len(result.assignments) == 1
        assignment = result.assignments[0]
        
        # Las fechas deben estar en rango válido
        if assignment.calculated_start_date:
            assert MIN_DATE <= assignment.calculated_start_date <= MAX_DATE
        if assignment.calculated_end_date:
            assert MIN_DATE <= assignment.calculated_end_date <= MAX_DATE
        
        print(f"✅ Escenario original del error resuelto")
        print(f"  Start: {assignment.calculated_start_date}")
        print(f"  End: {assignment.calculated_end_date}")


if __name__ == "__main__":
    test = TestDateRangeBugFix()
    test.test_validate_date_range_function()
    test.test_extreme_date_scenario()
    test.test_monitoring_module_safety()
    test.test_scheduler_robustness_with_bad_data()
    test.test_original_error_scenario()
    print("\n🎉 Todos los tests de corrección del bug pasaron exitosamente!")