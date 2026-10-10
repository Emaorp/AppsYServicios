from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Medicion(Base):
    """Tabla mediciones: una fila por magnitud de cada mensaje MQTT válido."""

    __tablename__ = "mediciones"

    # BIGSERIAL en PostgreSQL (la variante Integer solo existe para las pruebas con SQLite)
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    # FK -> sensor_magnitudes(id)
    sensor_magnitud_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sensor_magnitudes.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_recepcion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sensor_magnitud: Mapped["SensorMagnitud"] = relationship(back_populates="mediciones")
