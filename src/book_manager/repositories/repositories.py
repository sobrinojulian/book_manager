"""Repositorios SQLAlchemy para las entidades del catálogo."""
from __future__ import annotations

import abc
from datetime import date
from typing import Generic, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
  CotizacionDolar,
  Editorial,
  EntidadBase,
  Genero,
  Libro,
  Moneda,
  Precio,
  Stock,
  TipoCotizacion,
)
from book_manager.models.models import (
  Base,
  CotizacionDolar as ModeloCotizacionDolar,
  Editorial as ModeloEditorial,
  Genero as ModeloGenero,
  Libro as ModeloLibro,
  Moneda as ModeloMoneda,
  Precio as ModeloPrecio,
  Stock as ModeloStock,
  TipoCotizacion as ModeloTipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)
M = TypeVar("M", bound=Base)

_conexion_compartida: ConexionDB | None = None


def _conexion_por_defecto() -> ConexionDB:
  global _conexion_compartida
  if _conexion_compartida is None:
    _conexion_compartida = ConexionDB()
  return _conexion_compartida


def _fecha_como_date(valor: date | str) -> date:
  if isinstance(valor, date):
    return valor
  return date.fromisoformat(valor)


class IRepositorio(abc.ABC, Generic[T]):
  """Contrato común para consultar y modificar entidades persistidas."""

  @abc.abstractmethod
  def crear(self, entidad: T) -> T:
    """Guarda una entidad nueva y la devuelve con su identificador."""

  @abc.abstractmethod
  def leer_por_id(self, id: int) -> Optional[T]:
    """Busca una entidad a partir de su identificador."""

  @abc.abstractmethod
  def leer_todos(self) -> list[T]:
    """Devuelve las entidades disponibles."""

  @abc.abstractmethod
  def actualizar(self, entidad: T) -> T:
    """Persiste los cambios de una entidad existente."""

  @abc.abstractmethod
  def eliminar(self, id: int) -> bool:
    """Elimina la entidad indicada e informa si existía."""


class IRepositorioStock(abc.ABC):
  """Amplía el contrato CRUD con operaciones por libro."""

  @abc.abstractmethod
  def crear(self, stock: Stock) -> Stock:
    """Registra las existencias asociadas a un libro."""

  @abc.abstractmethod
  def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
    """Busca las existencias asociadas a un libro."""

  @abc.abstractmethod
  def actualizar(self, stock: Stock) -> Stock:
    """Guarda los cambios en las existencias."""

  @abc.abstractmethod
  def eliminar(self, libro_id: int) -> bool:
    """Elimina las existencias asociadas al libro indicado."""


class IRepositorioCotizacionDolar(abc.ABC):
  """Define consultas específicas para el historial del dólar."""

  @abc.abstractmethod
  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    """Añade un registro de cotización al historial."""

  @abc.abstractmethod
  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: str
  ) -> Optional[CotizacionDolar]:
    """Busca el registro de un tipo de dólar para una fecha."""

  @abc.abstractmethod
  def leer_historico_por_tipo(
    self, tipo_id: int
  ) -> list[CotizacionDolar]:
    """Devuelve las cotizaciones registradas para un tipo."""

  @abc.abstractmethod
  def actualizar(
    self, cotizacion: CotizacionDolar
  ) -> CotizacionDolar:
    """Actualiza un registro existente del historial."""

  @abc.abstractmethod
  def eliminar(self, tipo_id: int, fecha: str) -> bool:
    """Quita la cotización correspondiente al tipo y fecha."""


