# Análisis del Test Case de Scheduling - APE

## Descripción del Test Case

Este test case demuestra el algoritmo de scheduling con un ejemplo simple pero completo que incluye:
- 2 proyectos (Alpha y Beta)
- 2 equipos (Arch y Model)
- Dependencias secuenciales entre fases
- Gestión de capacidad de equipos

## Datos de Entrada

### Assignments (Asignaciones)
```python
assignments = [
    # Proyecto Alpha - Prioridad 1
    {'project_id': 1, 'project_name':'Alpha', 'priority':1, 'phase':'Arch', 'phase_order':0,
     'team_id':2, 'devs_assigned':1, 'hours_needed':16, 'ready_date':date(2025,6,16)},
    {'project_id': 1, 'project_name':'Alpha', 'priority':1, 'phase':'Model', 'phase_order':1,
     'team_id':3, 'devs_assigned':1, 'hours_needed':40, 'ready_date':date(2025,6,16)},
    
    # Proyecto Beta - Prioridad 2
    {'project_id': 2, 'project_name':'Beta', 'priority':2, 'phase':'Arch', 'phase_order':0,
     'team_id':2, 'devs_assigned':1, 'hours_needed':16, 'ready_date':date(2025,6,16)},
]
```

### Teams (Equipos)
```python
teams = {
    2: {'total_devs':2, 'busy_devs':0},  # Equipo Arch: 2 desarrolladores disponibles
    3: {'total_devs':4, 'busy_devs':0},  # Equipo Model: 4 desarrolladores disponibles
}
```

### Configuración
- **Fecha de inicio**: 2025-06-16 (lunes)
- **Orden de fases**: ["Arch", "Model", "Dev", "Dqa"]
- **Horas por día**: 8 horas por desarrollador

## Paso a Paso del Algoritmo

### Paso 1: Ordenamiento de Asignaciones

El DataFrame se ordena por `priority` y `phase_order`:

| Orden | Project | Phase | Priority | Phase_Order | Team_ID | Devs | Hours |
|-------|---------|-------|----------|-------------|---------|------|-------|
| 1     | Alpha   | Arch  | 1        | 0           | 2       | 1    | 16    |
| 2     | Alpha   | Model | 1        | 1           | 3       | 1    | 40    |
| 3     | Beta    | Arch  | 2        | 0           | 2       | 1    | 16    |

### Paso 2: Procesamiento de Cada Asignación

#### Asignación 1: Alpha - Arch
```python
# Datos de entrada
project_id = 1, phase = 'Arch', team_id = 2
devs_assigned = 1, hours_needed = 16
ready_date = 2025-06-16

# Cálculos
ready = max(ready_date, today) = 2025-06-16
hours_per_day = devs_assigned * 8 = 1 * 8 = 8 horas/día
days_needed = ceil(hours_needed / hours_per_day) = ceil(16 / 8) = 2 días

# Verificación de capacidad
def fits(2025-06-16):
    for day in [2025-06-16, 2025-06-17]:
        used = teams[2]['busy_devs'] + sum(active_assignments) = 0 + 0 = 0
        if used + 1 > 2: return False  # 0 + 1 <= 2 ✓
    return True

# Resultado
start_sim = 2025-06-16 (lunes)
end_sim = 2025-06-17 (martes)
project_next_free[1] = 2025-06-18 (miércoles)

# Registro en active_by_team
active_by_team[2] = [{'start': 2025-06-16, 'end': 2025-06-17, 'devs': 1}]
```

#### Asignación 2: Alpha - Model
```python
# Datos de entrada
project_id = 1, phase = 'Model', team_id = 3
devs_assigned = 1, hours_needed = 40
ready_date = 2025-06-16

# Cálculos
ready = max(ready_date, project_next_free[1]) = max(2025-06-16, 2025-06-18) = 2025-06-18
hours_per_day = 1 * 8 = 8 horas/día
days_needed = ceil(40 / 8) = 5 días

# Verificación de capacidad
def fits(2025-06-18):
    for day in [2025-06-18, 2025-06-19, 2025-06-20, 2025-06-23, 2025-06-24]:
        used = teams[3]['busy_devs'] + sum(active_assignments) = 0 + 0 = 0
        if used + 1 > 4: return False  # 0 + 1 <= 4 ✓
    return True

# Resultado
start_sim = 2025-06-18 (miércoles)
end_sim = 2025-06-24 (martes siguiente)
project_next_free[1] = 2025-06-25 (miércoles siguiente)

# Registro en active_by_team
active_by_team[3] = [{'start': 2025-06-18, 'end': 2025-06-24, 'devs': 1}]
```

