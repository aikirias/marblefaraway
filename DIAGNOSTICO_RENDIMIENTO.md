# 🐛 Diagnóstico de Rendimiento APE

## 📋 Resumen del Problema

La aplicación APE está funcionando muy lenta o se cuelga después de implementar las mejoras del cronograma de Gantt. Se han identificado las posibles causas y se han agregado logs de diagnóstico para validar las hipótesis.

## 🔍 Posibles Causas Identificadas

### 🎯 **Causas Más Probables (1-2)**

1. **Bucle infinito/excesivo en scheduling** 
   - El algoritmo `_find_available_slot()` puede iterar hasta 730 veces (365*2 días)
   - Puede ocurrir cuando no hay capacidad suficiente en los equipos
   - **Ubicación**: `app/modules/simulation/scheduler.py:135-156`

2. **Re-renderizado excesivo de Streamlit**
   - El `auto_run` combinado con `session_state` puede causar ejecuciones múltiples
   - Cada cambio de prioridad puede disparar una nueva simulación
   - **Ubicación**: `app/modules/simulation/simulation.py:77-85`

### 📊 **Otras Causas Posibles (3-7)**

3. **Procesamiento ineficiente en vista consolidada**
   - `create_consolidated_gantt()` crea múltiples trazas de Plotly (una por fase)
   - **Ubicación**: `app/modules/simulation/gantt_config.py:161-275`

4. **Escritura de archivos JSON innecesaria**
   - Se escriben `simulation_input.json` y `simulation_output.json` en cada simulación
   - **Ubicación**: `app/modules/simulation/scheduler.py:47-49, 81-83`

5. **Validación de secuencia de fases repetitiva**
   - `validate_phase_sequence()` se ejecuta para cada proyecto
   - **Ubicación**: `app/modules/simulation/gantt_views.py:137-138`

6. **Cálculos de fechas complejos**
   - Múltiples operaciones con `BusinessDay` y `pd.Timestamp`
   - **Ubicación**: `app/modules/simulation/scheduler.py:190-211`

7. **Hover personalizado complejo**
   - Generación de texto de hover para cada fase en vista consolidada
   - **Ubicación**: `app/modules/simulation/gantt_config.py:197-207`

## 🔧 Logs de Diagnóstico Implementados

### 📍 **Logs en Scheduler** (`scheduler.py`)
```python
# Detecta bucles infinitos o excesivos
🔍 [SCHEDULER] Buscando slot para team_id=X, devs_needed=Y, days_needed=Z
⚠️ [SCHEDULER] 50 iteraciones buscando slot para team_id=X
✅ [SCHEDULER] Slot encontrado para team_id=X en N iteraciones
❌ [SCHEDULER] ERROR: Máximo de iteraciones alcanzado
```

### 🎨 **Logs en Streamlit** (`simulation.py`)
```python
# Detecta re-renderizado excesivo
🎨 [STREAMLIT] render_simulation() iniciado
🚀 [STREAMLIT] Iniciando simulación con N cambios de prioridad
📊 [STREAMLIT] Datos cargados: X proyectos, Y equipos, Z asignaciones
```

### 📊 **Logs en Gantt** (`gantt_config.py`)
```python
# Detecta problemas en generación de gráficos
📊 [GANTT] Creando vista consolidada con N proyectos
🔄 [GANTT] Procesando proyecto X con Y fases
✅ [GANTT] Vista consolidada creada con N trazas totales
```

## 🚀 Cómo Ejecutar el Diagnóstico

### **Opción 1: Script Automático**
```bash
./debug_performance.py
```

### **Opción 2: Manual**
```bash
cd app
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 📊 Señales de Problemas a Observar

### ⚠️ **Bucle Infinito en Scheduler**
- Logs con `⚠️ [SCHEDULER] 50+ iteraciones`
- Logs con `❌ [SCHEDULER] ERROR: Máximo de iteraciones`
- La aplicación se cuelga durante "Ejecutando simulación..."

### 🔄 **Re-renderizado Excesivo**
- Múltiples logs `🎨 [STREAMLIT] render_simulation() iniciado`
- Múltiples logs `🚀 [STREAMLIT] Iniciando simulación`
- La aplicación se vuelve lenta al cambiar prioridades

### 📈 **Problemas en Gantt Consolidado**
- Logs con `✅ [GANTT] Vista consolidada creada con 100+ trazas`
- La aplicación se cuelga al cambiar a vista consolidada
- Renderizado lento del gráfico Gantt

## 🎯 Próximos Pasos

1. **Ejecutar diagnóstico** usando el script `debug_performance.py`
2. **Reproducir el problema** en la pestaña Simulation
3. **Analizar logs** para identificar la causa específica
4. **Confirmar diagnóstico** con el usuario
5. **Implementar solución** basada en los hallazgos

## 📝 Notas Importantes

- Los logs aparecen en la consola donde se ejecuta Streamlit
- El diagnóstico no afecta la funcionalidad de la aplicación
- Los logs se pueden remover después del diagnóstico
- Se recomienda probar con datos reales para reproducir el problema

---

**Fecha**: 2025-01-26  
**Estado**: Logs implementados, listo para diagnóstico  
**Siguiente**: Ejecutar diagnóstico y confirmar causa raíz