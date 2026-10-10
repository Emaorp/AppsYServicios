from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.database.connection import get_db
from app.schemas.medicion import MedicionResponse, medicion_a_respuesta
from app.utils.tiempo import local_a_utc

router = APIRouter(tags=["Mediciones"])


def _sensor_o_404(db: Session, sensor_id: int):
    sensor = crud_sensor.obtener(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe el sensor con id {sensor_id}")
    return sensor


@router.get("/mediciones/{medicion_id}", response_model=MedicionResponse)
def obtener_medicion(medicion_id: int, db: Session = Depends(get_db)):
    """Obtiene una medición por su id."""
    medicion = crud_medicion.obtener(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail=f"No existe la medición con id {medicion_id}")
    return medicion_a_respuesta(medicion)


@router.get("/sensores/{sensor_id}/mediciones", response_model=list[MedicionResponse])
def listar_mediciones_del_sensor(
    sensor_id: int,
    magnitud: str | None = Query(None, description="Filtra por magnitud, ej. temperature"),
    desde: datetime | None = Query(None, description="Fecha inicial. Sin zona horaria = hora de Colombia"),
    hasta: datetime | None = Query(None, description="Fecha final. Sin zona horaria = hora de Colombia"),
    limit: int = Query(100, ge=1, le=1000, description="Últimas N mediciones"),
    db: Session = Depends(get_db),
):
    """Histórico del sensor (más reciente primero). Los filtros se pueden combinar."""
    _sensor_o_404(db, sensor_id)

    desde_utc = local_a_utc(desde) if desde else None
    hasta_utc = local_a_utc(hasta) if hasta else None
    if desde_utc and hasta_utc and desde_utc > hasta_utc:
        raise HTTPException(status_code=400, detail="Rango inválido: 'desde' no puede ser mayor que 'hasta'")

    if magnitud is not None and magnitud not in crud_sensor_magnitud.mapa_por_nombre(db, sensor_id):
        raise HTTPException(
            status_code=404, detail=f"El sensor {sensor_id} no tiene la magnitud '{magnitud}'"
        )

    mediciones = crud_medicion.listar_por_sensor(db, sensor_id, magnitud, desde_utc, hasta_utc, limit)
    return [medicion_a_respuesta(m) for m in mediciones]


@router.get("/sensores/{sensor_id}/ultima-medicion", response_model=MedicionResponse)
def ultima_medicion_del_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Medición más reciente del sensor."""
    _sensor_o_404(db, sensor_id)
    medicion = crud_medicion.ultima_por_sensor(db, sensor_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail=f"El sensor {sensor_id} aún no tiene mediciones")
    return medicion_a_respuesta(medicion)
