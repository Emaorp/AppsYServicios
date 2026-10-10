"""Evidencias 3 a 7: mensajes MQTT inválidos son rechazados y NO se guardan.

Usa la base real para leer el sensor y su configuración, pero trabaja en modo
simulación (dry_run=True): jamás inserta nada en PostgreSQL.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python -m pruebas.probar_validaciones --sensor TEST-001
Genera: evidencias/validaciones_mqtt.txt
"""

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.database.connection import SessionLocal
from app.mqtt.procesador import procesar_mensaje

logging.getLogger("iot.mqtt").setLevel(logging.CRITICAL)  # el detalle sale en este reporte


def construir_casos(codigo: str, magnitud: str, unidad: str, minimo: float, maximo: float):
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    medio = round((minimo + maximo) / 2, 2)

    def msg(sensor_id=codigo, timestamp=ahora, medidas=None):
        medidas = medidas if medidas is not None else {magnitud: {"value": medio, "unit": unidad}}
        return json.dumps({"sensor_id": sensor_id, "timestamp": timestamp, "measurements": medidas})

    return [
        ("Control: mensaje válido (solo simulación, no se guarda)", "debe ser aceptado", msg(), True, True),
        # Sin comprobar el tópico, para que la causa del rechazo sea que el sensor no existe en la BD.
        ("3. Sensor inexistente", "debe ser rechazado", msg(sensor_id="SENSOR-INEXISTENTE"), False, False),
        ("4. Unidad incorrecta", "debe ser rechazado",
         msg(medidas={magnitud: {"value": medio, "unit": "UNIDAD-FALSA"}}), False, True),
        ("5. Tipo de dato incorrecto (valor como texto)", "debe ser rechazado",
         msg(medidas={magnitud: {"value": "veinticuatro", "unit": unidad}}), False, True),
        ("6. Magnitud incorrecta", "debe ser rechazado",
         msg(medidas={"magnitud_inexistente": {"value": 1, "unit": unidad}}), False, True),
        ("7. Timestamp inválido", "debe ser rechazado", msg(timestamp="ayer por la tarde"), False, True),
        ("Extra: valor fuera de rango", "debe ser rechazado",
         msg(medidas={magnitud: {"value": maximo + 1000, "unit": unidad}}), False, True),
        ("Extra: JSON dañado", "debe ser rechazado", "{esto no es json", False, True),
        ("Extra: sensor distinto al del tópico asignado", "debe ser rechazado",
         msg(sensor_id="OTRO-SENSOR"), False, True),
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sensor", required=True, help="código del sensor, ej. TEST-001")
    args = parser.parse_args()

    with SessionLocal() as db:
        sensor = crud_sensor.obtener_por_codigo(db, args.sensor)
        if sensor is None:
            raise SystemExit(f"El sensor '{args.sensor}' no existe en la base. Revisa el código.")
        magnitudes = crud_sensor_magnitud.listar_por_sensor(db, sensor.id)
        if not magnitudes:
            raise SystemExit("El sensor no tiene magnitudes configuradas.")
        m = magnitudes[0]
        casos = construir_casos(sensor.codigo, m.magnitud, m.unidad, float(m.valor_minimo), float(m.valor_maximo))

        lineas = [
            "PRUEBAS DE VALIDACIÓN DE MENSAJES MQTT",
            f"Fecha de ejecución: {datetime.now().isoformat(timespec='seconds')}",
            f"Sensor usado como referencia: {sensor.codigo} (magnitud {m.magnitud}, unidad {m.unidad})",
            "Modo: simulación (dry_run). Ninguna de estas pruebas escribe en la base de datos.",
            "Lógica: app/mqtt/procesador.py -> procesar_mensaje()",
            "=" * 78,
        ]
        for titulo, esperado, crudo, debe_aceptar, usar_topico in casos:
            esperado_topico = sensor.codigo if usar_topico else None
            resultado = procesar_mensaje(db, crudo, codigo_esperado=esperado_topico, dry_run=True)
            correcto = resultado.aceptado == debe_aceptar
            lineas += [
                f"\n{titulo}",
                f"  Entrada  : {crudo}",
                f"  Esperado : {esperado}",
                f"  Obtenido : {'ACEPTADO' if resultado.aceptado else 'RECHAZADO'} -> {resultado.motivo}",
                f"  Resultado: {'OK' if correcto else 'FALLÓ (revisar)'}",
            ]

    texto = "\n".join(lineas)
    print(texto)
    ruta = Path("evidencias/validaciones_mqtt.txt")
    ruta.parent.mkdir(exist_ok=True)
    ruta.write_text(texto + "\n", encoding="utf-8")
    print(f"\nEvidencia guardada en {ruta}")


if __name__ == "__main__":
    main()
