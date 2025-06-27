#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas de rendimiento en APE
Ejecuta la aplicación y captura logs para análisis
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def run_app_with_logging():
    """Ejecuta la aplicación con logging habilitado"""
    
    print("🔍 DIAGNÓSTICO DE RENDIMIENTO APE")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Cambiar al directorio de la app
    app_dir = "./app"
    if not os.path.exists(app_dir):
        print("❌ Error: Directorio ./app no encontrado")
        return
    
    print("📂 Cambiando al directorio de la aplicación...")
    os.chdir(app_dir)
    
    # Verificar que existe app.py
    if not os.path.exists("app.py"):
        print("❌ Error: app.py no encontrado en ./app")
        return
    
    print("🚀 Iniciando aplicación Streamlit...")
    print("📝 Los logs de diagnóstico aparecerán a continuación:")
    print("-" * 50)
    
    try:
        # Ejecutar streamlit con output en tiempo real
        process = subprocess.Popen(
            ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print("✅ Aplicación iniciada. Accede a http://localhost:8501")
        print("🔍 Monitoreando logs de rendimiento...")
        print("⚠️  Presiona Ctrl+C para detener")
        print()
        
        # Leer output en tiempo real
        for line in iter(process.stdout.readline, ''):
            if line:
                # Filtrar y resaltar logs de diagnóstico
                line = line.strip()
                if any(tag in line for tag in ['[STREAMLIT]', '[SCHEDULER]', '[GANTT]']):
                    print(f"🐛 {line}")
                elif "ERROR" in line.upper() or "EXCEPTION" in line.upper():
                    print(f"❌ {line}")
                elif "WARNING" in line.upper() or "WARN" in line.upper():
                    print(f"⚠️  {line}")
                else:
                    # Mostrar otros logs importantes de Streamlit
                    if any(keyword in line for keyword in ['Running on', 'Local URL', 'Network URL', 'External URL']):
                        print(f"ℹ️  {line}")
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo aplicación...")
        process.terminate()
        process.wait()
        print("✅ Aplicación detenida")
        
    except Exception as e:
        print(f"❌ Error ejecutando aplicación: {e}")
        if 'process' in locals():
            process.terminate()

def show_instructions():
    """Muestra instrucciones para el diagnóstico"""
    print("\n📋 INSTRUCCIONES PARA EL DIAGNÓSTICO:")
    print("=" * 50)
    print("1. La aplicación se iniciará en http://localhost:8501")
    print("2. Ve a la pestaña 'Simulation'")
    print("3. Intenta ejecutar una simulación")
    print("4. Observa los logs que aparecen aquí:")
    print()
    print("🔍 LOGS A OBSERVAR:")
    print("   • [STREAMLIT] - Detecta re-renderizado excesivo")
    print("   • [SCHEDULER] - Detecta bucles infinitos en scheduling")
    print("   • [GANTT] - Detecta problemas en generación de gráficos")
    print()
    print("⚠️  SEÑALES DE PROBLEMAS:")
    print("   • Muchas iteraciones en scheduler (>50)")
    print("   • Múltiples renderizados de Streamlit")
    print("   • Muchas trazas en Gantt consolidado (>100)")
    print()

if __name__ == "__main__":
    show_instructions()
    input("Presiona Enter para continuar...")
    run_app_with_logging()