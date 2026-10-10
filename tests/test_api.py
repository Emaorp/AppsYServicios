"""Pruebas de los endpoints (evidencias 8 a 16 de la guía)."""

import json

from app.mqtt.procesador import procesar_mensaje


def guardar(db, timestamp, temperatura=24.0, humedad=None):
    medidas = {"temperature": {"value": temperatura, "unit": "C"}}
    if humedad is not None:
        medidas["humidity"] = {"value": humedad, "unit": "%"}
    crudo = json.dumps({"sensor_id": "TEST-001", "timestamp": timestamp, "measurements": medidas})
    assert procesar_mensaje(db, crudo).aceptado


def test_listar_sensores(cliente):
    r = cliente.get("/sensores")
    assert r.status_code == 200 and len(r.json()) == 2


def test_sensor_por_id_y_por_codigo(cliente):
    assert cliente.get("/sensores/1").json()["codigo"] == "TEST-001"
    assert cliente.get("/sensores/por-codigo/TEST-001").json()["id"] == 1


def test_sensor_inexistente_404(cliente):
    assert cliente.get("/sensores/999").status_code == 404
    assert cliente.get("/sensores/por-codigo/NADA").status_code == 404


def test_magnitudes_del_sensor(cliente):
    r = cliente.get("/sensores/1/magnitudes")
    assert r.status_code == 200
    assert {m["magnitud"] for m in r.json()} == {"temperature", "humidity"}
    assert cliente.get("/sensores/999/magnitudes").status_code == 404


def test_sensor_magnitud_por_id(cliente):
    assert cliente.get("/sensor-magnitudes/1").json()["unidad"] == "C"
    assert cliente.get("/sensor-magnitudes/999").status_code == 404


def test_medicion_por_id_y_hora_local(cliente, db):
    guardar(db, "2026-10-07T16:25:30Z")
    r = cliente.get("/mediciones/1")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["valor"] == 24.0
    assert cuerpo["sensor_codigo"] == "TEST-001"
    # 16:25:30 UTC == 11:25:30 en Colombia
    assert cuerpo["timestamp_local"] == "2026-10-07 11:25:30 (UTC-05:00)"


def test_medicion_inexistente_404(cliente):
    assert cliente.get("/mediciones/999").status_code == 404


def test_historico_orden_y_limit(cliente, db):
    for minuto in range(5):
        guardar(db, f"2026-10-07T16:0{minuto}:00Z", temperatura=20 + minuto)
    todo = cliente.get("/sensores/1/mediciones").json()
    assert len(todo) == 5 and todo[0]["valor"] == 24.0  # la más reciente primero
    ultimas = cliente.get("/sensores/1/mediciones?limit=2").json()
    assert [m["valor"] for m in ultimas] == [24.0, 23.0]


def test_filtro_por_magnitud(cliente, db):
    guardar(db, "2026-10-07T16:00:00Z", humedad=50)
    r = cliente.get("/sensores/1/mediciones?magnitud=humidity").json()
    assert len(r) == 1 and r[0]["magnitud"] == "humidity"
    assert cliente.get("/sensores/1/mediciones?magnitud=co2").status_code == 404


def test_rango_de_fechas_en_hora_local(cliente, db):
    guardar(db, "2026-10-07T15:00:00Z", temperatura=10)  # 10:00 Colombia
    guardar(db, "2026-10-07T17:00:00Z", temperatura=20)  # 12:00 Colombia
    guardar(db, "2026-10-07T19:00:00Z", temperatura=30)  # 14:00 Colombia
    r = cliente.get("/sensores/1/mediciones?desde=2026-10-07T11:00:00&hasta=2026-10-07T13:00:00").json()
    assert [m["valor"] for m in r] == [20.0]


def test_filtros_combinados(cliente, db):
    guardar(db, "2026-10-07T15:00:00Z", temperatura=10, humedad=40)
    guardar(db, "2026-10-07T17:00:00Z", temperatura=20, humedad=50)
    url = "/sensores/1/mediciones?magnitud=temperature&desde=2026-10-07T09:00:00&hasta=2026-10-07T23:00:00&limit=1"
    r = cliente.get(url).json()
    assert len(r) == 1 and r[0]["valor"] == 20.0


def test_rango_invertido_400(cliente):
    r = cliente.get("/sensores/1/mediciones?desde=2026-10-08T00:00:00&hasta=2026-10-07T00:00:00")
    assert r.status_code == 400


def test_validacion_http_422(cliente):
    assert cliente.get("/sensores/abc").status_code == 422
    assert cliente.get("/sensores/1/mediciones?limit=0").status_code == 422
    assert cliente.get("/sensores/1/mediciones?desde=no-es-fecha").status_code == 422


def test_ultima_medicion(cliente, db):
    guardar(db, "2026-10-07T16:00:00Z", temperatura=11)
    guardar(db, "2026-10-07T16:10:00Z", temperatura=22)
    r = cliente.get("/sensores/1/ultima-medicion")
    assert r.status_code == 200 and r.json()["valor"] == 22.0


def test_ultima_medicion_sin_datos_404(cliente):
    assert cliente.get("/sensores/1/ultima-medicion").status_code == 404
    assert cliente.get("/sensores/999/ultima-medicion").status_code == 404
