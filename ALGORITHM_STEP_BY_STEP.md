# Algoritmo de Scheduling - Paso a Paso con Estados de Memoria

## Estructuras de Datos en Memoria

El algoritmo mantiene estas estructuras de datos que van cambiando durante la ejecución:

```python
# Estado inicial
active_by_team = {
    2: [],  # Equipo Arch (team_id=2)
    3: []   # Equipo Model (team_id=3)
}

project_next_free = {}  # Cuándo puede empezar la siguiente fase de cada proyecto

records = []  # Resultados finales del cronograma
```

## Datos de Entrada Ordenados

Después del ordenamiento por `priority` y `phase_order`:

```python
df_sorted = [
    # Índice 0
    {'project_id': 1, 'project_name': 'Alpha', 'phase': 'Arch', 'team_id': 2, 
     'devs_assigned': 1, 'hours_needed': 16, 'ready_date': '2025-06-16'},
    
    # Índice 1  
    {'project_id': 1, 'project_name': 'Alpha', 'phase': 'Model', 'team_id': 3,
     'devs_assigned': 1, 'hours_needed': 40, 'ready_date': '2025-06-16'},
    
    # Índice 2
    {'project_id': 2, 'project_name': 'Beta', 'phase': 'Arch', 'team_id': 2,
     'devs_assigned': 1, 'hours_needed': 16, 'ready_date': '2025-06-16'}
]
```

## Ejecución Paso a Paso

### ITERACIÓN 1: Alpha - Arch

#### Estado Inicial
```python
# Antes de procesar Alpha-Arch
active_by_team = {
    2: [],  # Equipo Arch vacío
    3: []   # Equipo Model vacío
}
project_next_free = {}
records = []
```

#### Cálculos
```python
# Datos de la asignación actual
r = df_sorted[0]  # Alpha-Arch
project_id = 1
team_id = 2
devs_assigned = 1
hours_needed = 16
ready_date = date(2025, 6, 16)

# Fecha de inicio mínima
ready = max(ready_date, today) = max(2025-06-16, 2025-06-16) = 2025-06-16

# Como project_id=1 no está en project_next_free, no hay restricción adicional

# Duración
hours_per_day = devs_assigned * 8 = 1 * 8 = 8
days_needed = ceil(hours_needed / hours_per_day) = ceil(16 / 8) = 2
```

#### Verificación de Capacidad
```python
def fits(start_date=2025-06-16):
    # Verificar cada día del período [2025-06-16, 2025-06-17]
    
    # Día 1: 2025-06-16 (lunes)
    day = 2025-06-16
    used = teams[2]['busy_devs'] = 0  # No hay devs ocupados base
    
    # Verificar asignaciones activas en active_by_team[2]
    for assignment in active_by_team[2]:  # active_by_team[2] = [] (vacío)
        if assignment['start'] <= day <= assignment['end']:
            used += assignment['devs']
    # used sigue siendo 0
    
    if used + devs_assigned > teams[2]['total_devs']:  # 0 + 1 > 2? NO
        return False
    
    # Día 2: 2025-06-17 (martes)
    day = 2025-06-17
    used = 0  # Mismo cálculo, active_by_team[2] sigue vacío
    if 0 + 1 > 2:  # NO
        return False
    
    return True  # ✓ Cabe perfectamente
```

#### Resultado y Actualización de Estado
```python
# Fechas calculadas
start_sim = 2025-06-16
end_sim = 2025-06-17
next_free = 2025-06-18

# ACTUALIZAR ESTRUCTURAS DE DATOS
active_by_team[2].append({
    'start': date(2025, 6, 16),
    'end': date(2025, 6, 17),
    'devs': 1
})

project_next_free[1] = date(2025, 6, 18)

records.append({
    'project_id': 1,
    'project_name': 'Alpha',
    'phase': 'Arch',
    'start': date(2025, 6, 16),
    'end': date(2025, 6, 17)
})
```

#### Estado Después de Iteración 1
```python
active_by_team = {
    2: [{'start': date(2025, 6, 16), 'end': date(2025, 6, 17), 'devs': 1}],
    3: []
}

project_next_free = {
    1: date(2025, 6, 18)  # Alpha puede continuar el 18 de junio
}

records = [
    {'project_id': 1, 'project_name': 'Alpha', 'phase': 'Arch', 
     'start': date(2025, 6, 16), 'end': date(2025, 6, 17)}
]
```

### ITERACIÓN 2: Alpha - Model

