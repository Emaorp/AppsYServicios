from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.database.connection import get_db
from app.schemas.sensor_magnitud import SensorMagnitudResponse

router = APIRouter(tags=["Magnitudes"])


@router.get("/sensores/{sensor_id}/magnitudes", response_model=list[SensorMagnitudResponse])
def listar_magnitudes_del_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Magnitudes (con unidad y rango válido) que mide un sensor."""
    if crud_sensor.obtener(db, sensor_id) is None:
        raise HTTPException(status_code=404, detail=f"No existe el sensor con id {sensor_id}")
    return crud_sensor_magnitud.listar_por_sensor(db, sensor_id)


@router.get("/sensor-magnitudes/{sensor_magnitud_id}", response_model=SensorMagnitudResponse)
def obtener_sensor_magnitud(sensor_magnitud_id: int, db: Session = Depends(get_db)):
    """Obtiene una relación sensor-magnitud por su id."""
    relacion = crud_sensor_magnitud.obtener(db, sensor_magnitud_id)
    if relacion is None:
        raise HTTPException(
            status_code=404, detail=f"No existe la relación sensor-magnitud con id {sensor_magnitud_id}"
        )
    return relacion
