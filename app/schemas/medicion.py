"""Schemas de mediciones.

Hay dos grupos:
- Payload MQTT (entrada): valida estructura, campos obligatorios, tipos y timestamp.
- MedicionResponse (salida de la API): con la hora convertida a Colombia.
"""

import math
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, field_validator

from app.utils.tiempo import a_hora_colombia


# ---------------------------------------------------------------------------
# Entrada: mensaje MQTT
# ---------------------------------------------------------------------------
class MagnitudPayload(BaseModel):
    """Una magnitud dentro de "measurements": {"value": 24.6, "unit": "C"}."""

    # Estricto: "24.6" (texto) o true NO son números válidos.
    value: StrictInt | StrictFloat
    unit: StrictStr = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def _numero_finito(cls, valor):
        if not math.isfinite(valor):
            raise ValueError("el valor debe ser un número finito")
        return valor


class MqttPayload(BaseModel):
    """Mensaje completo publicado por el sensor."""

    sensor_id: StrictStr = Field(min_length=1)
    timestamp: datetime
    measurements: dict[str, MagnitudPayload] = Field(min_length=1)

    @field_validator("timestamp", mode="before")
    @classmethod
    def _timestamp_debe_ser_texto(cls, valor):
        # Evita que un número (ej. 12345) sea interpretado como fecha.
        if not isinstance(valor, str):
            raise ValueError("el timestamp debe ser texto ISO 8601, por ejemplo 2026-10-07T16:25:30Z")
        return valor

    @field_validator("timestamp")
    @classmethod
    def _timestamp_con_zona(cls, valor: datetime):
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError("el timestamp debe incluir zona horaria (UTC), por ejemplo terminar en Z")
        return valor.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Salida: respuestas de la API
# ---------------------------------------------------------------------------
class MedicionResponse(BaseModel):
    id: int
    sensor_magnitud_id: int
    sensor_codigo: str
    magnitud: str
    unidad: str
    valor: float
    timestamp_local: str  # timestamp_utc convertido a hora de Colombia
    fecha_recepcion_local: str


def medicion_a_respuesta(medicion) -> MedicionResponse:
    """Convierte una fila ORM de Medicion en la respuesta de la API."""
    magnitud = medicion.sensor_magnitud
    return MedicionResponse(
        id=medicion.id,
        sensor_magnitud_id=medicion.sensor_magnitud_id,
        sensor_codigo=magnitud.sensor.codigo,
        magnitud=magnitud.magnitud,
        unidad=magnitud.unidad,
        valor=float(medicion.valor),
        timestamp_local=a_hora_colombia(medicion.timestamp_utc),
        fecha_recepcion_local=a_hora_colombia(medicion.fecha_recepcion),
    )
