# 🧪 Tests del Sistema APE Unificado

Este directorio contiene la suite completa de tests para el sistema APE (Automatic Project Estimator), implementando una estrategia pragmática de testing con cobertura completa de casos críticos.

## 📁 Estructura de Tests

```
tests/
├── conftest.py                    # Configuración pytest + fixtures
├── requirements.txt               # Dependencias de testing
├── unit/                         # Tests de modelos y lógica pura
│   ├── test_models.py            # Tests para Team, Project, Assignment
│   └── test_business_logic.py    # Métodos de negocio sin dependencias
├── integration/                  # Tests de CRUDs con mocks
│   ├── test_cruds.py            # Teams, Projects, Assignments CRUDs
│   └── test_data_flows.py       # Flujos completos de datos
└── simulation/                   # Tests críticos de simulación
    ├── test_simulation_scenarios.py  # Casos críticos principales
    ├── test_edge_cases.py            # Casos límite y errores
    └── test_priority_handling.py     # Manejo de prioridades
```

## 🎯 Casos Críticos Cubiertos

### **Unit Tests**
- ✅ `Team.get_available_devs()` - Cálculo de capacidad disponible
- ✅ `Assignment.get_hours_needed()` - Cálculo de horas por tier
- ✅ `Assignment.can_start_on()` - Validación de fechas
- ✅ `ScheduleResult` - Métodos de consulta y filtrado

### **Integration Tests**
- ✅ CRUDs con mocks de DB (teams, projects, assignments)
- ✅ Operaciones de lectura con JOINs
- ✅ Manejo de errores en operaciones de DB

### **Simulation Tests**
- ✅ **Proyecto simple**: 4 fases secuenciales (Arch → Model → Devs → Dqa)
- ✅ **Múltiples proyectos**: Verificación de prioridades
- ✅ **Capacidad limitada**: Sin paralelismo cuando no hay recursos
- ✅ **Dependencias**: Restricciones de ready_to_start_date
- ✅ **Flujo APE completo**: Secuencia real con cálculos precisos
- ✅ **Casos límite**: Equipos sin capacidad, loops infinitos, datos inválidos

## 🚀 Ejecutar Tests

### **Instalación de Dependencias**
```bash
pip install -r tests/requirements.txt
```

### **Ejecutar Todos los Tests**
```bash
python run_tests.py
```

### **Ejecutar por Categoría**
```bash
# Unit tests solamente
python run_tests.py --unit

# Integration tests solamente
python run_tests.py --integration

# Simulation tests solamente
python run_tests.py --simulation

# Tests con cobertura
python run_tests.py --coverage
```

### **Comandos Pytest Directos**
```bash
# Todos los tests con verbose
pytest tests/ -v

# Tests específicos
pytest tests/simulation/test_simulation_scenarios.py::TestSimulationScenarios::test_simple_project_sequential_phases -v

# Con cobertura
pytest tests/ --cov=app/modules --cov-report=html --cov-report=term-missing

# Solo tests rápidos
pytest tests/ -m "not slow"
```

## 📊 Métricas de Cobertura

### **Objetivos de Cobertura**
- **Unit Tests**: 90%+ en modelos y lógica de negocio
- **Integration Tests**: 80%+ en CRUDs
- **Simulation Tests**: 100% en casos críticos

### **Generar Reporte de Cobertura**
```bash
pytest tests/ --cov=app/modules --cov-report=html
# Abre htmlcov/index.html en el navegador
```

## 🧪 Fixtures Disponibles

### **Fixtures Básicas**
- `sample_team` - Team de ejemplo con tier_capacities
- `sample_project` - Project de ejemplo con fechas
- `sample_assignment` - Assignment de ejemplo completo
- `mock_connection` - Mock de conexión a DB

### **Fixtures APE**
- `ape_teams` - Equipos especializados (Arch, Model, Devs, Dqa)
- `sample_simulation_input` - Input completo para simulación

### **Usar Fixtures en Tests**
```python
def test_my_function(sample_team, sample_assignment):
    # Usar fixtures directamente
    result = my_function(sample_team, sample_assignment)
    assert result is not None
```