#### Asignación 3: Beta - Arch
```python
# Datos de entrada
project_id = 2, phase = 'Arch', team_id = 2
devs_assigned = 1, hours_needed = 16
ready_date = 2025-06-16

# Cálculos
ready = max(ready_date, today) = 2025-06-16
days_needed = ceil(16 / 8) = 2 días

# Verificación de capacidad
def fits(2025-06-16):
    for day in [2025-06-16, 2025-06-17]:
        used = teams[2]['busy_devs'] = 0
        # Verificar asignaciones activas del equipo 2
        for assignment in active_by_team[2]:  # [{'start': 2025-06-16, 'end': 2025-06-17, 'devs': 1}]
            if assignment['start'] <= day <= assignment['end']:
                used += assignment['devs']  # used = 0 + 1 = 1
        if used + 1 > 2: return False  # 1 + 1 = 2 <= 2 ✓
    return True

# Resultado
start_sim = 2025-06-16 (lunes) - ¡Puede ejecutarse en paralelo!
end_sim = 2025-06-17 (martes)
project_next_free[2] = 2025-06-18 (miércoles)

# Registro en active_by_team
active_by_team[2] = [
    {'start': 2025-06-16, 'end': 2025-06-17, 'devs': 1},  # Alpha-Arch
    {'start': 2025-06-16, 'end': 2025-06-17, 'devs': 1}   # Beta-Arch
]
```

## Resultado Final del Schedule

| Project | Phase | Start      | End        | Duración |
|---------|-------|------------|------------|----------|
| Alpha   | Arch  | 2025-06-16 | 2025-06-17 | 2 días   |
| Alpha   | Model | 2025-06-18 | 2025-06-24 | 5 días   |
| Beta    | Arch  | 2025-06-16 | 2025-06-17 | 2 días   |

## Summary por Proyecto

| Project | State       | Start      | Est_End    | Duración Total |
|---------|-------------|------------|------------|----------------|
| Alpha   | Not started | 2025-06-16 | 2025-06-24 | 7 días hábiles |
| Beta    | Not started | 2025-06-16 | 2025-06-17 | 2 días hábiles |

## Aspectos Clave del Algoritmo

### 1. **Gestión de Dependencias Secuenciales**
- Alpha-Model no puede empezar hasta que termine Alpha-Arch
- `project_next_free[1]` rastrea cuándo puede empezar la siguiente fase del proyecto

### 2. **Paralelización Inteligente**
- Alpha-Arch y Beta-Arch se ejecutan en paralelo
- El equipo Arch tiene capacidad para 2 devs, ambos proyectos usan 1 dev cada uno

### 3. **Cálculo de Capacidad**
```python
# Para cada día del período requerido
used = teams[team_id]['busy_devs']  # Ocupación base
for assignment in active_by_team[team_id]:
    if assignment['start'] <= day <= assignment['end']:
        used += assignment['devs']  # Sumar asignaciones activas
# Verificar: used + new_devs <= total_devs
```

### 4. **Manejo de Días Hábiles**
- Usa `BusinessDay` para saltar fines de semana
- 2025-06-20 (viernes) → 2025-06-23 (lunes)

### 5. **Algoritmo de Búsqueda de Slot**
```python
while not fits(start_sim):
    # Encontrar próxima fecha de liberación
    overlaps = [a['end'] for a in active_by_team[team_id] 
                if a['start'] <= start_sim <= a['end']]
    if overlaps:
        start_sim = min(overlaps) + 1 día hábil
    else:
        start_sim = start_sim + 1 día hábil
```

## Validación del Test Case

### ¿Por qué este resultado es correcto?

1. **Respeta prioridades**: Alpha (prioridad 1) se procesa antes que Beta (prioridad 2)
2. **Respeta dependencias**: Alpha-Model espera a que termine Alpha-Arch
3. **Optimiza recursos**: Ejecuta Alpha-Arch y Beta-Arch en paralelo
4. **Calcula correctamente**: 
   - 16 horas ÷ 8 horas/día = 2 días
   - 40 horas ÷ 8 horas/día = 5 días
5. **Maneja capacidad**: No excede los límites de cada equipo

### Casos Edge Cubiertos

1. **Conflicto de recursos**: Si Beta-Arch necesitara 2 devs, tendría que esperar
2. **Dependencias de proyecto**: Model espera a Arch del mismo proyecto
3. **Días hábiles**: Automáticamente salta fines de semana
4. **Fechas ready**: Respeta cuándo puede empezar cada fase

## Extensiones Posibles

### Para What-If Analysis
```python
# Cambiar prioridades
assignments[2]['priority'] = 1  # Beta pasa a prioridad 1

# Cambiar recursos
teams[2]['total_devs'] = 3  # Contratar 1 dev más en Arch

# Cambiar complejidad
assignments[1]['hours_needed'] = 32  # Alpha-Model más complejo
```

### Para Optimización
```python
# Detectar cuellos de botella
bottleneck_teams = find_overutilized_teams(schedule)

# Sugerir reasignaciones
suggestions = optimize_resource_allocation(assignments, teams)
```

Este test case demuestra que el algoritmo funciona correctamente para casos reales y proporciona una base sólida para implementar las mejoras de what-if analysis propuestas.