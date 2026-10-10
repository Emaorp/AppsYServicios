"""Utilidades de zona horaria.

La base guarda todo en UTC. En las respuestas GET se muestra la hora local de
Colombia. Colombia no usa horario de verano, por eso un desfase fijo de -5 h
es siempre correcto.
"""

from datetime import datetime, timedelta, timezone

COLOMBIA = timezone(timedelta(hours=-5), "COT")


def a_utc(fecha: datetime) -> datetime:
    """Convierte a UTC. Si llega sin zona horaria se asume que ya es UTC."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def local_a_utc(fecha: datetime) -> datetime:
    """Convierte a UTC. Si llega sin zona horaria se asume hora de Colombia."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=COLOMBIA).astimezone(timezone.utc)
    return fecha.astimezone(timezone.utc)


def a_hora_colombia(fecha: datetime) -> str:
    """Texto legible y consistente: 2026-10-07 11:25:30 (UTC-05:00)."""
    local = a_utc(fecha).astimezone(COLOMBIA)
    return local.strftime("%Y-%m-%d %H:%M:%S") + " (UTC-05:00)"
