import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"


def leer_estudiantes(ruta):
    lista_estudiantes = []
    with open(ruta, encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            lista_estudiantes.append(fila)
    return lista_estudiantes


def transformar_estudiante(estudiante):
    nombre_completo = estudiante["nombre"] + " " + estudiante["apellido"]

    if estudiante["activo"] == "true":
        estado = "Activo"
    else:
        estado = "Inactivo"

    estudiante_nuevo = {
        "id": estudiante["codigo"],
        "nombre_completo": nombre_completo,
        "programa": estudiante["programa"],
        "semestre": int(estudiante["semestre"]),
        "promedio": float(estudiante["promedio"]),
        "estado": estado
    }

    return estudiante_nuevo


def transformar_todos(estudiantes):
    estudiantes_transformados = []
    for estudiante in estudiantes:
        nuevo = transformar_estudiante(estudiante)
        estudiantes_transformados.append(nuevo)
    return estudiantes_transformados


def guardar_json(ruta, estudiantes):
    ruta.parent.mkdir(exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        datos = json.load(archivo)
    return datos


estudiantes = leer_estudiantes(RUTA_CSV)
print("Total de estudiantes leidos:", len(estudiantes))

estudiantes_transformados = transformar_todos(estudiantes)

guardar_json(RUTA_JSON, estudiantes_transformados)
print("Archivo JSON generado en:", RUTA_JSON)

estudiantes_recuperados = leer_json(RUTA_JSON)
print("Primer estudiante recuperado:", estudiantes_recuperados[0])
print("Total recuperado:", len(estudiantes_recuperados))