#### Estado Inicial
```python
# Antes de procesar Alpha-Model
active_by_team = {
    2: [{'start': date(2025, 6, 16), 'end': date(2025, 6, 17), 'devs': 1}],
    3: []  # Equipo Model sigue vacío
}
project_next_free = {1: date(2025, 6, 18)}
```

#### Cálculos
```python
r = df_sorted[1]  # Alpha-Model
project_id = 1
team_id = 3
devs_assigned = 1
hours_needed = 40
ready_date = date(2025, 6, 16)

# Fecha de inicio mínima
ready = max(ready_date, today) = max(2025-06-16, 2025-06-16) = 2025-06-16

# PERO project_id=1 SÍ está en project_next_free
ready = max(ready, project_next_free[1]) = max(2025-06-16, 2025-06-18) = 2025-06-18

# Duración
hours_per_day = 1 * 8 = 8
days_needed = ceil(40 / 8) = 5
```

#### Verificación de Capacidad
```python
def fits(start_date=2025-06-18):
    # Verificar período [2025-06-18, 2025-06-19, 2025-06-20, 2025-06-23, 2025-06-24]
    # (Nota: 2025-06-21 y 2025-06-22 son fin de semana, se saltan)
    
    for day in [2025-06-18, 2025-06-19, 2025-06-20, 2025-06-23, 2025-06-24]:
        used = teams[3]['busy_devs'] = 0
        
        # Verificar active_by_team[3]
        for assignment in active_by_team[3]:  # active_by_team[3] = [] (vacío)
            if assignment['start'] <= day <= assignment['end']:
                used += assignment['devs']
        # used = 0
        
        if used + 1 > 4:  # 0 + 1 > 4? NO
            return False
    
    return True  # ✓ Cabe perfectamente
```

#### Resultado y Actualización de Estado
```python
start_sim = 2025-06-18
end_sim = 2025-06-24  # 5 días hábiles después
next_free = 2025-06-25

# ACTUALIZAR ESTRUCTURAS
active_by_team[3].append({
    'start': date(2025, 6, 18),
    'end': date(2025, 6, 24),
    'devs': 1
})

project_next_free[1] = date(2025, 6, 25)  # Actualizar para Alpha

records.append({
    'project_id': 1,
    'project_name': 'Alpha',
    'phase': 'Model',
    'start': date(2025, 6, 18),
    'end': date(2025, 6, 24)
})
```

#### Estado Después de Iteración 2
```python
active_by_team = {
    2: [{'start': date(2025, 6, 16), 'end': date(2025, 6, 17), 'devs': 1}],
    3: [{'start': date(2025, 6, 18), 'end': date(2025, 6, 24), 'devs': 1}]
}

project_next_free = {
    1: date(2025, 6, 25)  # Alpha actualizado
}

records = [
    {'project_id': 1, 'project_name': 'Alpha', 'phase': 'Arch', 
     'start': date(2025, 6, 16), 'end': date(2025, 6, 17)},
    {'project_id': 1, 'project_name': 'Alpha', 'phase': 'Model',
     'start': date(2025, 6, 18), 'end': date(2025, 6, 24)}
]
```

### ITERACIÓN 3: Beta - Arch

#### Estado Inicial
```python
# Antes de procesar Beta-Arch
active_by_team = {
    2: [{'start': date(2025, 6, 16), 'end': date(2025, 6, 17), 'devs': 1}],  # Alpha-Arch ocupando 1 dev
    3: [{'start': date(2025, 6, 18), 'end': date(2025, 6, 24), 'devs': 1}]   # Alpha-Model ocupando 1 dev
}
project_next_free = {1: date(2025, 6, 25)}
```

#### Cálculos
```python
r = df_sorted[2]  # Beta-Arch
project_id = 2
team_id = 2  # ¡Mismo equipo que Alpha-Arch!
devs_assigned = 1
hours_needed = 16
ready_date = date(2025, 6, 16)

ready = max(2025-06-16, 2025-06-16) = 2025-06-16
# project_id=2 no está en project_next_free, no hay restricción

days_needed = ceil(16 / 8) = 2
```

