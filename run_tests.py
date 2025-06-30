#!/usr/bin/env python3
"""
Script para ejecutar tests del sistema APE con diferentes opciones
"""

import subprocess
import sys
import argparse


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Ejecutando: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} - EXITOSO")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FALLÓ (código: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"\n❌ Error: pytest no encontrado. Instala las dependencias con:")
        print("pip install -r tests/requirements.txt")
        return False


def main():
    parser = argparse.ArgumentParser(description="Ejecutar tests del sistema APE")
    parser.add_argument("--unit", action="store_true", help="Ejecutar solo unit tests")
    parser.add_argument("--integration", action="store_true", help="Ejecutar solo integration tests")
    parser.add_argument("--simulation", action="store_true", help="Ejecutar solo simulation tests")
    parser.add_argument("--gantt", action="store_true", help="Ejecutar solo gantt tests")
    parser.add_argument("--coverage", action="store_true", help="Ejecutar con reporte de cobertura")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verbose")
    parser.add_argument("--fast", action="store_true", help="Ejecutar tests rápidos solamente")
    
    args = parser.parse_args()
    
    # Comando base
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    success = True
    
    if args.unit:
        cmd = base_cmd + ["tests/unit/"]
        success &= run_command(cmd, "Unit Tests")
    
    elif args.integration:
        cmd = base_cmd + ["tests/integration/"]
        success &= run_command(cmd, "Integration Tests")
    
    elif args.simulation:
        cmd = base_cmd + ["tests/simulation/"]
        success &= run_command(cmd, "Simulation Tests")
    
    elif args.gantt:
        cmd = base_cmd + ["tests/gantt/"]
        success &= run_command(cmd, "Gantt Tests")
    
    elif args.coverage:
        cmd = base_cmd + [
            "tests/",
            "--cov=app/modules",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ]
        success &= run_command(cmd, "Tests con Cobertura")
        
        if success:
            print(f"\n📊 Reporte de cobertura generado en: htmlcov/index.html")
    
    elif args.fast:
        cmd = base_cmd + ["tests/", "-m", "not slow"]
        success &= run_command(cmd, "Tests Rápidos")
    
    else:
        # Ejecutar todos los tests por categoría
        print("🚀 Ejecutando suite completa de tests APE")
        
        # Unit tests
        cmd = base_cmd + ["tests/unit/"]
        success &= run_command(cmd, "Unit Tests")
        
        # Integration tests
        cmd = base_cmd + ["tests/integration/"]
        success &= run_command(cmd, "Integration Tests")
        
        # Simulation tests
        cmd = base_cmd + ["tests/simulation/"]
        success &= run_command(cmd, "Simulation Tests")
        
        # Gantt tests
        cmd = base_cmd + ["tests/gantt/"]
        success &= run_command(cmd, "Gantt Tests")
    
    # Resumen final
    print(f"\n{'='*60}")
    if success:
        print("🎉 TODOS LOS TESTS PASARON")
        print("✅ El sistema APE está funcionando correctamente")
    else:
        print("💥 ALGUNOS TESTS FALLARON")
        print("❌ Revisa los errores arriba y corrige los problemas")
    print(f"{'='*60}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())