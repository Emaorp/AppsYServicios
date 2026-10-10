"""Operaciones sobre sensores. Solo lectura: el catálogo lo administra el docente."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor import Sensor


def listar(db: Session) -> list[Sensor]:
    return list(db.scalars(select(Sensor).order_by(Sensor.id)))


def obtener(db: Session, sensor_id: int) -> Sensor | None:
    return db.get(Sensor, sensor_id)


def obtener_por_codigo(db: Session, codigo: str) -> Sensor | None:
    return db.scalar(select(Sensor).where(Sensor.codigo == codigo))
