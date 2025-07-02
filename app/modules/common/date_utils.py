"""
Utilidades de fecha y tiempo consolidadas para APE
Elimina duplicación entre scheduler.py y monitoring.py
"""
from datetime import date
import pandas as pd
from pandas.tseries.offsets import BusinessDay
import logging
from .constants import MIN_DATE, MAX_DATE

logger = logging.getLogger(__name__)


def validate_date_range(target_date: date, context: str = "") -> date:
    """Valida que una fecha esté en el rango válido de Python"""
    if target_date < MIN_DATE:
        logger.warning(f"Fecha {target_date} fuera de rango mínimo en {context}. Ajustando a {MIN_DATE}")
        return MIN_DATE
    if target_date > MAX_DATE:
        logger.error(f"Fecha {target_date} fuera de rango máximo en {context}. Ajustando a {MAX_DATE}")
        return MAX_DATE
    return target_date


def safe_business_day_calculation(base_date: date, days_offset: int, context: str = "") -> date:
    """Calcula días hábiles de manera segura, evitando fechas fuera de rango"""
    try:
        # Validar fecha base
        safe_base_date = validate_date_range(base_date, f"{context} - fecha base")
        
        # Usar pandas para cálculo de días hábiles
        result_date = pd.Timestamp(safe_base_date) + BusinessDay(days_offset)
        result_date = result_date.date()
        
        # Validar resultado
        return validate_date_range(result_date, f"{context} - resultado")
        
    except Exception as e:
        logger.error(f"Error en cálculo de días hábiles en {context}: {e}")
        # Fallback: usar fecha base si hay error
        return validate_date_range(base_date, f"{context} - fallback")


def add_business_days(start_date: date, days: int) -> date:
    """Suma días hábiles a una fecha"""
    return safe_business_day_calculation(start_date, days, "add_business_days")


def next_business_day(current_date: date) -> date:
    """Obtiene el siguiente día hábil"""
    return add_business_days(current_date, 1)


def calculate_business_days(start_date: date, end_date: date) -> int:
    """Calcula días hábiles entre dos fechas usando pandas"""
    try:
        # Validar fechas
        safe_start = validate_date_range(start_date, "calculate_business_days - start")
        safe_end = validate_date_range(end_date, "calculate_business_days - end")
        
        # Usar pandas para cálculo preciso
        business_days = pd.bdate_range(safe_start, safe_end)
        return len(business_days) - 1  # Excluir el día de inicio
        
    except Exception as e:
        logger.error(f"Error calculando días hábiles: {e}")
        return 0