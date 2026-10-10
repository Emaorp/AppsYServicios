"""Evidencia 2: muestra directamente desde PostgreSQL las mediciones guardadas.

Solo hace SELECT (lectura).

Uso:
    python -m pruebas.ver_mediciones --sensor TEST-001
Genera: evidencias/mediciones_en_postgresql.txt
"""

import argparse
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from app.database.connection import SessionLocal
from app.models import Medicion, Sensor, SensorMagnitud
from app.utils.tiempo import a_hora_colombia


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sensor", required=True, help="código del sensor, ej. TEST-001")
    parser.add_argument("--filas", type=int, default=15)
    args = parser.parse_args()

    with SessionLocal() as db:
        base = (
            select(Medicion, SensorMagnitud.magnitud, SensorMagnitud.unidad)
            .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
            .join(Sensor, SensorMagnitud.sensor_id == Sensor.id)
            .where(Sensor.codigo == args.sensor)
        )
        total = db.scalar(select(func.count()).select_from(base.subquery()))
        filas = db.execute(base.order_by(Medicion.timestamp_utc.desc(), Medicion.id.desc()).limit(args.filas)).all()

    lineas = [
        f"MEDICIONES ALMACENADAS EN POSTGRESQL - sensor {args.sensor}",
        f"Consulta realizada: {datetime.now().isoformat(timespec='seconds')}",
        f"Total de mediciones del sensor: {total}",
        f"Últimas {len(filas)}:",
        f"{'id':>8} | {'sensor_magnitud_id':>18} | {'magnitud':<14} | {'valor':>10} | {'unidad':<6} | timestamp_utc (UTC)       | hora Colombia",
    ]
    for m, magnitud, unidad in filas:
        lineas.append(
            f"{m.id:>8} | {m.sensor_magnitud_id:>18} | {magnitud:<14} | {float(m.valor):>10.4f} | {unidad:<6} | "
            f"{m.timestamp_utc.isoformat():<25} | {a_hora_colombia(m.timestamp_utc)}"
        )
    texto = "\n".join(lineas)
    print(texto)
    ruta = Path("evidencias/mediciones_en_postgresql.txt")
    ruta.parent.mkdir(exist_ok=True)
    ruta.write_text(texto + "\n", encoding="utf-8")
    print(f"\nEvidencia guardada en {ruta}")


if __name__ == "__main__":
    main()
