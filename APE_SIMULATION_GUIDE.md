# 🔬 APE Simulation Guide - Guía Completa del Sistema de Simulación

## 📋 Resumen Ejecutivo

El sistema APE (Automatic Project Estimator) incluye un módulo de simulación completo que permite visualizar y analizar el algoritmo de scheduling "under the hood". Esta guía consolida toda la información sobre implementación, uso y funcionalidades del sistema.

## 🎯 Objetivos del Sistema

### Funcionalidades Principales
- **Simulación Realista**: Algoritmo idéntico al sistema APE real
- **Análisis What-If**: Experimentación con diferentes escenarios
- **Visualización Completa**: Gráficos interactivos y estructuras internas
- **Integración Nativa**: Pestaña integrada en la aplicación principal

### Casos de Uso
1. **Planificación**: ¿Qué pasa si tengo menos devs en Arch?
2. **Priorización**: ¿Cómo afecta cambiar orden de proyectos?
3. **Capacidad**: ¿Dónde están los cuellos de botella?
4. **Optimización**: ¿Cuál es la mejor distribución de recursos?

## 🏗️ Arquitectura del Sistema

### Estructura de Archivos
```
app/modules/simulation/
├── __init__.py              # Exports principales
├── models.py               # Estructuras de datos (Assignment, Team, ScheduleResult)
├── scheduler.py            # Algoritmo core de scheduling (205 líneas)
├── simulation.py           # Interfaz Streamlit integrada
├── demo.py                # Demo en terminal
└── README.md              # Documentación técnica
```

### Componentes Principales

#### 1. **Modelos de Datos** ([`models.py`](app/modules/simulation/models.py))
```python
@dataclass
class Assignment:
    project_id: int
    project_name: str
    phase: str
    phase_order: int
    team_id: int
    priority: int
    devs_assigned: float
    hours_needed: int
    ready_date: date
    start_date: Optional[date] = None
    end_date: Optional[date] = None

@dataclass
class Team:
    id: int
    name: str
    total_devs: int
    busy_devs: int = 0

@dataclass
class ScheduleResult:
    assignments: List[Assignment]
    project_summaries: List[Dict]
```

#### 2. **Algoritmo de Scheduling** ([`scheduler.py`](app/modules/simulation/scheduler.py))
- **Clase Principal**: [`ProjectScheduler`](app/modules/simulation/scheduler.py:14)
- **Método Core**: [`simulate()`](app/modules/simulation/scheduler.py:20)
- **Protección**: Límite de 2 años para evitar loops infinitos
- **Características**:
  - Gestión de dependencias secuenciales entre fases
  - Paralelización automática cuando hay capacidad
  - Cálculo correcto de días hábiles
  - Respeto de prioridades y capacidades

#### 3. **Interfaz de Usuario** ([`simulation.py`](app/modules/simulation/simulation.py))
- **Función Principal**: [`render_simulation()`](app/modules/simulation/simulation.py:10)
- **Integración**: Pestaña "Simulation" en [`app.py`](app/app.py:28)
- **Controles Interactivos**: Sidebar con configuración de equipos y prioridades

## 🔧 Correcciones y Mejoras Implementadas

### 1. **Bug Crítico Resuelto** ✅
**Problema**: Error "year 10000 is out of range" por loop infinito en [`_find_available_slot`](app/modules/simulation/scheduler.py:95)

**Solución**: Agregada protección contra loops infinitos
```python
max_iterations = 365 * 2  # Máximo 2 años en el futuro
iterations = 0

while not self._fits_in_period(...):
    iterations += 1
    if iterations > max_iterations:
        raise ValueError(f"No se pudo encontrar slot disponible...")
    candidate_start = self._next_business_day(candidate_start)
```

### 2. **Corrección de Cálculo de Fechas** ✅
**Problema**: Las tareas terminaban el mismo día que empezaban

