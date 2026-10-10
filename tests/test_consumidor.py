"""El callback del consumidor MQTT procesa mensajes como lo haría con el broker real."""

import json
from types import SimpleNamespace

from app.mqtt.client import ConsumidorMqtt, _codigo_desde_topico
from tests.conftest import contar_mediciones


def test_codigo_desde_topico():
    assert _codigo_desde_topico("iot/sensors/TEST-001/data") == "TEST-001"
    assert _codigo_desde_topico("iot/sensors/+/data") is None
    assert _codigo_desde_topico("otra/cosa") is None


def _mensaje(sensor_id="TEST-001", valor=24.6):
    return SimpleNamespace(
        topic="iot/sensors/TEST-001/data",
        payload=json.dumps({
            "sensor_id": sensor_id,
            "timestamp": "2026-10-07T16:25:30Z",
            "measurements": {"temperature": {"value": valor, "unit": "C"}},
        }).encode(),
    )


def test_on_message_guarda_valido_y_descarta_invalido():
    consumidor = ConsumidorMqtt("localhost", 1883, "iot/sensors/TEST-001/data")
    consumidor._on_message(None, None, _mensaje())
    assert contar_mediciones() == 1
    consumidor._on_message(None, None, _mensaje(valor=9999))   # fuera de rango
    consumidor._on_message(None, None, _mensaje(sensor_id="OTRO"))  # sensor distinto
    assert contar_mediciones() == 1


def test_on_message_no_se_cae_con_basura():
    consumidor = ConsumidorMqtt("localhost", 1883, "iot/sensors/TEST-001/data")
    consumidor._on_message(None, None, SimpleNamespace(topic="x", payload=b"\xff\xfe\x00 basura"))
    assert contar_mediciones() == 0