#### Verificación de Capacidad (¡CLAVE!)
```python
def fits(start_date=2025-06-16):
    # Verificar período [2025-06-16, 2025-06-17]
    
    # Día 1: 2025-06-16
    day = 2025-06-16
    used = teams[2]['busy_devs'] = 0
    
    # ¡AHORA active_by_team[2] NO está vacío!
    for assignment in active_by_team[2]:  # [{'start': 2025-06-16, 'end': 2025-06-17, 'devs': 1}]
        if assignment['start'] <= day <= assignment['end']:  # 2025-06-16 <= 2025-06-16 <= 2025-06-17? SÍ
            used += assignment['devs']  # used = 0 + 1 = 1
    
    if used + devs_assigned > teams[2]['total_devs']:  # 1 + 1 > 2? NO (1 + 1 = 2 ≤ 2)
        return False
    
    # Día 2: 2025-06-17
    day = 2025-06-17
    used = 0
    for assignment in active_by_team[2]:
        if 2025-06-16 <= 2025-06-17 <= 2025-06-17:  # SÍ
            used += 1  # used = 1
    
    if 1 + 1 > 2:  # NO
        return False
    
    return True  # ✓ ¡Cabe! Usa el segundo dev del equipo Arch
```

#### Resultado y Actualización Final
```python
start_sim = 2025-06-16  # ¡Mismo día que Alpha-Arch!
end_sim = 2025-06-17
next_free = 2025-06-18

# ACTUALIZAR ESTRUCTURAS
active_by_team[2].append({
    'start': date(2025, 6, 16),
    'end': date(2025, 6, 17),
    'devs': 1
})

project_next_free[2] = date(2025, 6, 18)  # Nuevo proyecto

records.append({
    'project_id': 2,
    'project_name': 'Beta',
    'phase': 'Arch',
    'start': date(2025, 6, 16),
    'end': date(2025, 6, 17)
})
```

## Estado Final de Todas las Estructuras

```python
# ESTADO FINAL
active_by_team = {
    2: [  # Equipo Arch
        {'start': date(2025, 6, 16), 'end': date(2025, 6, 17), 'devs': 1},  # Alpha-Arch
        {'start': date(2025, 6, 16), 'end': date(2025, 6, 17), 'devs': 1}   # Beta-Arch (PARALELO!)
    ],
    3: [  # Equipo Model
        {'start': date(2025, 6, 18), 'end': date(2025, 6, 24), 'devs': 1}   # Alpha-Model
    ]
}

project_next_free = {
    1: date(2025, 6, 25),  # Alpha puede continuar (si tuviera más fases)
    2: date(2025, 6, 18)   # Beta puede continuar
}

records = [
    {'project_id': 1, 'project_name': 'Alpha', 'phase': 'Arch', 
     'start': date(2025, 6, 16), 'end': date(2025, 6, 17)},
    {'project_id': 1, 'project_name': 'Alpha', 'phase': 'Model',
     'start': date(2025, 6, 18), 'end': date(2025, 6, 24)},
    {'project_id': 2, 'project_name': 'Beta', 'phase': 'Arch',
     'start': date(2025, 6, 16), 'end': date(2025, 6, 17)}
]
```

## Visualización del Cronograma Final

```
Equipo Arch (team_id=2, capacity=2):
2025-06-16: [Alpha-Arch(1 dev), Beta-Arch(1 dev)] = 2/2 devs ocupados
2025-06-17: [Alpha-Arch(1 dev), Beta-Arch(1 dev)] = 2/2 devs ocupados
2025-06-18: [] = 0/2 devs ocupados

Equipo Model (team_id=3, capacity=4):
2025-06-16: [] = 0/4 devs ocupados
2025-06-17: [] = 0/4 devs ocupados
2025-06-18: [Alpha-Model(1 dev)] = 1/4 devs ocupados
2025-06-19: [Alpha-Model(1 dev)] = 1/4 devs ocupados
2025-06-20: [Alpha-Model(1 dev)] = 1/4 devs ocupados
2025-06-23: [Alpha-Model(1 dev)] = 1/4 devs ocupados
2025-06-24: [Alpha-Model(1 dev)] = 1/4 devs ocupados
2025-06-25: [] = 0/4 devs ocupados
```

## Puntos Clave del Algoritmo

1. **`active_by_team`** rastrea qué asignaciones están activas en cada equipo en cada momento
2. **`project_next_free`** asegura que las fases de un proyecto sean secuenciales
3. **La función `fits()`** verifica si hay capacidad sumando todas las asignaciones activas
4. **El paralelismo** surge naturalmente cuando hay capacidad disponible
5. **Todo se mantiene en memoria** durante la simulación, no se persiste en la DB

Este algoritmo permite que Alpha-Arch y Beta-Arch se ejecuten en paralelo porque el equipo Arch tiene capacidad para 2 desarrolladores y cada asignación solo necesita 1.