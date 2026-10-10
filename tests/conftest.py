"""Pruebas automáticas con SQLite en archivo temporal (no tocan PostgreSQL)."""

import os
import tempfile
from decimal import Decimal

# La URL de prueba debe definirse ANTES de importar la aplicación.
_ruta_db = os.path.join(tempfile.mkdtemp(), "prueba.sqlite")
os.environ["DATABASE_URL"] = f"sqlite:///{_ruta_db}"
os.environ["MQTT_ENABLED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database.connection import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Medicion, Sensor, SensorMagnitud  # noqa: E402


@pytest.fixture(autouse=True)
def base_limpia():
    """Antes de cada prueba: tablas nuevas con un catálogo pequeño."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        s1 = Sensor(id=1, codigo="TEST-001", nombre="Sensor de prueba", categoria="AMBIENTE",
                    ubicacion="Laboratorio", activo=True)
        s2 = Sensor(id=2, codigo="OFF-002", nombre="Sensor apagado", categoria="AIRE",
                    ubicacion="Bodega", activo=False)
        db.add_all([s1, s2])
        db.flush()
        db.add_all([
            SensorMagnitud(id=1, sensor_id=1, magnitud="temperature", unidad="C",
                           valor_minimo=Decimal("-10"), valor_maximo=Decimal("60")),
            SensorMagnitud(id=2, sensor_id=1, magnitud="humidity", unidad="%",
                           valor_minimo=Decimal("0"), valor_maximo=Decimal("100")),
            SensorMagnitud(id=3, sensor_id=2, magnitud="pm25", unidad="ug/m3",
                           valor_minimo=Decimal("0"), valor_maximo=Decimal("500")),
        ])
        db.commit()
    yield


@pytest.fixture
def db():
    with SessionLocal() as sesion:
        yield sesion


@pytest.fixture
def cliente():
    with TestClient(app) as c:
        yield c


def contar_mediciones() -> int:
    with SessionLocal() as sesion:
        return sesion.query(Medicion).count()
