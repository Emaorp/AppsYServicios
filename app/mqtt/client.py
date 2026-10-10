"""Cliente MQTT: se conecta al broker, se suscribe al tópico y entrega cada mensaje
al procesador. Corre en un hilo aparte para no bloquear la API.
"""

import logging
import os
import re
from pathlib import Path

import paho.mqtt.client as paho

from app.database.connection import SessionLocal
from app.mqtt.procesador import procesar_mensaje

logger = logging.getLogger("iot.mqtt")


def _codigo_desde_topico(topico: str) -> str | None:
    """iot/sensors/TEST-001/data -> TEST-001. Con comodines (+ o #) devuelve None."""
    coincidencia = re.fullmatch(r"iot/sensors/([^/+#]+)/data", topico)
    return coincidencia.group(1) if coincidencia else None


def _configurar_registro_en_archivo():
    """Además de la consola, guarda el registro en un .txt (sirve como evidencia)."""
    ruta = Path(os.getenv("MQTT_REGISTRO_ARCHIVO", "evidencias/registro_mqtt.txt"))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta_abs = str(ruta.resolve())
    for h in logger.handlers:
        if getattr(h, "baseFilename", None) == ruta_abs:
            return
    manejador = logging.FileHandler(ruta, encoding="utf-8")
    manejador.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(manejador)
    logger.setLevel(logging.INFO)


class ConsumidorMqtt:
    def __init__(self, broker: str, puerto: int, topico: str, usuario=None, password=None, keepalive=60):
        self.broker = broker
        self.puerto = puerto
        self.topico = topico
        self.keepalive = keepalive
        self.codigo_esperado = _codigo_desde_topico(topico)
        self.conectado = False

        self.cliente = paho.Client(paho.CallbackAPIVersion.VERSION2)
        if usuario:
            self.cliente.username_pw_set(usuario, password or "")
        self.cliente.on_connect = self._on_connect
        self.cliente.on_disconnect = self._on_disconnect
        self.cliente.on_message = self._on_message

    # --- callbacks -------------------------------------------------------
    def _on_connect(self, cliente, userdata, flags, reason_code, properties=None):
        if reason_code.is_failure:
            logger.error("Error de conexión MQTT: %s", reason_code)
            return
        self.conectado = True
        logger.info("Conectado al broker %s:%s", self.broker, self.puerto)
        # Se suscribe aquí para que también se re-suscriba si la conexión se reinicia.
        cliente.subscribe(self.topico)
        logger.info("Suscrito al tópico: %s", self.topico)

    def _on_disconnect(self, cliente, userdata, flags, reason_code, properties=None):
        self.conectado = False
        logger.warning("Desconectado del broker (%s). Se reintentará automáticamente.", reason_code)

    def _on_message(self, cliente, userdata, mensaje):
        logger.info("RECIBIDO | tópico=%s | payload=%s", mensaje.topic, mensaje.payload.decode("utf-8", "replace"))
        # Una sesión de base de datos nueva por mensaje (este código corre en otro hilo).
        with SessionLocal() as db:
            try:
                procesar_mensaje(db, mensaje.payload, codigo_esperado=self.codigo_esperado)
            except Exception:  # noqa: BLE001 - un mensaje malo nunca debe tumbar el consumidor
                logger.exception("Error inesperado procesando el mensaje")

    # --- ciclo de vida ---------------------------------------------------
    def iniciar(self):
        _configurar_registro_en_archivo()
        logger.info("Iniciando consumidor MQTT -> %s:%s (tópico %s)", self.broker, self.puerto, self.topico)
        # connect_async: si el broker no responde, la API arranca igual y se reintenta.
        self.cliente.connect_async(self.broker, self.puerto, self.keepalive)
        self.cliente.loop_start()

    def detener(self):
        self.cliente.loop_stop()
        self.cliente.disconnect()
        logger.info("Consumidor MQTT detenido")


def crear_consumidor_desde_entorno() -> ConsumidorMqtt | None:
    """Crea el consumidor con las variables MQTT_* del .env (None si está desactivado)."""
    if os.getenv("MQTT_ENABLED", "true").lower() in ("0", "false", "no"):
        return None
    broker = os.getenv("MQTT_BROKER")
    if not broker:
        logger.error("Falta MQTT_BROKER en el .env: el consumidor MQTT no se iniciará")
        return None
    return ConsumidorMqtt(
        broker=broker,
        puerto=int(os.getenv("MQTT_PORT", "1883")),
        topico=os.getenv("MQTT_TOPIC", "iot/sensors/TEST-001/data"),
        usuario=os.getenv("MQTT_USERNAME"),
        password=os.getenv("MQTT_PASSWORD"),
        keepalive=int(os.getenv("MQTT_KEEPALIVE", "60")),
    )
