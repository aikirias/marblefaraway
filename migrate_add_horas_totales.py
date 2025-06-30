#!/usr/bin/env python3
"""
Script de migración para agregar el campo horas_totales_estimadas a la tabla projects
"""

import os
import sqlalchemy as sa
from sqlalchemy import text

def migrate_database():
    """Agrega la columna horas_totales_estimadas a la tabla projects"""
    
    # Obtener URL de la base de datos
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Error: Variable de entorno DATABASE_URL no está configurada")
        return False
    
    try:
        # Crear conexión
        engine = sa.create_engine(db_url, future=True)
        
        with engine.begin() as conn:
            # Verificar si la columna ya existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'projects' 
                AND column_name = 'horas_totales_estimadas'
            """))
            
            if result.fetchone():
                print("✅ La columna 'horas_totales_estimadas' ya existe en la tabla projects")
                return True
            
            # Agregar la nueva columna
            print("🔄 Agregando columna 'horas_totales_estimadas' a la tabla projects...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN horas_totales_estimadas INTEGER NOT NULL DEFAULT 0
            """))
            
            print("✅ Migración completada exitosamente")
            print("📊 La columna 'horas_totales_estimadas' ha sido agregada a la tabla projects")
            
            # Verificar que la columna se agregó correctamente
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'projects' 
                AND column_name = 'horas_totales_estimadas'
            """))
            
            column_info = result.fetchone()
            if column_info:
                print(f"📋 Información de la columna: {column_info}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando migración de base de datos...")
    print("📝 Agregando campo 'horas_totales_estimadas' a la tabla projects")
    
    success = migrate_database()
    
    if success:
        print("\n✅ Migración completada exitosamente!")
        print("🎯 Ahora puedes usar la funcionalidad de cálculo de horas faltantes")
    else:
        print("\n❌ La migración falló. Revisa los errores anteriores.")
        exit(1)