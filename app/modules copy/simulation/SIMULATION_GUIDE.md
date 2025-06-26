# Guía del Módulo de Simulación APE

## Descripción General

El módulo de simulación APE permite visualizar y analizar el comportamiento del algoritmo de scheduling de proyectos. Está diseñado para reflejar la estructura real de la aplicación APE y proporciona una interfaz visual para crear casos de prueba y ejecutar simulaciones.

## Estructura del Módulo

```
app/modules/simulation/
├── __init__.py              # API pública del módulo
├── models.py               # Modelos de datos (Team, Project, Assignment, etc.)
├── scheduler.py            # Lógica principal del algoritmo de scheduling
├── simulation.py           # Interfaz principal de Streamlit
├── test_case_builder.py    # Constructor visual de casos de prueba
└── SIMULATION_GUIDE.md     # Esta documentación
```

## Guía de Uso

### 1. Acceso al Simulador

El simulador está disponible en la aplicación APE bajo la sección "🔬 Simulador de Scheduling APE".

### 2. Configuración de Equipos

Los equipos por defecto reflejan la estructura real de APE:

- **Arch** (ID: 1): 2 desarrolladores totales
- **Model** (ID: 2): 4 desarrolladores totales  
- **Devs** (ID: 3): 6 desarrolladores totales
- **Dqa** (ID: 4): 3 desarrolladores totales

Puedes ajustar:
- Total de desarrolladores por equipo
- Desarrolladores ocupados (no disponibles)

### 3. Creación de Proyectos

#### Plantillas Predefinidas

El sistema incluye escenarios predefinidos:

- **🚀 Escenario Básico**: 3 proyectos con diferentes prioridades
- **⚡ Alta Presión**: Múltiples proyectos urgentes con recursos limitados
- **🔄 Proyectos Escalonados**: Proyectos que inician en diferentes fechas
- **🎯 Solo Backend**: Proyectos que no requieren frontend

#### Constructor Manual

Permite crear proyectos personalizados configurando:

- **Información básica**: Nombre, prioridad (1-3), fecha de inicio
- **Tamaño del proyecto**: Pequeño, Mediano, Grande, Crítico
- **Fases**: Completo (4 fases), Sin DQA, Solo Backend, Solo Frontend
- **Tiers por fase**: Configuración individual del tier para cada fase

### 4. Configuración de Tiers por Fase

Cada fase tiene configuraciones específicas:

| Fase  | Tier por Defecto | Devs Asignados | Descripción |
|-------|------------------|----------------|-------------|
| Arch  | 1                | 1.0            | Arquitectura - siempre Tier 1 |
| Model | 2                | 1.0            | Modelado - típicamente Tier 2 |
| Devs  | 3                | 1.0            | Desarrollo - siempre Tier 3 |
| Dqa   | 2                | 1.0            | QA - máximo Tier 3 |

### 5. Ejecución de Simulación

El sistema:
1. Valida la configuración del caso de prueba
2. Genera automáticamente los assignments siguiendo el patrón APE
3. Ejecuta el algoritmo de scheduling
4. Muestra resultados en formato tabla y gráfico Gantt

## Ejemplos de Casos de Prueba

### Caso Básico: Proyecto Simple

```
Proyecto: MiApp
- Prioridad: 1
- Tamaño: Mediano
- Fases: Arch (Tier 1) → Model (Tier 2) → Devs (Tier 3) → Dqa (Tier 2)
- Fecha inicio: Hoy
```

### Caso Complejo: Múltiples Proyectos

```
Proyecto A (Prioridad 1, Grande):
- Arch: Tier 1, 16h
- Model: Tier 4, 112h  
- Devs: Tier 3, 80h
- Dqa: Tier 3, 48h

Proyecto B (Prioridad 2, Mediano):
- Arch: Tier 1, 16h
- Model: Tier 2, 56h
- Devs: Tier 3, 40h
- Dqa: Tier 2, 24h
```

## API Reference

