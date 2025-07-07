"""
CRUD operations para el sistema de planes persistentes
Maneja guardado, recuperación y comparación de planes de simulación
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

from .db import get_db_connection
from .models import Plan, PlanAssignment, ScheduleResult, Assignment

logger = logging.getLogger(__name__)


class PlansError(Exception):
    """Excepción base para errores del sistema de planes"""
    pass


def save_plan(result: ScheduleResult, name: str = "", description: str = "", 
              set_as_active: bool = True, current_priorities: Dict[int, int] = None) -> Plan:
    """
    Guarda un resultado de simulación como plan persistente
    
    Args:
        result: Resultado de la simulación
        name: Nombre del plan (opcional, se genera automáticamente si está vacío)
        description: Descripción del plan
        set_as_active: Si marcar este plan como activo
        current_priorities: Diccionario con las prioridades actuales {project_id: priority}
    
    Returns:
        Plan guardado con ID asignado
    
    Raises:
        PlansError: Si hay error guardando el plan
    """
    try:
        # Crear plan desde resultado
        plan = Plan.from_schedule_result(result, name, description)
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Si se debe marcar como activo, desactivar otros planes primero
                if set_as_active:
                    cursor.execute("UPDATE plans SET is_active = false WHERE is_active = true")
                    plan.is_active = True
                
                # Insertar plan principal
                cursor.execute("""
                    INSERT INTO plans (name, description, checksum, is_active, 
                                     simulation_date, total_assignments, total_projects)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """, (
                    plan.name, plan.description, plan.checksum, plan.is_active,
                    plan.simulation_date, plan.total_assignments, plan.total_projects
                ))
                
                row = cursor.fetchone()
                plan.id = row['id']
                plan.created_at = row['created_at']
                
                # Insertar asignaciones del plan
                plan_assignments = []
                for assignment in result.assignments:
                    # Obtener prioridad específica del plan o usar la del proyecto
                    priority_order = None
                    if current_priorities and assignment.project_id in current_priorities:
                        priority_order = current_priorities[assignment.project_id]
                    
                    plan_assignment = PlanAssignment.from_assignment(assignment, plan.id, priority_order)
                    plan_assignments.append(plan_assignment)
                
                if plan_assignments:
                    cursor.executemany("""
                        INSERT INTO plan_assignments (
                            plan_id, assignment_id, project_id, project_name, project_priority,
                            priority_order, team_id, team_name, tier, devs_assigned, estimated_hours,
                            calculated_start_date, calculated_end_date, pending_hours,
                            ready_to_start_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        (
                            pa.plan_id, pa.assignment_id, pa.project_id, pa.project_name,
                            pa.project_priority, pa.priority_order, pa.team_id, pa.team_name, pa.tier,
                            pa.devs_assigned, pa.estimated_hours, pa.calculated_start_date,
                            pa.calculated_end_date, pa.pending_hours, pa.ready_to_start_date
                        ) for pa in plan_assignments
                    ])
                
                plan.assignments = plan_assignments
                conn.commit()
                
                logger.info(f"Plan guardado exitosamente: ID={plan.id}, checksum={plan.checksum[:8]}...")
                return plan
                
    except Exception as e:
        logger.error(f"Error guardando plan: {e}")
        raise PlansError(f"No se pudo guardar el plan: {e}")


