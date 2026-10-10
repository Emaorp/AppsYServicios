from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import sensor as crud_sensor
from app.database.connection import get_db
from app.schemas.sensor import SensorResponse

router = APIRouter(prefix="/sensores", tags=["Sensores"])


@router.get("", response_model=list[SensorResponse])
def listar_sensores(db: Session = Depends(get_db)):
    """Lista todos los sensores del catálogo."""
    return crud_sensor.listar(db)


# Esta ruta va ANTES de /{sensor_id} para que "por-codigo" no se confunda con un id.
@router.get("/por-codigo/{codigo}", response_model=SensorResponse)
def obtener_sensor_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """Busca un sensor por su código (el sensor_id que llega por MQTT)."""
    sensor = crud_sensor.obtener_por_codigo(db, codigo)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe un sensor con código '{codigo}'")
    return sensor


@router.get("/{sensor_id}", response_model=SensorResponse)
def obtener_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Obtiene un sensor por su id numérico."""
    sensor = crud_sensor.obtener(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe el sensor con id {sensor_id}")
    return sensor
