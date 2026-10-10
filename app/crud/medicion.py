"""Operaciones sobre mediciones: crear (desde MQTT) y consultar. No hay update ni delete."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.medicion import Medicion
from app.models.sensor_magnitud import SensorMagnitud


def _con_relaciones():
    return joinedload(Medicion.sensor_magnitud).joinedload(SensorMagnitud.sensor)


def crear_lote(db: Session, registros: list[dict]) -> list[Medicion]:
    """Guarda todas las mediciones de un mensaje en UNA sola transacción.

    Si algo falla no se guarda ninguna (todo o nada).
    """
    objetos = [Medicion(**registro) for registro in registros]
    db.add_all(objetos)
    db.commit()
    return objetos


def obtener(db: Session, medicion_id: int) -> Medicion | None:
    consulta = select(Medicion).options(_con_relaciones()).where(Medicion.id == medicion_id)
    return db.scalar(consulta)


def listar_por_sensor(
    db: Session,
    sensor_id: int,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int = 100,
) -> list[Medicion]:
    """Histórico de un sensor, de la más reciente a la más antigua.

    Los filtros se pueden combinar. `limit` devuelve las últimas N.
    """
    consulta = (
        select(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .options(_con_relaciones())
        .where(SensorMagnitud.sensor_id == sensor_id)
    )
    if magnitud is not None:
        consulta = consulta.where(SensorMagnitud.magnitud == magnitud)
    if desde is not None:
        consulta = consulta.where(Medicion.timestamp_utc >= desde)
    if hasta is not None:
        consulta = consulta.where(Medicion.timestamp_utc <= hasta)

    consulta = consulta.order_by(Medicion.timestamp_utc.desc(), Medicion.id.desc()).limit(limit)
    return list(db.scalars(consulta))


def ultima_por_sensor(db: Session, sensor_id: int) -> Medicion | None:
    resultado = listar_por_sensor(db, sensor_id, limit=1)
    return resultado[0] if resultado else None
