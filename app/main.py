import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api import medicion, sensor, sensor_magnitud
from app.database.connection import SessionLocal
from app.mqtt.client import crear_consumidor_desde_entorno

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Al arrancar la API también arranca el consumidor MQTT; al apagar, lo detiene."""
    consumidor = crear_consumidor_desde_entorno()
    app.state.consumidor_mqtt = consumidor
    if consumidor:
        consumidor.iniciar()
    yield
    if consumidor:
        consumidor.detener()


app = FastAPI(
    title="API IoT - Taller 2",
    description="Adquisición por MQTT, validación y consulta de datos de sensores IoT.",
    lifespan=lifespan,
)

app.include_router(sensor.router)
app.include_router(sensor_magnitud.router)
app.include_router(medicion.router)


@app.get("/", tags=["Estado"])
def raiz():
    return {"mensaje": "API IoT - Taller 2", "docs": "/docs"}


@app.get("/health", tags=["Estado"])
def estado():
    """Comprueba la base de datos y el estado de la conexión MQTT."""
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    consumidor = app.state.consumidor_mqtt
    return {
        "database": "ok",
        "mqtt": ("conectado" if consumidor.conectado else "sin conexión") if consumidor else "desactivado",
        "topico": consumidor.topico if consumidor else None,
    }
