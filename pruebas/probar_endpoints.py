"""Evidencias 8 a 16: llama a los endpoints reales y guarda cada respuesta.

La API debe estar corriendo (uvicorn app.main:app). Solo hace solicitudes GET.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python -m pruebas.probar_endpoints --sensor-id 1
Genera: evidencias/endpoints_http.txt
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--sensor-id", type=int, required=True, help="id numérico del sensor asignado")
    parser.add_argument("--magnitud", default=None, help="magnitud para el filtro (opcional)")
    args = parser.parse_args()

    base, sid = args.base, args.sensor_id

    # Datos reales del sensor para armar las consultas
    sensor = requests.get(f"{base}/sensores/{sid}", timeout=15).json()
    magnitudes = requests.get(f"{base}/sensores/{sid}/magnitudes", timeout=15).json()
    magnitud = args.magnitud or (magnitudes[0]["magnitud"] if magnitudes else "temperature")
    historico = requests.get(f"{base}/sensores/{sid}/mediciones?limit=1", timeout=15).json()
    id_medicion = historico[0]["id"] if isinstance(historico, list) and historico else 1

    casos = [
        ("1. Listar sensores", "200", "/sensores"),
        ("2. Sensor por id", "200", f"/sensores/{sid}"),
        ("3. Sensor por código", "200", f"/sensores/por-codigo/{sensor.get('codigo', 'X')}"),
        ("4. Magnitudes del sensor", "200", f"/sensores/{sid}/magnitudes"),
        ("5. Relación sensor-magnitud por id", "200",
         f"/sensor-magnitudes/{magnitudes[0]['id'] if magnitudes else 1}"),
        ("8. Consulta por ID existente", "200 (si hay mediciones)", f"/mediciones/{id_medicion}"),
        ("9. Consulta por ID inexistente", "404", "/mediciones/999999999"),
        ("10. Consulta histórica", "200", f"/sensores/{sid}/mediciones"),
        ("11. Consulta por rango de fechas", "200",
         f"/sensores/{sid}/mediciones?desde=2026-01-01T00:00:00&hasta=2030-01-01T00:00:00"),
        ("12. Rango con desde > hasta", "400",
         f"/sensores/{sid}/mediciones?desde=2030-01-01T00:00:00&hasta=2026-01-01T00:00:00"),
        ("13. Validación HTTP incorrecta (limit=0)", "422", f"/sensores/{sid}/mediciones?limit=0"),
        ("13b. Validación HTTP incorrecta (id no numérico)", "422", "/sensores/abc"),
        ("14. Última medición", "200 (si hay mediciones)", f"/sensores/{sid}/ultima-medicion"),
        ("15. Últimas N mediciones (limit=3)", "200", f"/sensores/{sid}/mediciones?limit=3"),
        ("16. Filtro por magnitud", "200", f"/sensores/{sid}/mediciones?magnitud={magnitud}"),
        ("Extra: sensor inexistente", "404", "/sensores/999999"),
        ("Extra: filtros combinados", "200",
         f"/sensores/{sid}/mediciones?magnitud={magnitud}&desde=2026-01-01T00:00:00&hasta=2030-01-01T00:00:00&limit=10"),
    ]

    lineas = [
        "PRUEBAS DE ENDPOINTS HTTP",
        f"Fecha de ejecución: {datetime.now().isoformat(timespec='seconds')}",
        f"API: {base} | sensor id={sid} | magnitud de prueba: {magnitud}",
        "=" * 78,
    ]
    for titulo, esperado, ruta in casos:
        r = requests.get(base + ruta, timeout=15)
        try:
            cuerpo = json.dumps(r.json(), ensure_ascii=False, indent=2)
        except ValueError:
            cuerpo = r.text
        if len(cuerpo) > 900:
            cuerpo = cuerpo[:900] + "\n  ... (recortado)"
        lineas += [
            f"\n{titulo}",
            f"  Solicitud: GET {ruta}",
            f"  Esperado : {esperado}",
            f"  Obtenido : HTTP {r.status_code}",
            "  Respuesta:",
            *["    " + linea for linea in cuerpo.splitlines()],
        ]

    texto = "\n".join(lineas)
    print(texto)
    ruta = Path("evidencias/endpoints_http.txt")
    ruta.parent.mkdir(exist_ok=True)
    ruta.write_text(texto + "\n", encoding="utf-8")
    print(f"\nEvidencia guardada en {ruta}")


if __name__ == "__main__":
    main()
