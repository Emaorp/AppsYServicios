from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class SensorMagnitud(Base):
    """Tabla sensor_magnitudes (catálogo suministrado por el docente, solo lectura).

    Define qué magnitud mide cada sensor, en qué unidad y en qué rango válido.
    """

    __tablename__ = "sensor_magnitudes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # FK -> sensores(id)
    sensor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    magnitud: Mapped[str] = mapped_column(String(50), nullable=False)
    unidad: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    valor_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    sensor: Mapped["Sensor"] = relationship(back_populates="magnitudes")
    # 1 magnitud -> N mediciones
    mediciones: Mapped[list["Medicion"]] = relationship(back_populates="sensor_magnitud")