class RepositorioSQLBase(IRepositorio[T], Generic[T, M]):
  """Implementa operaciones CRUD transaccionales sobre una tabla ORM."""

  modelo: type[M]

  def __init__(self, conexion: ConexionDB | None = None) -> None:
    self._conexion = conexion or _conexion_por_defecto()
    Base.metadata.create_all(self._conexion.engine)

  @abc.abstractmethod
  def _crear_modelo(self, entidad: T) -> M:
    """Construye el modelo ORM correspondiente a una entidad de dominio."""

  @abc.abstractmethod
  def _actualizar_modelo(self, modelo: M, entidad: T) -> None:
    """Copia los valores de dominio al modelo ORM existente."""

  @abc.abstractmethod
  def _a_entidad(self, modelo: M) -> T:
    """Convierte el modelo ORM en una entidad de dominio."""

  def crear(self, entidad: T) -> T:
    with self._conexion.transaccion() as sesion:
      modelo = self._crear_modelo(entidad)
      sesion.add(modelo)
      sesion.flush()
      entidad.id = modelo.id
    return entidad

  def leer_por_id(self, id: int) -> Optional[T]:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.get(self.modelo, id)
      return self._a_entidad(modelo) if modelo is not None else None

  def leer_todos(self) -> list[T]:
    with self._conexion.transaccion() as sesion:
      modelos = sesion.scalars(
        select(self.modelo).order_by(self.modelo.id)
      ).all()
      return [self._a_entidad(modelo) for modelo in modelos]

  def actualizar(self, entidad: T) -> T:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.get(self.modelo, entidad.id)
      if modelo is None:
        raise ValueError(
          f"No se encontró la entidad con id={entidad.id}."
        )
      self._actualizar_modelo(modelo, entidad)
    return entidad

  def eliminar(self, id: int) -> bool:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.get(self.modelo, id)
      if modelo is None:
        return False
      sesion.delete(modelo)
    return True


class RepositorioGenero(RepositorioSQLBase[Genero, ModeloGenero]):
  """Persiste los géneros disponibles en la base de datos."""

  modelo = ModeloGenero

  def _crear_modelo(self, entidad: Genero) -> ModeloGenero:
    return ModeloGenero(id=entidad.id, nombre=entidad.nombre)

  def _actualizar_modelo(
    self, modelo: ModeloGenero, entidad: Genero
  ) -> None:
    modelo.nombre = entidad.nombre

  def _a_entidad(self, modelo: ModeloGenero) -> Genero:
    return Genero(id=modelo.id, nombre=modelo.nombre)


class RepositorioEditorial(RepositorioSQLBase[Editorial, ModeloEditorial]):
  """Persiste las editoriales en la base de datos."""

  modelo = ModeloEditorial

  def _crear_modelo(self, entidad: Editorial) -> ModeloEditorial:
    return ModeloEditorial(
      id=entidad.id, nombre=entidad.nombre, pais=entidad.pais
    )

  def _actualizar_modelo(
    self, modelo: ModeloEditorial, entidad: Editorial
  ) -> None:
    modelo.nombre = entidad.nombre
    modelo.pais = entidad.pais

  def _a_entidad(self, modelo: ModeloEditorial) -> Editorial:
    return Editorial(
      id=modelo.id, nombre=modelo.nombre, pais=modelo.pais
    )


class RepositorioMoneda(RepositorioSQLBase[Moneda, ModeloMoneda]):
  """Persiste las monedas disponibles para los precios."""

  modelo = ModeloMoneda

  def _crear_modelo(self, entidad: Moneda) -> ModeloMoneda:
    return ModeloMoneda(
      id=entidad.id, codigo=entidad.codigo, nombre=entidad.nombre
    )

  def _actualizar_modelo(
    self, modelo: ModeloMoneda, entidad: Moneda
  ) -> None:
    modelo.codigo = entidad.codigo
    modelo.nombre = entidad.nombre

  def _a_entidad(self, modelo: ModeloMoneda) -> Moneda:
    return Moneda(
      id=modelo.id, codigo=modelo.codigo, nombre=modelo.nombre
    )


class RepositorioTipoCotizacion(
  RepositorioSQLBase[TipoCotizacion, ModeloTipoCotizacion]
):
  """Persiste los tipos de cotización configurados."""

  modelo = ModeloTipoCotizacion

  def _crear_modelo(self, entidad: TipoCotizacion) -> ModeloTipoCotizacion:
    return ModeloTipoCotizacion(id=entidad.id, nombre=entidad.nombre)

  def _actualizar_modelo(
    self, modelo: ModeloTipoCotizacion, entidad: TipoCotizacion
  ) -> None:
    modelo.nombre = entidad.nombre

  def _a_entidad(self, modelo: ModeloTipoCotizacion) -> TipoCotizacion:
    return TipoCotizacion(id=modelo.id, nombre=modelo.nombre)