def get_active_plan() -> Optional[Plan]:
    """
    Obtiene el plan actualmente activo
    
    Returns:
        Plan activo o None si no hay ninguno activo
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, description, checksum, created_at, is_active,
                           simulation_date, total_assignments, total_projects
                    FROM plans 
                    WHERE is_active = true
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                logging.info(row)
                if not row:
                    return None
                
                plan = Plan(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    checksum=row['checksum'],
                    created_at=row['created_at'],
                    is_active=row['is_active'],
                    simulation_date=row['simulation_date'],
                    total_assignments=row['total_assignments'],
                    total_projects=row['total_projects']
                )
                
                # Cargar asignaciones del plan
                plan.assignments = _load_plan_assignments(cursor, plan.id)
                return plan
                
    except Exception as e:
        logger.error(f"Error obteniendo plan activo: {e}")
        return None


def get_plan_by_id(plan_id: int) -> Optional[Plan]:
    """
    Obtiene un plan por su ID
    
    Args:
        plan_id: ID del plan
    
    Returns:
        Plan encontrado o None si no existe
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, description, checksum, created_at, is_active,
                           simulation_date, total_assignments, total_projects
                    FROM plans 
                    WHERE id = %s
                """, (plan_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                plan = Plan(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    checksum=row['checksum'],
                    created_at=row['created_at'],
                    is_active=row['is_active'],
                    simulation_date=row['simulation_date'],
                    total_assignments=row['total_assignments'],
                    total_projects=row['total_projects']
                )
                
                # Cargar asignaciones del plan
                plan.assignments = _load_plan_assignments(cursor, plan.id)
                
                return plan
                
    except Exception as e:
        logger.error(f"Error obteniendo plan {plan_id}: {e}")
        return None


def compare_plans(result: ScheduleResult, active_plan: Optional[Plan] = None) -> Dict[str, Any]:
    """
    Compara un resultado de simulación con el plan activo
    
    Args:
        result: Resultado de simulación a comparar
        active_plan: Plan activo (se obtiene automáticamente si no se proporciona)
    
    Returns:
        Diccionario con información de la comparación:
        - has_changes: bool - Si hay cambios
        - new_checksum: str - Checksum del nuevo resultado
        - active_checksum: str - Checksum del plan activo (si existe)
        - changes_detected: List[str] - Lista de cambios detectados
    """
    try:
        # Obtener plan activo si no se proporciona
        if active_plan is None:
            active_plan = get_active_plan()
        
        # Crear plan temporal para calcular checksum
        temp_plan = Plan.from_schedule_result(result)
        new_checksum = temp_plan.checksum
        
        comparison = {
            'has_changes': True,
            'new_checksum': new_checksum,
            'active_checksum': None,
            'changes_detected': []
        }
        
        if active_plan is None:
            comparison['changes_detected'].append("No hay plan activo para comparar")
            return comparison
        
        comparison['active_checksum'] = active_plan.checksum
        
        # Comparar checksums
        if new_checksum == active_plan.checksum:
            comparison['has_changes'] = False
            comparison['changes_detected'].append("Sin cambios detectados")
        else:
            comparison['changes_detected'].append("Cambios detectados en el cronograma")
            
            # Análisis detallado de cambios (opcional)
            _analyze_detailed_changes(result, active_plan, comparison)
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparando planes: {e}")
        return {
            'has_changes': True,
            'new_checksum': '',
            'active_checksum': None,
            'changes_detected': [f"Error en comparación: {e}"]
        }


def set_active_plan(plan_id: int) -> bool:
    """
    Marca un plan como activo (desactiva otros)
    
    Args:
        plan_id: ID del plan a activar
    
    Returns:
        True si se activó correctamente, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Desactivar todos los planes
                cursor.execute("UPDATE plans SET is_active = false WHERE is_active = true")
                
                # Activar el plan especificado
                cursor.execute("""
                    UPDATE plans SET is_active = true 
                    WHERE id = %s
                """, (plan_id,))
                
                if cursor.rowcount == 0:
                    logger.warning(f"Plan {plan_id} no encontrado")
                    return False
                
                conn.commit()
                logger.info(f"Plan {plan_id} marcado como activo")
                return True
                
    except Exception as e:
        logger.error(f"Error activando plan {plan_id}: {e}")
        return False


def list_plans(limit: int = 50) -> List[Plan]:
    """
    Lista todos los planes ordenados por fecha de creación (más recientes primero)
    
    Args:
        limit: Número máximo de planes a retornar
    
    Returns:
        Lista de planes (sin asignaciones cargadas para eficiencia)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, description, checksum, created_at, is_active,
                           simulation_date, total_assignments, total_projects
                    FROM plans 
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
                
                plans = []
                for row in cursor.fetchall():
                    plan = Plan(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        checksum=row['checksum'],
                        created_at=row['created_at'],
                        is_active=row['is_active'],
                        simulation_date=row['simulation_date'],
                        total_assignments=row['total_assignments'],
                        total_projects=row['total_projects']
                    )
                    plans.append(plan)
                
                return plans
                
    except Exception as e:
        logger.error(f"Error listando planes: {e}")
        return []


def delete_plan(plan_id: int) -> bool:
    """
    Elimina un plan y todas sus asignaciones
    
    Args:
        plan_id: ID del plan a eliminar
    
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Las asignaciones se eliminan automáticamente por CASCADE
                cursor.execute("DELETE FROM plans WHERE id = %s", (plan_id,))
                
                if cursor.rowcount == 0:
                    logger.warning(f"Plan {plan_id} no encontrado para eliminar")
                    return False
                
                conn.commit()
                logger.info(f"Plan {plan_id} eliminado exitosamente")
                return True
                
    except Exception as e:
        logger.error(f"Error eliminando plan {plan_id}: {e}")
        return False


def _load_plan_assignments(cursor, plan_id: int) -> List[PlanAssignment]:
    """Carga las asignaciones de un plan (función auxiliar)"""
    cursor.execute("""
        SELECT id, plan_id, assignment_id, project_id, project_name, project_priority,
               priority_order, team_id, team_name, tier, devs_assigned, estimated_hours,
               calculated_start_date, calculated_end_date, pending_hours,
               ready_to_start_date
        FROM plan_assignments 
        WHERE plan_id = %s
        ORDER BY calculated_start_date, COALESCE(priority_order, project_priority), assignment_id
    """, (plan_id,))
    
    assignments = []
    for row in cursor.fetchall():
        assignment = PlanAssignment(
            id=row['id'],
            plan_id=row['plan_id'],
            assignment_id=row['assignment_id'],
            project_id=row['project_id'],
            project_name=row['project_name'],
            project_priority=row['project_priority'],
            priority_order=row['priority_order'],
            team_id=row['team_id'],
            team_name=row['team_name'],
            tier=row['tier'],
            devs_assigned=row['devs_assigned'],
            estimated_hours=row['estimated_hours'],
            calculated_start_date=row['calculated_start_date'],
            calculated_end_date=row['calculated_end_date'],
            pending_hours=row['pending_hours'],
            ready_to_start_date=row['ready_to_start_date']
        )
        assignments.append(assignment)
    
    return assignments


