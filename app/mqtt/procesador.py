"""Procesamiento de un mensaje MQTT: validar y, si todo es válido, guardar.

Pasos (en este orden):
1. JSON válido.                                   -> Pydantic (estructura, tipos, timestamp)
2. El sensor del mensaje es el del tópico.        -> evita tocar datos de otros grupos
3. El sensor existe y está activo.                -> ORM
4. Cada magnitud pertenece al sensor.             -> ORM
5. Cada unidad coincide con la configurada.       -> ORM
6. Cada valor está dentro del rango configurado.  -> ORM
7. Solo si TODAS las magnitudes son válidas se guardan, cada una como un registro
   independiente y todas con el mismo timestamp_utc.
"""

import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.schemas.medicion import MqttPayload

logger = logging.getLogger("iot.mqtt")


@dataclass
class Resultado:
    aceptado: bool
    motivo: str
    ids_guardados: list[int] = field(default_factory=list)


def _rechazar(motivo: str, crudo) -> Resultado:
    """Los errores MQTT se manejan internamente: se registran, no se guardan."""
    logger.warning("RECHAZADO | %s | mensaje=%s", motivo, crudo)
    return Resultado(False, motivo)


def _texto_errores(error: ValidationError) -> str:
    partes = []
    for e in error.errors():
        ubicacion = ".".join(str(p) for p in e["loc"]) or "mensaje"
        partes.append(f"{ubicacion}: {e['msg']}")
    return "; ".join(partes)


def procesar_mensaje(
    db: Session,
    crudo: bytes | str,
    codigo_esperado: str | None = None,
    dry_run: bool = False,
) -> Resultado:
    """Valida un mensaje y lo guarda si es válido.

    codigo_esperado: código del sensor del tópico suscrito (None = no comprobar).
    dry_run: valida todo pero NO guarda (se usa en las pruebas de rechazo).
    """
    # 1. JSON + estructura (Pydantic)
    try:
        texto = crudo.decode("utf-8") if isinstance(crudo, bytes) else crudo
        datos = json.loads(texto)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return _rechazar(f"JSON inválido ({error})", crudo)

    try:
        payload = MqttPayload.model_validate(datos)
    except ValidationError as error:
        return _rechazar(f"Estructura inválida: {_texto_errores(error)}", crudo)

    # 2. El mensaje debe ser del sensor asignado
    if codigo_esperado is not None and payload.sensor_id != codigo_esperado:
        return _rechazar(
            f"sensor_id '{payload.sensor_id}' no corresponde al sensor del tópico '{codigo_esperado}'",
            crudo,
        )

    # 3. Sensor existente y activo (ORM)
    sensor = crud_sensor.obtener_por_codigo(db, payload.sensor_id)
    if sensor is None:
        return _rechazar(f"Sensor inexistente: '{payload.sensor_id}'", crudo)
    if not sensor.activo:
        return _rechazar(f"Sensor inactivo: '{payload.sensor_id}'", crudo)

    # 4-6. Magnitud, unidad y rango de CADA magnitud (ORM)
    configuradas = crud_sensor_magnitud.mapa_por_nombre(db, sensor.id)
    registros = []
    for nombre, medida in payload.measurements.items():
        config = configuradas.get(nombre)
        if config is None:
            return _rechazar(f"Magnitud '{nombre}' no pertenece al sensor '{sensor.codigo}'", crudo)
        if medida.unit != config.unidad:
            return _rechazar(
                f"Unidad incorrecta en '{nombre}': recibida '{medida.unit}', esperada '{config.unidad}'",
                crudo,
            )
        valor = Decimal(str(medida.value))
        if not (config.valor_minimo <= valor <= config.valor_maximo):
            return _rechazar(
                f"Valor fuera de rango en '{nombre}': {valor} no está entre "
                f"{config.valor_minimo} y {config.valor_maximo}",
                crudo,
            )
        registros.append(
            {
                "sensor_magnitud_id": config.id,
                "valor": valor,
                "timestamp_utc": payload.timestamp,  # mismo timestamp para todo el mensaje
            }
        )

    # 7. Todo válido -> guardar (o solo simular)
    if dry_run:
        return Resultado(True, f"Válido (simulación, no se guardó): {len(registros)} magnitud(es)")

    try:
        guardadas = crud_medicion.crear_lote(db, registros)
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("ERROR BD | no se pudo guardar el mensaje: %s", error)
        return Resultado(False, "Error de base de datos al guardar")

    ids = [m.id for m in guardadas]
    logger.info(
        "ACEPTADO | sensor=%s | timestamp_utc=%s | %d magnitud(es) | ids=%s",
        sensor.codigo,
        payload.timestamp.isoformat(),
        len(ids),
        ids,
    )
    return Resultado(True, f"Guardadas {len(ids)} medición(es)", ids)
