from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.utils.tiempo import a_hora_colombia


class SensorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    categoria: str
    ubicacion: str
    activo: bool
    fecha_registro: str  # hora local de Colombia

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def _a_hora_local(cls, valor):
        return a_hora_colombia(valor) if isinstance(valor, datetime) else valor
