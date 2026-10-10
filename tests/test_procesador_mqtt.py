"""Pruebas de validación de mensajes MQTT (evidencias 2 a 7 de la guía)."""

import json

from app.mqtt.procesador import procesar_mensaje
from app.models import Medicion
from tests.conftest import contar_mediciones


def mensaje(**cambios):
    base = {
        "sensor_id": "TEST-001",
        "timestamp": "2026-10-07T16:25:30Z",
        "measurements": {"temperature": {"value": 24.6, "unit": "C"}},
    }
    base.update(cambios)
    return json.dumps(base)


def test_mensaje_valido_se_guarda(db):
    r = procesar_mensaje(db, mensaje(), codigo_esperado="TEST-001")
    assert r.aceptado and len(r.ids_guardados) == 1
    assert contar_mediciones() == 1


def test_varias_magnitudes_son_registros_independientes_con_mismo_timestamp(db):
    medidas = {"temperature": {"value": 24.6, "unit": "C"}, "humidity": {"value": 55, "unit": "%"}}
    r = procesar_mensaje(db, mensaje(measurements=medidas), codigo_esperado="TEST-001")
    assert r.aceptado and len(r.ids_guardados) == 2
    filas = db.query(Medicion).all()
    assert len({f.sensor_magnitud_id for f in filas}) == 2
    assert len({f.timestamp_utc for f in filas}) == 1


def test_timestamp_se_guarda_en_utc(db):
    # 11:25:30 en Colombia (-05:00) == 16:25:30 UTC
    r = procesar_mensaje(db, mensaje(timestamp="2026-10-07T11:25:30-05:00"))
    assert r.aceptado
    fila = db.get(Medicion, r.ids_guardados[0])
    assert fila.timestamp_utc.hour == 16


def test_sensor_inexistente(db):
    r = procesar_mensaje(db, mensaje(sensor_id="NO-EXISTE"))
    assert not r.aceptado and "inexistente" in r.motivo
    assert contar_mediciones() == 0


def test_sensor_inactivo(db):
    medidas = {"pm25": {"value": 10, "unit": "ug/m3"}}
    r = procesar_mensaje(db, mensaje(sensor_id="OFF-002", measurements=medidas))
    assert not r.aceptado and "inactivo" in r.motivo


def test_unidad_incorrecta(db):
    r = procesar_mensaje(db, mensaje(measurements={"temperature": {"value": 24.6, "unit": "F"}}))
    assert not r.aceptado and "Unidad incorrecta" in r.motivo
    assert contar_mediciones() == 0


def test_tipo_de_dato_incorrecto_texto(db):
    r = procesar_mensaje(db, mensaje(measurements={"temperature": {"value": "24.6", "unit": "C"}}))
    assert not r.aceptado and "Estructura inválida" in r.motivo


def test_tipo_de_dato_incorrecto_booleano(db):
    r = procesar_mensaje(db, mensaje(measurements={"temperature": {"value": True, "unit": "C"}}))
    assert not r.aceptado


def test_magnitud_incorrecta(db):
    r = procesar_mensaje(db, mensaje(measurements={"co2": {"value": 400, "unit": "ppm"}}))
    assert not r.aceptado and "no pertenece" in r.motivo


def test_timestamp_invalido_texto(db):
    r = procesar_mensaje(db, mensaje(timestamp="ayer por la tarde"))
    assert not r.aceptado and "timestamp" in r.motivo


def test_timestamp_invalido_numero(db):
    r = procesar_mensaje(db, mensaje(timestamp=1760000000))
    assert not r.aceptado


def test_timestamp_sin_zona_horaria(db):
    r = procesar_mensaje(db, mensaje(timestamp="2026-10-07T16:25:30"))
    assert not r.aceptado and "zona horaria" in r.motivo


def test_valor_fuera_de_rango(db):
    r = procesar_mensaje(db, mensaje(measurements={"temperature": {"value": 999, "unit": "C"}}))
    assert not r.aceptado and "fuera de rango" in r.motivo


def test_campo_obligatorio_faltante(db):
    datos = json.loads(mensaje())
    del datos["measurements"]
    r = procesar_mensaje(db, json.dumps(datos))
    assert not r.aceptado


def test_json_invalido(db):
    r = procesar_mensaje(db, "esto no es json {")
    assert not r.aceptado and "JSON" in r.motivo


def test_payload_con_una_magnitud_invalida_no_guarda_ninguna(db):
    medidas = {"temperature": {"value": 24.6, "unit": "C"}, "humidity": {"value": 500, "unit": "%"}}
    r = procesar_mensaje(db, mensaje(measurements=medidas))
    assert not r.aceptado
    assert contar_mediciones() == 0


def test_sensor_distinto_al_del_topico_se_rechaza(db):
    r = procesar_mensaje(db, mensaje(), codigo_esperado="OTRO-999")
    assert not r.aceptado and "no corresponde" in r.motivo
    assert contar_mediciones() == 0


def test_dry_run_no_guarda(db):
    r = procesar_mensaje(db, mensaje(), dry_run=True)
    assert r.aceptado
    assert contar_mediciones() == 0
