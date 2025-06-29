# 🚀 APE (Automatic Project Estimator)

Sistema de estimación y planificación de proyectos internos de desarrollo de software con gestión de equipos especializados, tiers de complejidad y simulación de cronogramas.

## 📚 Documentación

### 🏗️ [Arquitectura Consolidada](ARQUITECTURA_CONSOLIDADA.md)
Documentación técnica completa del sistema:
- Modelo de datos detallado
- Algoritmo de scheduling paso a paso
- Stack tecnológico y componentes
- Casos especiales implementados
- Estrategia de testing
- Optimizaciones de rendimiento

### 📖 [Guía Completa del Usuario](GUIA_COMPLETA_APE.md)
Guía práctica para entender y usar APE:
- ¿Qué es APE y qué problema resuelve?
- Cómo funciona el sistema de tiers
- Casos especiales importantes (regla +1 día, paralelismo, etc.)
- Análisis What-If y visualizaciones
- Casos de uso reales y mejores prácticas

## 🚀 Inicio Rápido

```bash
# Clonar repositorio
git clone <repo-url>
cd marblefaraway

# Levantar con Docker
docker compose up --build

# Acceder a la aplicación
http://localhost:8501
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
python run_tests.py

# Tests específicos
python -m pytest tests/simulation/ -v
```

## 🎯 Características Principales

- **Equipos Especializados**: Arch → Model → Devs → Dqa (flujo secuencial)
- **Sistema de Tiers**: 4 niveles de complejidad con horas predefinidas
- **Simulación Inteligente**: Algoritmo que respeta capacidades y dependencias
- **Análisis What-If**: Experimentación sin afectar datos reales
- **Visualización Avanzada**: Gantt charts interactivos con Plotly
- **Paralelismo Automático**: Optimización de recursos disponibles

## 📊 Ejemplo de Uso

```
Proyecto Alpha (Prioridad 1, Tier 3):
├── Arch: 72h → 9 días (1 dev)
├── Model: 120h → 15 días (1 dev)  
├── Devs: 80h → 10 días (1 dev)
└── Dqa: 40h → 5 días (1 dev)

Total: 39 días hábiles
```

---

**Para información detallada, consulta la [Arquitectura Consolidada](ARQUITECTURA_CONSOLIDADA.md) y la [Guía Completa](GUIA_COMPLETA_APE.md).**