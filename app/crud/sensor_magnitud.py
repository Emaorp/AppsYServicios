"""Operaciones sobre sensor_magnitudes. Solo lectura."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor_magnitud import SensorMagnitud


def listar_por_sensor(db: Session, sensor_id: int) -> list[SensorMagnitud]:
    consulta = (
        select(SensorMagnitud)
        .where(SensorMagnitud.sensor_id == sensor_id)
        .order_by(SensorMagnitud.id)
    )
    return list(db.scalars(consulta))


def obtener(db: Session, sensor_magnitud_id: int) -> SensorMagnitud | None:
    return db.get(SensorMagnitud, sensor_magnitud_id)


def mapa_por_nombre(db: Session, sensor_id: int) -> dict[str, SensorMagnitud]:
    """Devuelve {nombre_de_magnitud: SensorMagnitud} para validar mensajes MQTT."""
    return {m.magnitud: m for m in listar_por_sensor(db, sensor_id)}