**Solución**: Eliminada resta incorrecta en [`_calculate_end_date`](app/modules/simulation/scheduler.py:131)
```python
# ANTES (Incorrecto)
end_timestamp = pd.Timestamp(start_date) + BusinessDay(days_needed) - BusinessDay(1)

# DESPUÉS (Correcto)  
end_timestamp = pd.Timestamp(start_date) + BusinessDay(days_needed)
```

**Resultado**: Si una tarea empieza hoy y dura N días, termina N días hábiles después

### 3. **Integración Completa** ✅
- **Pestaña Nativa**: Integrada en aplicación principal APE
- **Sin Conflictos**: Coexiste con Teams, Projects, Monitoring
- **API Consistente**: Usa la misma estructura que el módulo original

## 🎮 Funcionalidades de la Interfaz

### ⚙️ Controles Interactivos (Sidebar)
- **📅 Fecha de inicio**: Date picker para simulación
- **👥 Capacidad de equipos**: Sliders para total y ocupados por equipo
- **🎯 Prioridades**: Selectores para orden de proyectos

### 📊 Visualización Principal
- **📋 Datos de entrada**: Tablas de equipos y asignaciones
- **🎯 Resultados**: Cronograma detallado con fechas y duración
- **📈 Métricas**: Duración total y número de asignaciones

### 📊 Gráficos Interactivos
- **📅 Gantt Chart**: Timeline visual de proyectos con Plotly
- **📈 Utilización**: Gráfico de barras de uso por equipo
- **🎨 Colores**: Alpha (rojo), Beta (turquesa), Gamma (azul)

### 🔍 Under the Hood
- **Proceso paso a paso**: Cómo se ejecuta el algoritmo
- **Estructuras internas**: `active_by_team` y `project_next_free`
- **Código de ejemplo**: Snippets explicativos

## 🧪 Datos de Prueba y Validación

### Proyectos de Ejemplo
- **Alpha** (Prioridad 1): Arch(16h) → Model(56h) → Devs(40h) → Dqa(24h)
- **Beta** (Prioridad 2): Arch(16h) → Model(56h) → Devs(40h) → Dqa(24h)
- **Gamma** (Prioridad 3): Arch(8h) → Model(28h) → Devs(20h)

### Equipos Configurables
- **Arch**: 2 devs totales, 0 ocupados (por defecto)
- **Model**: 4 devs totales, 0 ocupados (por defecto)
- **Devs**: 6 devs totales, 1 ocupado (por defecto)
- **Dqa**: 3 devs totales, 0 ocupados (por defecto)

### Casos de Validación ✅
- **Paralelismo**: Alpha-Arch y Beta-Arch ejecutan simultáneamente
- **Dependencias**: Alpha-Model espera a Alpha-Arch
- **Prioridades**: Orden correcto según prioridad de proyecto
- **Capacidad**: Respeta límites de devs por equipo
- **Duración**: Cálculo correcto de días hábiles

## 🚀 Cómo Usar el Sistema

### Acceso a la Simulación
1. **Ejecutar aplicación**: `docker compose up --build`
2. **Abrir navegador**: `http://localhost:8501`
3. **Hacer clic en pestaña**: **"Simulation"**

### Demo en Terminal (Alternativa)
```bash
cd /home/a/development/migrated/marblefaraway/app
python -m modules.simulation.demo
```

### Experimentación What-If
1. **Ajustar controles** en sidebar (equipos, prioridades)
2. **Observar cambios** en tiempo real en gráficos
3. **Analizar impacto** en cronograma y utilización

### Casos What-If Recomendados
- **Cambiar Prioridades**: ¿Qué pasa si Beta tiene prioridad 1?
- **Ajustar Capacidad**: ¿Cómo afecta reducir Arch a 1 dev?
- **Modificar Ocupación**: ¿Qué impacto tiene tener 2 devs ocupados en Model?
- **Observar Paralelismo**: Nota cómo Alpha-Arch y Beta-Arch ejecutan simultáneamente

## 🔍 Análisis del Algoritmo Paso a Paso

