# Sistema de Planes Persistentes - APE

## Descripción General

El sistema de planes persistentes permite guardar, comparar y gestionar resultados de simulaciones de cronogramas como "planes" que se almacenan en la base de datos. Esto facilita:

- **Persistencia**: Guardar resultados de simulaciones para referencia futura
- **Comparación**: Detectar automáticamente cambios entre simulaciones
- **Versionado**: Mantener historial de diferentes versiones de cronogramas
- **Activación**: Marcar un plan específico como "activo" para referencia

## Componentes Implementados

### 1. Migración SQL (`migrate_add_plans.sql`)

Crea las siguientes estructuras:

- **Tabla `plans`**: Almacena metadatos de cada plan
  - `checksum`: Hash SHA-256 para detectar cambios
  - `is_active`: Solo un plan puede estar activo a la vez
  - Estadísticas: total de asignaciones y proyectos

- **Tabla `plan_assignments`**: Snapshot de asignaciones calculadas
  - Fechas de inicio y fin calculadas
  - Información completa del proyecto y equipo
  - Horas estimadas y pendientes

- **Vista `plan_summary`**: Estadísticas agregadas de planes

### 2. Modelos Python (`app/modules/common/models.py`)

#### Clase `Plan`
```python
@dataclass
class Plan:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    checksum: str = ""
    is_active: bool = False
    simulation_date: date = None
    total_assignments: int = 0
    total_projects: int = 0
    assignments: List['PlanAssignment'] = field(default_factory=list)
```

**Métodos principales:**
- `calculate_checksum(assignments)`: Genera hash SHA-256 del contenido
- `from_schedule_result(result, name, description)`: Crea plan desde simulación

#### Clase `PlanAssignment`
```python
@dataclass
class PlanAssignment:
    # Snapshot completo de una asignación calculada
    plan_id: int = 0
    assignment_id: int = 0
    calculated_start_date: date = None
    calculated_end_date: date = None
    # ... otros campos
```

### 3. CRUD Operations (`app/modules/common/plans_crud.py`)

#### Funciones principales:

```python
# Guardar resultado como plan
def save_plan(result: ScheduleResult, name: str = "", 
              description: str = "", set_as_active: bool = True) -> Plan

# Obtener plan activo
def get_active_plan() -> Optional[Plan]

# Comparar con plan activo
def compare_plans(result: ScheduleResult, 
                  active_plan: Optional[Plan] = None) -> Dict[str, Any]

# Activar un plan específico
def set_active_plan(plan_id: int) -> bool

# Listar todos los planes
def list_plans(limit: int = 50) -> List[Plan]

# Eliminar plan
def delete_plan(plan_id: int) -> bool
```

### 4. Integración con Scheduler (`app/modules/simulation/scheduler.py`)

El `ProjectScheduler` ahora incluye:

```python
# Generar checksum automáticamente
result.checksum = self._generate_checksum(result)

# Detectar cambios vs plan activo
result.has_changes = self._detect_changes(result)

# Métodos de conveniencia
def convert_to_plan(self, result: ScheduleResult, name: str = "") -> Plan
def save_as_plan(self, result: ScheduleResult, name: str = "") -> Plan
```

## Uso del Sistema

### 1. Ejecutar Simulación y Guardar Plan

```python
from app.modules.simulation.scheduler import ProjectScheduler
from app.modules.common.plans_crud import save_plan

# Ejecutar simulación
scheduler = ProjectScheduler()
result = scheduler.simulate(simulation_input)

# Guardar como plan activo
plan = save_plan(
    result, 
    name="Cronograma Q1 2025",
    description="Plan inicial para primer trimestre",
    set_as_active=True
)

print(f"Plan guardado: {plan.id}")
print(f"Checksum: {plan.checksum[:16]}...")
```

### 2. Detectar Cambios Automáticamente

```python
# El scheduler detecta cambios automáticamente
result = scheduler.simulate(simulation_input)

if result.has_changes:
    print("⚠️ Se detectaron cambios en el cronograma")
    print(f"Nuevo checksum: {result.checksum[:16]}...")
else:
    print("✅ Sin cambios detectados")
```

### 3. Comparación Detallada

```python
from app.modules.common.plans_crud import compare_plans

# Comparar resultado con plan activo
comparison = compare_plans(result)

print(f"Tiene cambios: {comparison['has_changes']}")
print(f"Cambios detectados: {comparison['changes_detected']}")
```

### 4. Gestión de Planes

```python
from app.modules.common.plans_crud import list_plans, set_active_plan

# Listar planes existentes
planes = list_plans(10)
for plan in planes:
    status = "🟢 ACTIVO" if plan.is_active else "⚪ Inactivo"
    print(f"{plan.name} ({status}) - {plan.created_at}")

# Activar plan específico
set_active_plan(plan_id=5)
```

## Algoritmo de Checksum

El sistema usa SHA-256 para generar checksums consistentes:

1. **Ordenamiento**: Las asignaciones se ordenan por ID para consistencia
2. **Campos clave**: Se incluyen campos que afectan el cronograma:
   - `assignment_id`, `project_id`, `team_id`
   - `calculated_start_date`, `calculated_end_date`
   - `pending_hours`, `devs_assigned`
3. **Serialización**: JSON ordenado para hash reproducible
4. **Hash**: SHA-256 del JSON resultante

## Casos de Uso

### 1. Versionado de Cronogramas
```python
# Guardar versión inicial
plan_v1 = save_plan(result, "Cronograma v1.0", set_as_active=True)

# Después de cambios, guardar nueva versión
plan_v2 = save_plan(new_result, "Cronograma v1.1", set_as_active=True)

# Comparar versiones por checksum
if plan_v1.checksum != plan_v2.checksum:
    print("Cronograma actualizado")
```

### 2. Detección Automática de Cambios
```python
# En proceso de simulación regular
result = scheduler.simulate(input_data)

if result.has_changes:
    # Notificar a stakeholders
    send_notification("Cronograma actualizado")
    
    # Guardar nueva versión
    save_plan(result, f"Actualización {datetime.now()}")
```

### 3. Rollback a Plan Anterior
```python
# Listar planes disponibles
planes = list_plans()

# Activar plan anterior
previous_plan = planes[1]  # Segundo más reciente
set_active_plan(previous_plan.id)
```

## Pruebas

Ejecutar el script de pruebas:

```bash
python test_plans_system.py
```

Este script verifica:
- ✅ Creación de planes desde simulaciones
- ✅ Guardado y recuperación de base de datos
- ✅ Detección de cambios por checksum
- ✅ Comparación entre planes

## Consideraciones Técnicas

### Performance
- Los checksums se calculan solo cuando es necesario
- Las consultas usan índices optimizados
- La vista `plan_summary` pre-calcula estadísticas

### Consistencia
- Constraint único para plan activo
- Transacciones para operaciones atómicas
- Validación de fechas y datos

### Escalabilidad
- Paginación en listado de planes
- Eliminación en cascada de asignaciones
- Índices para consultas frecuentes

## Próximos Pasos

1. **Interfaz Web**: Crear UI para gestionar planes
2. **Notificaciones**: Sistema de alertas por cambios
3. **Exportación**: Generar reportes de planes
4. **API REST**: Endpoints para integración externa
5. **Métricas**: Dashboard de estadísticas de planes