class RepositorioLibro(RepositorioSQLBase[Libro, ModeloLibro]):
  """Persiste libros y sus referencias de catálogo."""

  modelo = ModeloLibro

  def __init__(
    self,
    repo_editorial: RepositorioEditorial,
    repo_genero: RepositorioGenero,
    conexion: ConexionDB | None = None,
  ) -> None:
    conexion_resuelta = conexion or repo_editorial._conexion
    if (
      repo_genero._conexion is not conexion_resuelta
      or repo_editorial._conexion is not conexion_resuelta
    ):
      raise ValueError("Los repositorios relacionados deben usar la misma conexión.")
    super().__init__(conexion_resuelta)

  def _crear_modelo(self, entidad: Libro) -> ModeloLibro:
    return ModeloLibro(
      id=entidad.id,
      isbn=entidad.isbn,
      titulo=entidad.titulo,
      autor=entidad.autor,
      editorial_id=entidad.editorial.id,
      genero_id=entidad.genero.id,
    )

  def _actualizar_modelo(
    self, modelo: ModeloLibro, entidad: Libro
  ) -> None:
    modelo.isbn = entidad.isbn
    modelo.titulo = entidad.titulo
    modelo.autor = entidad.autor
    modelo.editorial_id = entidad.editorial.id
    modelo.genero_id = entidad.genero.id

  def _a_entidad(self, modelo: ModeloLibro) -> Libro:
    return Libro(
      id=modelo.id,
      isbn=modelo.isbn,
      titulo=modelo.titulo,
      autor=modelo.autor,
      editorial=Editorial(
        id=modelo.editorial.id,
        nombre=modelo.editorial.nombre,
        pais=modelo.editorial.pais,
      ),
      genero=Genero(
        id=modelo.genero.id,
        nombre=modelo.genero.nombre,
      ),
    )


class RepositorioPrecio(RepositorioSQLBase[Precio, ModeloPrecio]):
  """Persiste importes asociados a libros y monedas."""

  modelo = ModeloPrecio

  def __init__(
    self,
    repo_libro: RepositorioLibro,
    repo_moneda: RepositorioMoneda,
    conexion: ConexionDB | None = None,
  ) -> None:
    conexion_resuelta = conexion or repo_libro._conexion
    if (
      repo_libro._conexion is not conexion_resuelta
      or repo_moneda._conexion is not conexion_resuelta
    ):
      raise ValueError("Los repositorios relacionados deben usar la misma conexión.")
    super().__init__(conexion_resuelta)

  def _crear_modelo(self, entidad: Precio) -> ModeloPrecio:
    return ModeloPrecio(
      id=entidad.id,
      libro_id=entidad.libro.id,
      moneda_id=entidad.moneda.id,
      monto=entidad.monto,
    )

  def _actualizar_modelo(
    self, modelo: ModeloPrecio, entidad: Precio
  ) -> None:
    modelo.libro_id = entidad.libro.id
    modelo.moneda_id = entidad.moneda.id
    modelo.monto = entidad.monto

  def _a_entidad(self, modelo: ModeloPrecio) -> Precio:
    return Precio(
      id=modelo.id,
      libro=Libro(
        id=modelo.libro.id,
        isbn=modelo.libro.isbn,
        titulo=modelo.libro.titulo,
        autor=modelo.libro.autor,
        editorial=Editorial(
          id=modelo.libro.editorial.id,
          nombre=modelo.libro.editorial.nombre,
          pais=modelo.libro.editorial.pais,
        ),
        genero=Genero(
          id=modelo.libro.genero.id,
          nombre=modelo.libro.genero.nombre,
        ),
      ),
      moneda=Moneda(
        id=modelo.moneda.id,
        codigo=modelo.moneda.codigo,
        nombre=modelo.moneda.nombre,
      ),
      monto=float(modelo.monto),
    )


