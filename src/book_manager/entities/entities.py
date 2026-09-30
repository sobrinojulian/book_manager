"""Objetos principales del dominio de una librería."""
from __future__ import annotations

import abc
from datetime import date
from typing import Optional


def _formatear_importe(valor: float) -> str:
  parte_entera, parte_decimal = f"{valor:,.2f}".split(".")
  return f"{parte_entera.replace(',', '.')},{parte_decimal}"


class EntidadBase(abc.ABC):
  """Comparte el identificador con el que se reconoce cada registro."""

  def __init__(self, id: Optional[int] = None) -> None:
    self._id = id

  @property
  def id(self) -> Optional[int]:
    return self._id

  @id.setter
  def id(self, valor: int) -> None:
    self._id = valor


class Genero(EntidadBase):
  """Clasifica los títulos por su temática o tipo literario."""

  def __init__(
    self, nombre: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._nombre = nombre

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  def __repr__(self) -> str:
    return f"Genero(id={self.id}, nombre={self.nombre!r})"

  def __str__(self) -> str:
    return self.nombre


class Editorial(EntidadBase):
  """Identifica la casa editorial que publica o distribuye una obra."""

  def __init__(
    self, nombre: str, pais: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._nombre = nombre
    self._pais = pais

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  @property
  def pais(self) -> str:
    return self._pais

  @pais.setter
  def pais(self, valor: str) -> None:
    self._pais = valor

  def __repr__(self) -> str:
    return (
      f"Editorial(id={self.id}, nombre={self.nombre!r}, "
      f"pais={self.pais!r})"
    )

  def __str__(self) -> str:
    if self.pais:
      return f"{self.nombre} ({self.pais})"
    return self.nombre


class Moneda(EntidadBase):
  """Representa la divisa utilizada para expresar un importe."""

  def __init__(
    self, codigo: str, nombre: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._codigo = codigo.upper()
    self._nombre = nombre

  @property
  def codigo(self) -> str:
    return self._codigo

  @codigo.setter
  def codigo(self, valor: str) -> None:
    self._codigo = valor.upper()

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  def __repr__(self) -> str:
    return f"Moneda(id={self.id}, codigo={self.codigo!r})"

  def __str__(self) -> str:
    return f"{self.nombre} ({self.codigo})"


class TipoCotizacion(EntidadBase):
  """Variante del dólar que se toma como referencia, por ejemplo MEP."""

  def __init__(
    self, nombre: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._nombre = nombre

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  def __repr__(self) -> str:
    return f"TipoCotizacion(id={self.id}, nombre={self.nombre!r})"

  def __str__(self) -> str:
    return self.nombre


class Libro(EntidadBase):
  """Ficha bibliográfica de una obra disponible en el catálogo."""

  def __init__(
    self,
    isbn: str,
    titulo: str,
    autor: str,
    editorial: Editorial,
    genero: Genero,
    id: Optional[int] = None,
  ) -> None:
    super().__init__(id)
    self._isbn = isbn
    self._titulo = titulo
    self._autor = autor
    self._editorial = editorial
    self._genero = genero

  @property
  def isbn(self) -> str:
    return self._isbn

  @isbn.setter
  def isbn(self, valor: str) -> None:
    self._isbn = valor

  @property
  def titulo(self) -> str:
    return self._titulo

  @titulo.setter
  def titulo(self, valor: str) -> None:
    self._titulo = valor

  @property
  def autor(self) -> str:
    return self._autor

  @autor.setter
  def autor(self, valor: str) -> None:
    self._autor = valor

  @property
  def editorial(self) -> Editorial:
    return self._editorial

  @editorial.setter
  def editorial(self, valor: Editorial) -> None:
    self._editorial = valor

  @property
  def genero(self) -> Genero:
    return self._genero

  @genero.setter
  def genero(self, valor: Genero) -> None:
    self._genero = valor

  def __repr__(self) -> str:
    return (
      f"Libro(id={self.id}, isbn={self.isbn!r}, "
      f"titulo={self.titulo!r}, autor={self.autor!r})"
    )

  def __str__(self) -> str:
    return f"{self.titulo} — {self.autor} (ISBN: {self.isbn})"


class Precio(EntidadBase):
  """Importe de un libro expresado en una divisa concreta."""

  def __init__(
    self,
    libro: Libro,
    moneda: Moneda,
    monto: float,
    id: Optional[int] = None,
  ) -> None:
    super().__init__(id)
    self._libro = libro
    self._moneda = moneda
    self.monto = monto

  @property
  def libro(self) -> Libro:
    return self._libro

  @libro.setter
  def libro(self, valor: Libro) -> None:
    self._libro = valor

  @property
  def moneda(self) -> Moneda:
    return self._moneda

  @moneda.setter
  def moneda(self, valor: Moneda) -> None:
    self._moneda = valor

  @property
  def monto(self) -> float:
    return self._monto

  @monto.setter
  def monto(self, valor: float) -> None:
    if valor < 0:
      raise ValueError("El monto no puede ser negativo.")
    self._monto = valor

  def __repr__(self) -> str:
    return (
      f"Precio(id={self.id}, libro={self.libro.titulo!r}, "
      f"monto={self.monto} {self.moneda.codigo})"
    )

  def __str__(self) -> str:
    return (
      f"{self.libro.titulo}: {self.moneda.codigo} "
      f"{_formatear_importe(self.monto)}"
    )


class Stock(EntidadBase):
  """Existencias registradas para un título del catálogo."""

  def __init__(
    self, libro: Libro, cantidad: int, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._libro = libro
    self.cantidad = cantidad

  @property
  def libro(self) -> Libro:
    return self._libro

  @libro.setter
  def libro(self, valor: Libro) -> None:
    self._libro = valor

  @property
  def cantidad(self) -> int:
    return self._cantidad

  @cantidad.setter
  def cantidad(self, valor: int) -> None:
    if valor < 0:
      raise ValueError("La cantidad no puede ser negativa.")
    self._cantidad = valor

  def __repr__(self) -> str:
    return (
      f"Stock(id={self.id}, libro={self.libro.titulo!r}, "
      f"cantidad={self.cantidad})"
    )

  def __str__(self) -> str:
    identificador = f"ID {self.id} | " if self.id is not None else ""
    return (
      f"{identificador}{self.libro.titulo}: "
      f"{self.cantidad} unidades disponibles"
    )


class CotizacionDolar(EntidadBase):
  """Valores de compra y venta del dólar registrados en una fecha."""

  def __init__(
    self,
    tipo: TipoCotizacion,
    fecha: date,
    valor_compra: float,
    valor_venta: float,
    id: Optional[int] = None,
  ) -> None:
    super().__init__(id)
    self._tipo = tipo
    self._fecha = fecha
    self._valor_compra = valor_compra
    self._valor_venta = valor_venta

  @property
  def tipo(self) -> TipoCotizacion:
    return self._tipo

  @tipo.setter
  def tipo(self, valor: TipoCotizacion) -> None:
    self._tipo = valor

  @property
  def fecha(self) -> date:
    return self._fecha

  @fecha.setter
  def fecha(self, valor: date) -> None:
    self._fecha = valor

  @property
  def valor_compra(self) -> float:
    return self._valor_compra

  @valor_compra.setter
  def valor_compra(self, valor: float) -> None:
    self._valor_compra = valor

  @property
  def valor_venta(self) -> float:
    return self._valor_venta

  @valor_venta.setter
  def valor_venta(self, valor: float) -> None:
    self._valor_venta = valor

  def __repr__(self) -> str:
    return (
      f"CotizacionDolar(tipo={self.tipo.nombre!r}, "
      f"fecha={self.fecha!r}, venta={self.valor_venta})"
    )

  def __str__(self) -> str:
    fecha_legible = self.fecha.strftime("%d/%m/%Y")
    return (
      f"Dólar {self.tipo.nombre} ({fecha_legible}) — "
      f"compra ARS {_formatear_importe(self.valor_compra)}; "
      f"venta ARS {_formatear_importe(self.valor_venta)}"
    )