## 🔧 Configuración de Tests

### **pytest.ini**
```ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests for models and business logic
    integration: Integration tests for CRUDs
    simulation: Simulation tests for critical scenarios
```

### **Markers Disponibles**
```bash
# Ejecutar solo unit tests
pytest -m unit

# Ejecutar solo simulation tests
pytest -m simulation

# Excluir tests lentos
pytest -m "not slow"
```

## 🐛 Debugging Tests

### **Ejecutar Test Individual con Debug**
```bash
pytest tests/simulation/test_simulation_scenarios.py::TestSimulationScenarios::test_simple_project_sequential_phases -v -s --tb=long
```

### **Usar pdb para Debug**
```python
def test_debug_example():
    import pdb; pdb.set_trace()
    # Tu código de test aquí
```

### **Ver Output Completo**
```bash
pytest tests/ -v -s --tb=short
```

## 📈 Casos de Test Críticos

### **1. Dependencias Secuenciales APE**
```python
def test_arch_model_devs_dqa_sequence():
    """Verifica que Arch → Model → Devs → Dqa se ejecutan en orden"""
```

### **2. Manejo de Prioridades**
```python
def test_multiple_projects_priority_handling():
    """Verifica que prioridad 1 se ejecuta antes que prioridad 2"""
```

### **3. Capacidad Limitada**
```python
def test_limited_capacity_no_parallelism():
    """Verifica que no hay paralelismo cuando no hay recursos"""
```

### **4. Restricciones de Fecha**
```python
def test_ready_to_start_date_constraint():
    """Verifica que se respetan las fechas mínimas de inicio"""
```

## 🚨 Casos Límite Cubiertos

- ✅ Equipos sin capacidad disponible
- ✅ Protección contra loops infinitos
- ✅ Listas vacías de asignaciones
- ✅ Equipos inexistentes
- ✅ Asignaciones con 0 horas
- ✅ Devs fraccionarios (ej: 1.5 devs)
- ✅ Fechas muy antiguas o futuras
- ✅ Tiers inexistentes en capacidades

## 📝 Agregar Nuevos Tests

### **1. Unit Test**
```python
# tests/unit/test_models.py
def test_new_functionality(sample_team):
    """Test nueva funcionalidad"""
    result = sample_team.new_method()
    assert result == expected_value
```

### **2. Integration Test**
```python
# tests/integration/test_cruds.py
def test_new_crud_operation(mock_connection, mocker):
    """Test nueva operación CRUD"""
    # Setup mocks
    # Ejecutar operación
    # Verificar resultados
```

### **3. Simulation Test**
```python
# tests/simulation/test_simulation_scenarios.py
def test_new_scenario():
    """Test nuevo escenario de simulación"""
    # Setup teams, projects, assignments
    # Ejecutar simulación
    # Verificar resultados críticos
```

## 🎯 Criterios de Aceptación

Para que un test sea considerado exitoso debe:

1. **Pasar consistentemente** en múltiples ejecuciones
2. **Ser independiente** de otros tests
3. **Tener assertions claras** y específicas
4. **Cubrir casos edge** relevantes
5. **Usar fixtures apropiadas** para setup
6. **Tener nombres descriptivos** que expliquen qué testea

## 🔄 CI/CD Integration

Los tests están configurados para ejecutarse automáticamente en CI/CD:

```yaml
# .github/workflows/tests.yml
- name: Run Unit Tests
  run: pytest tests/unit/ -v

- name: Run Integration Tests  
  run: pytest tests/integration/ -v

- name: Run Simulation Tests
  run: pytest tests/simulation/ -v

- name: Generate Coverage
  run: pytest tests/ --cov=app/modules --cov-report=xml
```

## 📞 Soporte

Si tienes problemas con los tests:

1. **Verifica dependencias**: `pip install -r tests/requirements.txt`
2. **Ejecuta tests individuales** para aislar problemas
3. **Revisa fixtures** en `conftest.py`
4. **Consulta la estrategia completa** en `ESTRATEGIA_TESTING_APE.md`