class RepositorioStock(
  RepositorioSQLBase[Stock, ModeloStock], IRepositorioStock
):
  """Persiste existencias y permite consultarlas por libro."""

  modelo = ModeloStock

  def __init__(
    self,
    repo_libro: RepositorioLibro,
    conexion: ConexionDB | None = None,
  ) -> None:
    if conexion is not None and conexion is not repo_libro._conexion:
      raise ValueError("Los repositorios relacionados deben usar la misma conexión.")
    super().__init__(repo_libro._conexion)

  def _crear_modelo(self, entidad: Stock) -> ModeloStock:
    return ModeloStock(
      id=entidad.id,
      libro_id=entidad.libro.id,
      cantidad=entidad.cantidad,
    )

  def _actualizar_modelo(
    self, modelo: ModeloStock, entidad: Stock
  ) -> None:
    modelo.libro_id = entidad.libro.id
    modelo.cantidad = entidad.cantidad

  def _a_entidad(self, modelo: ModeloStock) -> Stock:
    return Stock(
      id=modelo.id,
      libro=Libro(
        id=modelo.libro.id,
        isbn=modelo.libro.isbn,
        titulo=modelo.libro.titulo,
        autor=modelo.libro.autor,
        editorial=Editorial(
          id=modelo.libro.editorial.id,
          nombre=modelo.libro.editorial.nombre,
          pais=modelo.libro.editorial.pais,
        ),
        genero=Genero(
          id=modelo.libro.genero.id,
          nombre=modelo.libro.genero.nombre,
        ),
      ),
      cantidad=modelo.cantidad,
    )

  def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.scalar(
        select(self.modelo).where(self.modelo.libro_id == libro_id)
      )
      return self._a_entidad(modelo) if modelo is not None else None

  def eliminar(self, libro_id: int) -> bool:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.scalar(
        select(self.modelo).where(self.modelo.libro_id == libro_id)
      )
      if modelo is None:
        return False
      sesion.delete(modelo)
    return True


class RepositorioCotizacionDolar(
  RepositorioSQLBase[CotizacionDolar, ModeloCotizacionDolar],
  IRepositorioCotizacionDolar,
):
  """Persiste y consulta el historial de cotizaciones."""

  modelo = ModeloCotizacionDolar

  def __init__(
    self,
    repo_tipo: RepositorioTipoCotizacion,
    conexion: ConexionDB | None = None,
  ) -> None:
    if conexion is not None and conexion is not repo_tipo._conexion:
      raise ValueError("Los repositorios relacionados deben usar la misma conexión.")
    super().__init__(repo_tipo._conexion)

  def _crear_modelo(
    self, entidad: CotizacionDolar
  ) -> ModeloCotizacionDolar:
    return ModeloCotizacionDolar(
      id=entidad.id,
      tipo_id=entidad.tipo.id,
      fecha=_fecha_como_date(entidad.fecha),
      valor_compra=entidad.valor_compra,
      valor_venta=entidad.valor_venta,
    )

  def _actualizar_modelo(
    self, modelo: ModeloCotizacionDolar, entidad: CotizacionDolar
  ) -> None:
    modelo.tipo_id = entidad.tipo.id
    modelo.fecha = _fecha_como_date(entidad.fecha)
    modelo.valor_compra = entidad.valor_compra
    modelo.valor_venta = entidad.valor_venta

  def _a_entidad(self, modelo: ModeloCotizacionDolar) -> CotizacionDolar:
    return CotizacionDolar(
      id=modelo.id,
      tipo=TipoCotizacion(
        id=modelo.tipo.id, nombre=modelo.tipo.nombre
      ),
      fecha=modelo.fecha,
      valor_compra=float(modelo.valor_compra),
      valor_venta=float(modelo.valor_venta),
    )

  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: str
  ) -> Optional[CotizacionDolar]:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.scalar(
        select(self.modelo).where(
          self.modelo.tipo_id == tipo_id,
          self.modelo.fecha == _fecha_como_date(fecha),
        )
      )
      return self._a_entidad(modelo) if modelo is not None else None

  def leer_historico_por_tipo(
    self, tipo_id: int
  ) -> list[CotizacionDolar]:
    with self._conexion.transaccion() as sesion:
      modelos = sesion.scalars(
        select(self.modelo)
        .where(self.modelo.tipo_id == tipo_id)
        .order_by(self.modelo.fecha)
      ).all()
      return [self._a_entidad(modelo) for modelo in modelos]

  def eliminar(self, tipo_id: int, fecha: str) -> bool:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.scalar(
        select(self.modelo).where(
          self.modelo.tipo_id == tipo_id,
          self.modelo.fecha == _fecha_como_date(fecha),
        )
      )
      if modelo is None:
        return False
      sesion.delete(modelo)
    return True
