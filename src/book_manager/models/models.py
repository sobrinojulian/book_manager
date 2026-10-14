"""Modelos ORM y relaciones de la base de datos del catálogo."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
  CheckConstraint,
  Date,
  ForeignKey,
  Integer,
  Numeric,
  String,
  UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  """Base declarativa común para las tablas del sistema."""


class Genero(Base):
  __tablename__ = "generos"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

  libros: Mapped[list[Libro]] = relationship(back_populates="genero")


class Editorial(Base):
  __tablename__ = "editoriales"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(150), nullable=False)
  pais: Mapped[str] = mapped_column(String(100), nullable=False)

  libros: Mapped[list[Libro]] = relationship(back_populates="editorial")


class Moneda(Base):
  __tablename__ = "monedas"
  __table_args__ = (
    UniqueConstraint("codigo", name="uq_monedas_codigo"),
  )

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  codigo: Mapped[str] = mapped_column(String(3), nullable=False)
  nombre: Mapped[str] = mapped_column(String(100), nullable=False)

  precios: Mapped[list[Precio]] = relationship(back_populates="moneda")


class TipoCotizacion(Base):
  __tablename__ = "tipos_cotizacion"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

  cotizaciones: Mapped[list[CotizacionDolar]] = relationship(
    back_populates="tipo"
  )


class Libro(Base):
  __tablename__ = "libros"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  isbn: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
  titulo: Mapped[str] = mapped_column(String(250), nullable=False)
  autor: Mapped[str] = mapped_column(String(200), nullable=False)
  editorial_id: Mapped[int] = mapped_column(
    ForeignKey("editoriales.id", ondelete="RESTRICT"), nullable=False
  )
  genero_id: Mapped[int] = mapped_column(
    ForeignKey("generos.id", ondelete="RESTRICT"), nullable=False
  )

  editorial: Mapped[Editorial] = relationship(back_populates="libros")
  genero: Mapped[Genero] = relationship(back_populates="libros")
  precios: Mapped[list[Precio]] = relationship(
    back_populates="libro",
    cascade="all, delete-orphan",
    passive_deletes=True,
  )
  stock: Mapped[Stock | None] = relationship(
    back_populates="libro",
    cascade="all, delete-orphan",
    passive_deletes=True,
    uselist=False,
  )


class Precio(Base):
  __tablename__ = "precios"
  __table_args__ = (
    CheckConstraint("monto >= 0", name="ck_precios_monto_no_negativo"),
  )

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  libro_id: Mapped[int] = mapped_column(
    ForeignKey("libros.id", ondelete="CASCADE"), nullable=False
  )
  moneda_id: Mapped[int] = mapped_column(
    ForeignKey("monedas.id", ondelete="RESTRICT"), nullable=False
  )
  monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

  libro: Mapped[Libro] = relationship(back_populates="precios")
  moneda: Mapped[Moneda] = relationship(back_populates="precios")


class Stock(Base):
  __tablename__ = "stocks"
  __table_args__ = (
    CheckConstraint("cantidad >= 0", name="ck_stocks_cantidad_no_negativa"),
  )

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  libro_id: Mapped[int] = mapped_column(
    ForeignKey("libros.id", ondelete="CASCADE"),
    nullable=False,
    unique=True,
  )
  cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

  libro: Mapped[Libro] = relationship(back_populates="stock")


class CotizacionDolar(Base):
  __tablename__ = "cotizaciones_dolar"
  __table_args__ = (
    UniqueConstraint(
      "tipo_id", "fecha", name="uq_cotizaciones_tipo_fecha"
    ),
    CheckConstraint(
      "valor_compra >= 0", name="ck_cotizaciones_compra_no_negativa"
    ),
    CheckConstraint(
      "valor_venta >= 0", name="ck_cotizaciones_venta_no_negativa"
    ),
  )

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  tipo_id: Mapped[int] = mapped_column(
    ForeignKey("tipos_cotizacion.id", ondelete="RESTRICT"), nullable=False
  )
  fecha: Mapped[date] = mapped_column(Date, nullable=False)
  valor_compra: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
  valor_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

  tipo: Mapped[TipoCotizacion] = relationship(back_populates="cotizaciones")
