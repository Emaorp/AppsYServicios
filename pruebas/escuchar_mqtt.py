"""Evidencia 1: escucha el tópico y muestra los mensajes SIN guardar nada.

Es una versión del mqtt_example.py del profesor. Sirve para ver el payload real
del sensor (magnitudes, unidades, tipos, timestamp) antes de arrancar la API.

Uso:
    python -m pruebas.escuchar_mqtt
Detener con Ctrl+C.  El tópico y el broker salen del archivo .env
"""

import json
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "iot/sensors/TEST-001/data")


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code.is_failure:
        print(f"Error de conexión MQTT: {reason_code}")
        return
    print(f"Conectado al broker {BROKER}:{PORT}")
    client.subscribe(TOPIC)
    print(f"Suscrito al tópico: {TOPIC}\nEsperando mensajes... (Ctrl+C para salir)")


def on_message(client, userdata, message):
    recibido = datetime.now(timezone.utc).isoformat()
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        texto = json.dumps(payload, indent=2, ensure_ascii=False)
    except (UnicodeDecodeError, json.JSONDecodeError):
        texto = f"(payload no es JSON válido) {message.payload!r}"
    print(f"\n[{recibido}] Tópico: {message.topic}\n{texto}")


def main():
    if not BROKER:
        raise SystemExit("Falta MQTT_BROKER en el archivo .env")
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = on_connect
    cliente.on_message = on_message
    cliente.connect(BROKER, PORT, 60)
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")


if __name__ == "__main__":
    main()
