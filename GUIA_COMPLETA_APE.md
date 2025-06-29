# 📚 APE (Automatic Project Estimator) - Guía Completa del Sistema

## 🎯 ¿Qué es APE?

APE es un sistema de estimación y planificación de proyectos internos de desarrollo de software que te permite:

- **Gestionar equipos especializados** y su capacidad disponible
- **Estimar proyectos** basándose en niveles de complejidad (tiers)
- **Simular cronogramas** de entrega considerando dependencias entre fases
- **Realizar análisis "what-if"** para optimizar la planificación de recursos

## 🏢 Contexto de Negocio

### El Problema que Resuelve APE

Imagina que tienes varios proyectos de desarrollo y necesitas saber:
- ¿Cuándo va a terminar cada proyecto?
- ¿Qué equipo va a estar ocupado y cuándo?
- ¿Qué pasa si cambio las prioridades?
- ¿Dónde están los cuellos de botella?

**APE responde todas estas preguntas automáticamente.**

### Ejemplo Práctico

Tienes 3 proyectos:
- **Proyecto Alpha** (Prioridad 1): Sistema de facturación
- **Proyecto Beta** (Prioridad 2): Dashboard de reportes  
- **Proyecto Gamma** (Prioridad 3): API de integración

Cada proyecto pasa por 4 fases obligatorias:
1. **Arquitectura** (Arch) - Diseño del sistema
2. **Modelado** (Model) - Estructura de datos
3. **Desarrollo** (Devs) - Implementación
4. **QA** (Dqa) - Testing y validación

APE calcula automáticamente cuándo empieza y termina cada fase, considerando que:
- Las fases son **secuenciales** (Arch → Model → Devs → Dqa)
- Los equipos tienen **capacidad limitada**
- Los proyectos tienen **diferentes prioridades**

## 🎮 Cómo Funciona APE

### 1. **Configuración de Equipos**

Defines tus equipos especializados:

```
Equipo Arquitectura: 2 desarrolladores
Equipo Modelado: 4 desarrolladores  
Equipo Desarrollo: 6 desarrolladores
Equipo QA: 3 desarrolladores
```

### 2. **Definición de Proyectos**

Creas proyectos con:
- **Nombre**: "Sistema de Facturación v2.0"
- **Prioridad**: 1 (más importante = número menor)
- **Complejidad por fase**: Tier 1, 2, 3 o 4

### 3. **Sistema de Tiers (Complejidad)**

Cada fase tiene un **tier de complejidad** que determina las horas necesarias:

| Fase | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Descripción |
|------|--------|--------|--------|--------|-------------|
| **Arch** | 16h | 32h | 72h | 240h | Arquitectura simple → compleja |
| **Model** | 40h | 80h | 120h | 160h | Modelado básico → avanzado |
| **Devs** | 16h | 40h | 80h | 120h | Desarrollo rápido → extenso |
| **Dqa** | 8h | 24h | 40h | - | Testing básico → completo |

**Ejemplo**: Un proyecto Tier 3 en Desarrollo necesita 80 horas.
- Con 1 desarrollador: 80h ÷ 8h/día = 10 días
- Con 2 desarrolladores: 80h ÷ 16h/día = 5 días

### 4. **Simulación Automática**

APE ejecuta una simulación que:

1. **Ordena proyectos por prioridad** (1, 2, 3...)
2. **Procesa cada fase secuencialmente** (Arch → Model → Devs → Dqa)
3. **Busca el primer slot disponible** en cada equipo
4. **Calcula fechas de inicio y fin** considerando días hábiles
5. **Actualiza la ocupación** de cada equipo

## 📊 Casos Especiales Importantes

### 1. **La Regla del +1 Día**

**Situación**: Una fase necesita 8 horas y empieza el lunes.
**Matemática simple**: 8h ÷ 8h/día = 1 día → terminaría el lunes
**Realidad**: Las 8 horas se ejecutan **durante** el lunes → termina al final del lunes

**Solución APE**: Suma 1 día para reflejar el paso real del tiempo.
- Empieza: Lunes
- Termina: Lunes (al final del día)
- Siguiente fase puede empezar: Martes

