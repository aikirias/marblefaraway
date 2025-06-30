#!/usr/bin/env python3
"""
Script para crear datos de prueba para validar los bugs reportados
"""

import os
import sys
from datetime import date, timedelta

# Agregar el directorio app al path
sys.path.append('app')

from modules.common.models import Project
from modules.common.projects_crud import create_project
from modules.common.assignments_crud import create_assignment
from modules.common.models import Assignment
from modules.common.teams_crud import read_all_teams

def create_test_projects():
    """Crear proyectos de prueba para validar bugs"""
    
    print("🚀 Creando proyectos de prueba...")
    
    # Proyecto 1: Activo con horas trabajadas
    project1 = Project(
        id=0,
        name="Sistema de Facturación",
        priority=1,
        start_date=date.today() - timedelta(days=10),
        due_date_wo_qa=date.today() + timedelta(days=20),
        due_date_with_qa=date.today() + timedelta(days=25),
        phase="development",
        active=True,
        horas_trabajadas=24,  # Tiene horas trabajadas para Bug #2
        fecha_inicio_real=date.today() - timedelta(days=8)
    )
    
    # Proyecto 2: Activo sin horas trabajadas
    project2 = Project(
        id=0,
        name="Portal de Clientes",
        priority=2,
        start_date=date.today() - timedelta(days=5),
        due_date_wo_qa=date.today() + timedelta(days=30),
        due_date_with_qa=date.today() + timedelta(days=35),
        phase="development",
        active=True,
        horas_trabajadas=0,
        fecha_inicio_real=date.today() - timedelta(days=3)
    )
    
    # Proyecto 3: Inactivo con horas trabajadas
    project3 = Project(
        id=0,
        name="API de Integración",
        priority=3,
        start_date=date.today() + timedelta(days=5),
        due_date_wo_qa=date.today() + timedelta(days=40),
        due_date_with_qa=date.today() + timedelta(days=45),
        phase="draft",
        active=False,
        horas_trabajadas=16,  # Tiene horas trabajadas para Bug #2
        fecha_inicio_real=None
    )
    
    projects = [project1, project2, project3]
    
    # Crear proyectos en DB
    for project in projects:
        proj_id = create_project(project)
        print(f"✅ Creado proyecto: {project.name} (ID: {proj_id})")
        
        # Crear asignaciones por defecto para todos los equipos
        teams = read_all_teams()
        for team_id, team in teams.items():
            max_tier = max(team.tier_capacities.keys()) if team.tier_capacities else 1
            
            assignment = Assignment(
                id=0,
                project_id=proj_id,
                project_name=project.name,
                project_priority=project.priority,
                team_id=team_id,
                team_name=team.name,
                tier=max_tier,
                devs_assigned=1.0,
                max_devs=1.0,
                estimated_hours=80,  # Horas estimadas para calcular horas faltantes
                ready_to_start_date=project.start_date,
                assignment_start_date=project.start_date,
                status="In Progress" if project.active else "Not Started",
                pending_hours=80 - (project.horas_trabajadas // len(teams)) if project.horas_trabajadas > 0 else 80,
                paused_on=None
            )
            create_assignment(assignment)
    
    print(f"🎉 Creados {len(projects)} proyectos de prueba con sus asignaciones")
    print("\n📋 Resumen de datos de prueba:")
    print("- Sistema de Facturación: ACTIVO, 24 horas trabajadas")
    print("- Portal de Clientes: ACTIVO, 0 horas trabajadas") 
    print("- API de Integración: INACTIVO, 16 horas trabajadas")
    print("\n🔍 Ahora puedes validar los bugs:")
    print("Bug #1: Cambiar estado de 'Sistema de Facturación' y verificar sincronización")
    print("Bug #2: Verificar cálculo de horas faltantes en proyectos con horas trabajadas")

if __name__ == "__main__":
    create_test_projects()