### Flujo de Procesamiento
1. **Ordenamiento**: Por prioridad y orden de fase
2. **Procesamiento secuencial**: Cada asignación una por una
3. **Cálculo de fechas**: Considerando dependencias y capacidad
4. **Actualización de estado**: Registro en estructuras internas

### Estructuras Internas Clave
```python
# active_by_team: Tracking de asignaciones activas por equipo
active_by_team = {
    "Arch": [("Alpha", "2025-06-16", "2025-06-17")],
    "Model": [("Alpha", "2025-06-18", "2025-06-24")],
    "Devs": [],
    "Dqa": []
}

# project_next_free: Cuándo puede continuar cada proyecto
project_next_free = {
    "Alpha": "2025-06-18",  # Después de Arch
    "Beta": "2025-06-18",   # Después de Arch
    "Gamma": "2025-06-16"   # Puede empezar inmediatamente
}
```

### Algoritmo de Búsqueda de Slot
```python
def _find_available_slot(self, team_id, devs_needed, days_needed, earliest_start, teams, active_by_team):
    candidate_start = earliest_start
    max_iterations = 365 * 2  # Protección contra loops infinitos
    iterations = 0
    
    while not self._fits_in_period(team_id, devs_needed, days_needed, candidate_start, teams, active_by_team):
        iterations += 1
        if iterations > max_iterations:
            raise ValueError("No se pudo encontrar slot disponible")
        candidate_start = self._next_business_day(candidate_start)
    
    return candidate_start
```

## 🎯 Plan de Mejoras Futuras

### Capacidades Avanzadas Propuestas
1. **Capacity Manager**: Gestión dinámica de recursos ocupados
2. **Enhanced Simulator**: Simulación con timeline de liberación
3. **Optimization Engine**: Sugerencias automáticas de mejoras
4. **Advanced What-If**: Comparación de múltiples escenarios

### Métricas de Éxito Objetivo
- **Precisión de Estimación**: ±5 días vs. baseline actual
- **Tiempo de Análisis**: <30 segundos para simular 20 proyectos
- **Scenarios Evaluados**: Capacidad de comparar 3+ escenarios simultáneamente
- **Optimización Automática**: Identificar 80% de cuellos de botella reales

## 🔧 Troubleshooting

### Errores Comunes
1. **Error de Importación**: `pip install -r requirements.txt`
2. **Puerto Ocupado**: `streamlit run ... --server.port 8502`
3. **Error de Pandas/BusinessDay**: Verificar pandas >= 2.3.0

### Validación de Funcionamiento
```bash
# Test básico
cd /home/a/development/migrated/marblefaraway/app
python -m modules.simulation.demo

# Verificar aplicación web
docker compose up --build
# Abrir http://localhost:8501 → pestaña "Simulation"
```

## 📊 Estado Actual del Proyecto

### ✅ Completado
- [x] Módulo de simulación implementado
- [x] Bug crítico del loop infinito resuelto
- [x] Corrección de cálculo de fechas
- [x] Integración en aplicación principal
- [x] Interfaz interactiva funcional
- [x] Validación con casos de prueba
- [x] Documentación consolidada

### 🧹 Limpieza Realizada
- [x] Eliminado `streamlit_demo.py` (duplicado)
- [x] Eliminado `integration.py` (no usado)
- [x] Eliminado `test_scheduler.py` (no usado)
- [x] Eliminado `DEMO_INSTRUCTIONS.md` (obsoleto)
- [x] Consolidado documentación en este archivo

### 🎉 Resultado Final

**El sistema de simulación APE está completamente funcional y limpio**. Los usuarios pueden:

1. **Navegar** entre pestañas sin cambiar de aplicación
2. **Experimentar** con escenarios what-if en tiempo real
3. **Visualizar** el funcionamiento interno del algoritmo
4. **Entender** cómo se calculan los cronogramas
5. **Analizar** cuellos de botella y optimizaciones

El proyecto mantiene toda la funcionalidad del módulo original mientras proporciona una experiencia de usuario unificada dentro de la aplicación APE existente, sin errores críticos y con documentación consolidada.