"""Conexión a PostgreSQL con SQLAlchemy.

Las credenciales se leen de variables de entorno (archivo .env).
Nunca se escriben en el código.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


def _construir_url():
    """Arma la URL de conexión a partir del entorno."""
    # DATABASE_URL permite sobreescribir todo (se usa en las pruebas con SQLite).
    url_completa = os.getenv("DATABASE_URL")
    if url_completa:
        return url_completa

    faltantes = [
        nombre
        for nombre in ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
        if not os.getenv(nombre)
    ]
    if faltantes:
        raise RuntimeError(
            "Faltan variables de entorno para la base de datos: "
            + ", ".join(faltantes)
            + ". Revisa tu archivo .env"
        )

    return URL.create(
        "postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"),
    )


_url = _construir_url()
_args = {"check_same_thread": False} if str(_url).startswith("sqlite") else {}

engine = create_engine(_url, pool_pre_ping=True, connect_args=_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base de todos los modelos ORM."""


def get_db():
    """Dependencia de FastAPI: abre una sesión por solicitud y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