### Modelos Principales

#### `Team`
```python
@dataclass
class Team:
    id: int
    name: str
    total_devs: int
    busy_devs: int = 0
    tier_capacities: Dict[int, int] = None
    
    def get_available_devs(self) -> int
    def get_hours_per_person_for_tier(self, tier: int) -> int
```

#### `Project`
```python
@dataclass
class Project:
    id: int
    name: str
    priority: int
    start_date: date
    due_date_wo_qa: date
    due_date_with_qa: date
    phase: str = ""
```

#### `Assignment`
```python
@dataclass
class Assignment:
    id: int
    project_id: int
    project_name: str
    project_priority: int
    team_id: int
    team_name: str
    tier: int
    devs_assigned: float
    max_devs: float
    estimated_hours: int
    ready_to_start_date: date
    assignment_start_date: date
    status: str = "Not Started"
    
    # Calculados por la simulación
    calculated_start_date: Optional[date] = None
    calculated_end_date: Optional[date] = None
    pending_hours: int = 0
    paused_on: Optional[date] = None
```

### Funciones Principales

#### `render_simulation()`
Función principal que renderiza la interfaz de simulación.

#### `TestCaseBuilder`
Clase principal para construir casos de prueba:

- `render_team_configuration()`: Configura equipos
- `render_project_builder()`: Constructor de proyectos
- `create_assignments_from_projects()`: Genera assignments automáticamente
- `validate_test_case()`: Valida configuración antes de simular

## Flujo de Ejecución

1. **Inicialización**: Se cargan las configuraciones por defecto
2. **Configuración de Equipos**: El usuario ajusta capacidades
3. **Definición de Proyectos**: Se crean proyectos usando plantillas o constructor
4. **Generación de Assignments**: Se generan automáticamente siguiendo patrones APE
5. **Validación**: Se verifica la consistencia del caso de prueba
6. **Simulación**: Se ejecuta el algoritmo de scheduling
7. **Visualización**: Se muestran resultados en tabla y gráfico Gantt

## Patrones de Generación Automática

El sistema genera assignments automáticamente siguiendo estos patrones:

- **Arch**: Siempre Tier 1, 1 desarrollador asignado
- **Model**: Tier variable (1-4), 1 desarrollador asignado
- **Devs**: Siempre Tier 3, 1 desarrollador asignado  
- **Dqa**: Tier variable (1-3), 1 desarrollador asignado

Los esfuerzos se calculan según presets:

| Tamaño   | Arch | Model | Devs | Dqa |
|----------|------|-------|------|-----|
| Pequeño  | 8h   | 28h   | 20h  | 12h |
| Mediano  | 16h  | 56h   | 40h  | 24h |
| Grande   | 32h  | 112h  | 80h  | 48h |
| Crítico  | 48h  | 168h  | 120h | 72h |

## Validaciones

El sistema valida automáticamente:

- ✅ Existencia de al menos un proyecto
- ✅ Nombres únicos de proyectos
- ✅ Disponibilidad de desarrolladores en equipos
- ✅ Fechas de inicio válidas
- ✅ Configuración correcta de tiers (DQA máximo Tier 3)

## Consejos de Uso

1. **Comienza con plantillas**: Usa los escenarios predefinidos para familiarizarte
2. **Ajusta gradualmente**: Modifica un parámetro a la vez para entender el impacto
3. **Valida siempre**: Revisa los errores de validación antes de simular
4. **Analiza resultados**: Usa el gráfico Gantt para visualizar dependencias y paralelismo
5. **Experimenta con tiers**: Cambia los tiers por fase para ver el impacto en duración

## Limitaciones Conocidas

- Los assignments se generan automáticamente (no edición manual)
- Máximo Tier 3 para fase DQA
- Fechas de inicio no pueden ser en el pasado
- Un desarrollador por assignment (no fraccionamiento)

## Soporte

Para reportar problemas o sugerir mejoras, contacta al equipo de desarrollo APE.