### 2. **Paralelismo Inteligente**

APE permite que diferentes proyectos usen el mismo equipo **en paralelo** si hay capacidad:

```
Equipo Arquitectura (2 desarrolladores):
Lunes: Alpha-Arch (1 dev) + Beta-Arch (1 dev) = 2/2 devs ✅
Martes: Solo Gamma-Arch (1 dev) = 1/2 devs ✅
```

### 3. **Dependencias Secuenciales Estrictas**

Dentro del mismo proyecto, las fases **NUNCA** se solapan:

```
Proyecto Alpha:
Arch: 16-17 enero → Model: 18-24 enero → Devs: 25-31 enero → Dqa: 1-5 febrero
```

### 4. **Manejo de Prioridades**

Los proyectos se procesan en orden de prioridad:

```
Priority 1: Alpha se programa primero
Priority 2: Beta se programa después (usando slots libres)
Priority 3: Gamma se programa al final
```

### 5. **Restricciones de Fecha**

Puedes definir que una fase no puede empezar antes de cierta fecha:

```
Proyecto Beta - Fase Desarrollo:
ready_to_start_date = 15 febrero
→ Aunque el equipo esté libre antes, no empezará hasta el 15 de febrero
```

## 🎨 Interfaz de Usuario

### Módulo Teams (Equipos)
- **Ver capacidad** de cada equipo
- **Configurar tiers** (horas por complejidad)
- **Ajustar disponibilidad** (devs ocupados)

### Módulo Projects (Proyectos)  
- **Crear/editar proyectos** con prioridades
- **Asignar complejidad** por fase
- **Definir fechas límite** y restricciones

### Módulo Monitoring (Cronograma)
- **Ver cronograma simulado** en tabla
- **Analizar utilización** de equipos
- **Identificar cuellos de botella**

### Módulo Simulation (Análisis What-If)
- **Experimentar con escenarios** sin afectar datos reales
- **Cambiar prioridades temporalmente**
- **Ajustar capacidades** de equipos
- **Ver impacto inmediato** en cronograma

## 📈 Visualizaciones Avanzadas

### Vista Detallada (Gantt)
Muestra cada fase como una línea separada:
```
Alpha-Arch    |████|
Alpha-Model   |      ████████|
Alpha-Devs    |              ██████|
Beta-Arch     |████|
Beta-Model    |      ████████|
```

### Vista Consolidada (Timeline)
Muestra cada proyecto como una línea continua con fases en colores:
```
Alpha  |Arch|Model    |Devs  |Dqa|
Beta   |Arch|Model    |Devs  |Dqa|
```

**Colores por fase**:
- 🔴 **Arch** (Rojo) - Arquitectura
- 🔵 **Model** (Azul) - Modelado
- 🟢 **Devs** (Verde) - Desarrollo  
- 🟡 **Dqa** (Amarillo) - QA

## 🔍 Análisis What-If

### Preguntas que Puedes Responder

**"¿Qué pasa si cambio las prioridades?"**
- Arrastra proyectos en el orden deseado
- Ve inmediatamente el nuevo cronograma

**"¿Qué pasa si tengo menos desarrolladores?"**
- Ajusta la capacidad de equipos
- Observa cómo se extienden los plazos

**"¿Qué pasa si un proyecto es más complejo?"**
- Cambia el tier de una fase
- Ve el impacto en duración total

**"¿Dónde están los cuellos de botella?"**
- Revisa la utilización por equipo
- Identifica equipos al 100% de capacidad

### Ejemplo de Análisis

**Escenario Base**:
- Arch: 2 devs, Model: 4 devs, Devs: 6 devs, Dqa: 3 devs
- 3 proyectos con prioridades 1, 2, 3
- Todos Tier 2

**Resultado**: Proyectos terminan en 8 semanas

**What-If: "¿Qué pasa si contrato 1 dev más en Arch?"**
- Cambias Arch de 2 a 3 devs
- **Resultado**: Proyectos terminan en 6 semanas (25% más rápido)

**Insight**: El equipo de Arquitectura era el cuello de botella.

