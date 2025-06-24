# 🔬 Demo de Simulación APE - Instrucciones

## Cómo Ejecutar la Demo

### Opción 1: Lanzador Automático
```bash
cd /home/a/development/migrated/marblefaraway/app
python run_simulation_demo.py
```

### Opción 2: Streamlit Directo
```bash
cd /home/a/development/migrated/marblefaraway/app
streamlit run modules/simulation/streamlit_demo.py --server.port 8501
```

### Opción 3: Demo en Terminal (sin UI)
```bash
cd /home/a/development/migrated/marblefaraway/app
python -m modules.simulation.demo
```

## ¿Qué Verás en la Demo?

### 📊 Panel Principal
- **Configuración de Equipos**: Sliders para ajustar capacidad y devs ocupados
- **Prioridades de Proyectos**: Selectores para cambiar orden de ejecución
- **Fecha de Simulación**: Date picker para cambiar punto de inicio

### 📋 Datos de Entrada
- **Tabla de Equipos**: Capacidad total, devs ocupados, disponibles
- **Tabla de Asignaciones**: Proyectos, fases, prioridades, horas necesarias

### 🎯 Resultados de Simulación
- **Cronograma Detallado**: Fechas de inicio/fin de cada asignación
- **Diagrama de Gantt**: Visualización temporal de proyectos
- **Resumen por Proyecto**: Estado y duración total
- **Métricas**: Estadísticas de utilización

### 🔍 Under the Hood
- **Proceso Paso a Paso**: Cómo se procesa cada asignación
- **Estructuras Internas**: 
  - `active_by_team`: Qué asignaciones están activas por equipo
  - `project_next_free`: Cuándo puede continuar cada proyecto
- **Timeline de Ocupación**: Gráfico de utilización de equipos en el tiempo

## Datos de Prueba Incluidos

### Proyectos
- **Alpha** (Prioridad 1): Arch → Model → Devs → Dqa
- **Beta** (Prioridad 2): Arch → Model → Devs → Dqa  
- **Gamma** (Prioridad 3): Arch → Model → Devs (sin Dqa)

### Equipos
- **Arch**: 2 devs totales, 0 ocupados
- **Model**: 4 devs totales, 0 ocupados
- **Devs**: 6 devs totales, 1 ocupado
- **Dqa**: 3 devs totales, 0 ocupados

## Casos What-If para Probar

### 1. Cambiar Prioridades
- Pon Beta en prioridad 1 → ¿Cómo cambia el cronograma?
- Pon Gamma en prioridad 1 → ¿Qué impacto tiene?

### 2. Ajustar Capacidad
- Reduce Arch a 1 dev → ¿Se crea cuello de botella?
- Aumenta Devs a 8 devs → ¿Mejora el tiempo total?
- Pon 2 devs ocupados en Model → ¿Cómo afecta?

### 3. Observar Paralelismo
- Nota cómo Alpha-Arch y Beta-Arch ejecutan en paralelo
- Ve cómo Alpha-Model espera a que termine Alpha-Arch

### 4. Analizar Utilización
- Observa el gráfico de utilización en el tiempo
- Identifica cuándo cada equipo está al 100%

## Funcionalidades Destacadas

### ✅ Simulación Realista
- Algoritmo idéntico al sistema APE real
- Manejo correcto de días hábiles
- Dependencias secuenciales entre fases

### ✅ Visualización Completa
- Datos de entrada y resultados
- Estructuras internas del algoritmo
- Gráficos interactivos con Plotly

### ✅ Análisis What-If
- Controles interactivos en sidebar
- Comparación inmediata de escenarios
- Sin persistencia (solo en memoria)

### ✅ Debugging Friendly
- Proceso paso a paso visible
- Estados internos expuestos
- Validación automática de resultados

## Troubleshooting

### Error de Importación
```bash
# Instalar dependencias
pip install -r requirements.txt
```

### Puerto Ocupado
```bash
# Usar puerto diferente
streamlit run modules/simulation/streamlit_demo.py --server.port 8502
```

### Error de Pandas/BusinessDay
```bash
# Verificar versión de pandas
python -c "import pandas; print(pandas.__version__)"
# Debe ser >= 2.3.0
```

La demo está lista para mostrar cómo funciona el algoritmo de scheduling "under the hood" y permite experimentar con diferentes escenarios what-if de forma interactiva.