def _analyze_detailed_changes(result: ScheduleResult, active_plan: Plan, comparison: Dict[str, Any]):
    """Analiza cambios detallados entre resultado y plan activo (función auxiliar)"""
    try:
        # Comparar número de asignaciones
        if len(result.assignments) != active_plan.total_assignments:
            comparison['changes_detected'].append(
                f"Número de asignaciones cambió: {active_plan.total_assignments} → {len(result.assignments)}"
            )
        
        # Comparar número de proyectos
        new_projects = len(set(a.project_id for a in result.assignments))
        if new_projects != active_plan.total_projects:
            comparison['changes_detected'].append(
                f"Número de proyectos cambió: {active_plan.total_projects} → {new_projects}"
            )
        
        # Análisis más detallado podría incluir:
        # - Fechas de inicio/fin específicas que cambiaron
        # - Proyectos que se agregaron/removieron
        # - Cambios en asignaciones de equipos
        
    except Exception as e:
        logger.warning(f"Error en análisis detallado de cambios: {e}")
        comparison['changes_detected'].append("Error analizando cambios detallados")


def apply_plan_priorities(plan_id: int) -> bool:
    """
    Aplica las prioridades de un plan a los proyectos activos en la base de datos
    
    Args:
        plan_id: ID del plan cuyas prioridades se aplicarán
    
    Returns:
        True si se aplicaron correctamente, False en caso contrario
    """
    try:
        plan = get_plan_by_id(plan_id)
        if not plan:
            logger.error(f"Plan {plan_id} no encontrado")
            return False
        
        # Extraer prioridades únicas por proyecto del plan
        project_priorities = {}
        for assignment in plan.assignments:
            if assignment.priority_order is not None:
                project_priorities[assignment.project_id] = assignment.priority_order
            else:
                project_priorities[assignment.project_id] = assignment.project_priority
        
        if not project_priorities:
            logger.warning(f"Plan {plan_id} no tiene prioridades para aplicar")
            return True
        
        # Aplicar prioridades a la tabla de proyectos
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                for project_id, priority in project_priorities.items():
                    cursor.execute("""
                        UPDATE projects 
                        SET priority = %s 
                        WHERE id = %s AND active = true
                    """, (priority, project_id))
                
                conn.commit()
                logger.info(f"Prioridades del plan {plan_id} aplicadas a {len(project_priorities)} proyectos")
                return True
                
    except Exception as e:
        logger.error(f"Error aplicando prioridades del plan {plan_id}: {e}")
        return False


def activate_plan(plan_id: int) -> bool:
    """
    Activa un plan y aplica sus prioridades a los proyectos
    
    Args:
        plan_id: ID del plan a activar
    
    Returns:
        True si se activó correctamente, False en caso contrario
    """
    try:
        # Primero marcar el plan como activo
        if not set_active_plan(plan_id):
            return False
        
        # Luego aplicar sus prioridades
        if not apply_plan_priorities(plan_id):
            logger.warning(f"Plan {plan_id} activado pero no se pudieron aplicar las prioridades")
            return False
        
        logger.info(f"Plan {plan_id} activado exitosamente con prioridades aplicadas")
        return True
        
    except Exception as e:
        logger.error(f"Error activando plan {plan_id}: {e}")
        return False


def deactivate_plan(plan_id: int) -> bool:
    """
    Desactiva un plan específico
    
    Args:
        plan_id: ID del plan a desactivar
    
    Returns:
        True si se desactivó correctamente, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE plans SET is_active = false 
                    WHERE id = %s
                """, (plan_id,))
                
                if cursor.rowcount == 0:
                    logger.warning(f"Plan {plan_id} no encontrado para desactivar")
                    return False
                
                conn.commit()
                logger.info(f"Plan {plan_id} desactivado exitosamente")
                return True
                
    except Exception as e:
        logger.error(f"Error desactivando plan {plan_id}: {e}")
        return False


def get_plan_priorities(plan_id: int) -> Dict[int, int]:
    """
    Obtiene las prioridades específicas de un plan
    
    Args:
        plan_id: ID del plan
    
    Returns:
        Diccionario {project_id: priority_order}
    """
    try:
        plan = get_plan_by_id(plan_id)
        if not plan:
            return {}
        
        priorities = {}
        for assignment in plan.assignments:
            if assignment.priority_order is not None:
                priorities[assignment.project_id] = assignment.priority_order
            else:
                priorities[assignment.project_id] = assignment.project_priority
        
        return priorities
        
    except Exception as e:
        logger.error(f"Error obteniendo prioridades del plan {plan_id}: {e}")
        return {}