## 🚀 Casos de Uso Reales

### 1. **Planificación Trimestral**
- Cargas todos los proyectos del trimestre
- Defines prioridades según objetivos de negocio
- APE te dice si es factible con los recursos actuales

### 2. **Análisis de Contratación**
- Simulas diferentes escenarios de contratación
- Identificas qué equipos necesitan refuerzo
- Calculas ROI de nuevas contrataciones

### 3. **Gestión de Crisis**
- Un proyecto se vuelve urgente (prioridad 1)
- APE recalcula todo el cronograma automáticamente
- Ves qué proyectos se retrasan y por cuánto

### 4. **Optimización de Recursos**
- Experimentas con diferentes asignaciones
- Encuentras la distribución óptima de desarrolladores
- Minimizas tiempo total de entrega

## 🎯 Beneficios Clave

### Para Project Managers
- **Visibilidad completa** del pipeline de proyectos
- **Fechas realistas** basadas en capacidad real
- **Identificación temprana** de problemas
- **Comunicación clara** con stakeholders

### Para Team Leads
- **Planificación de capacidad** por equipo
- **Identificación de cuellos de botella**
- **Optimización de asignaciones**
- **Previsión de carga de trabajo**

### Para Management
- **Toma de decisiones** basada en datos
- **Análisis de escenarios** what-if
- **ROI de contrataciones** y recursos
- **Cumplimiento de compromisos** más confiable

## 🔧 Configuración y Personalización

### Configuración Inicial
1. **Define tus equipos** y sus capacidades
2. **Configura la matriz de tiers** según tu contexto
3. **Carga proyectos** con prioridades realistas
4. **Ejecuta primera simulación** para validar

### Personalización Avanzada
- **Ajusta horas por tier** según tu experiencia histórica
- **Define restricciones** de fecha por proyecto
- **Configura alertas** para cuellos de botella
- **Personaliza visualizaciones** según preferencias

## 📊 Métricas y KPIs

### Métricas de Proyecto
- **Duración total**: Desde primera fase hasta última
- **Horas planificadas**: Suma de todas las fases
- **Fecha de entrega**: Cuándo termina realmente
- **Delay vs. objetivo**: Diferencia con fecha límite

### Métricas de Equipo
- **Utilización promedio**: % de capacidad usada
- **Períodos de inactividad**: Cuándo están libres
- **Carga de trabajo**: Distribución temporal
- **Cuellos de botella**: Equipos al límite

### Métricas de Portfolio
- **Throughput**: Proyectos completados por mes
- **Lead time**: Tiempo promedio por proyecto
- **Eficiencia**: Horas planificadas vs. disponibles
- **Predictibilidad**: Variación vs. estimaciones

## 🎓 Tips y Mejores Prácticas

### Para Estimaciones Precisas
1. **Usa datos históricos** para calibrar tiers
2. **Revisa y ajusta** la matriz regularmente
3. **Considera buffers** para imprevistos
4. **Valida con el equipo** las estimaciones

### Para Planificación Efectiva
1. **Define prioridades claras** y comunícalas
2. **Revisa cronogramas** semanalmente
3. **Anticipa cuellos de botella** y actúa temprano
4. **Mantén flexibilidad** para cambios urgentes

### Para Análisis What-If
1. **Experimenta con escenarios** extremos
2. **Documenta insights** importantes
3. **Comparte hallazgos** con el equipo
4. **Usa datos** para justificar decisiones

## 🚀 Próximos Pasos

### Si eres nuevo en APE
1. **Explora los módulos** uno por uno
2. **Carga datos de prueba** para familiarizarte
3. **Experimenta con simulaciones** simples
4. **Gradualmente agrega** complejidad real

### Si ya usas APE
1. **Optimiza tu configuración** de tiers
2. **Experimenta con análisis** what-if avanzados
3. **Automatiza reportes** regulares
4. **Comparte insights** con otros equipos

---

**APE transforma la planificación de proyectos de un arte subjetivo en una ciencia basada en datos, permitiendo decisiones más informadas y cronogramas más confiables.**