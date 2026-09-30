"""Persistencia CSV para las entidades del catálogo."""
from __future__ import annotations

import abc
import csv
import os
from typing import Dict, Generic, List, Optional, TypeVar

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

T = TypeVar("T", bound=EntidadBase)

RUTA_CSV: str = os.path.join(
  os.path.dirname(__file__), "..", "migrations", "csv"
)


class IRepositorio(abc.ABC, Generic[T]):
  """Contrato común para consultar y modificar entidades persistidas."""

  @abc.abstractmethod
  def crear(self, entidad: T) -> T:
    """Guarda una entidad nueva y la devuelve con su identificador."""

  @abc.abstractmethod
  def leer_por_id(self, id: int) -> Optional[T]:
    """Busca una entidad a partir de su identificador."""

  @abc.abstractmethod
  def leer_todos(self) -> List[T]:
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
    """Registra las existencias de un libro."""

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
  def crear(
    self, cotizacion: CotizacionDolar
  ) -> CotizacionDolar:
    """Añade un registro de cotización al historial."""

  @abc.abstractmethod
  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: str
  ) -> Optional[CotizacionDolar]:
    """Busca el registro de un tipo de dólar para una fecha."""

  @abc.abstractmethod
  def leer_historico_por_tipo(
    self, tipo_id: int
  ) -> List[CotizacionDolar]:
    """Devuelve las cotizaciones registradas para un tipo."""

  @abc.abstractmethod
  def actualizar(
    self, cotizacion: CotizacionDolar
  ) -> CotizacionDolar:
    """Actualiza un registro existente del historial."""

  @abc.abstractmethod
  def eliminar(self, tipo_id: int, fecha: str) -> bool:
    """Quita la cotización correspondiente al tipo y fecha."""


class RepositorioCSVBase(IRepositorio[T], abc.ABC):
  """Implementa el CRUD común y delega el formato CSV a sus subclases."""

  def __init__(self, nombre_archivo: str) -> None:
    self._ruta: str = os.path.join(RUTA_CSV, nombre_archivo)
    self._datos: Dict[int, T] = {}
    self._siguiente_id: int = 1
    self._cargar()

  @abc.abstractmethod
  def _encabezados(self) -> List[str]:
    """Indica qué columnas debe escribir el archivo."""

  @abc.abstractmethod
  def _a_fila(self, entidad: T) -> List[str]:
    """Serializa una entidad como valores de una fila."""

  @abc.abstractmethod
  def _desde_fila(self, fila: Dict[str, str]) -> T:
    """Reconstruye una entidad a partir de una fila leída."""

  def _cargar(self) -> None:
    if not os.path.exists(self._ruta):
      return
    with open(self._ruta, "r", newline="", encoding="utf-8") as f:
      lector = csv.DictReader(f)
      for fila in lector:
        entidad: T = self._desde_fila(fila)
        self._datos[entidad.id] = entidad
        self._siguiente_id = max(
          self._siguiente_id, entidad.id + 1
        )

  def _guardar(self) -> None:
    os.makedirs(os.path.dirname(self._ruta), exist_ok=True)
    with open(self._ruta, "w", newline="", encoding="utf-8") as f:
      escritor = csv.writer(f)
      escritor.writerow(self._encabezados())
      for entidad in self._datos.values():
        escritor.writerow(self._a_fila(entidad))

  def crear(self, entidad: T) -> T:
    entidad.id = self._siguiente_id
    self._siguiente_id += 1
    self._datos[entidad.id] = entidad
    self._guardar()
    return entidad

  def leer_por_id(self, id: int) -> Optional[T]:
    return self._datos.get(id)

  def leer_todos(self) -> List[T]:
    return list(self._datos.values())

  def actualizar(self, entidad: T) -> T:
    if entidad.id not in self._datos:
      raise ValueError(
        f"No se encontró la entidad con id={entidad.id}."
      )
    self._datos[entidad.id] = entidad
    self._guardar()
    return entidad

  def eliminar(self, id: int) -> bool:
    if id not in self._datos:
      return False
    del self._datos[id]
    self._guardar()
    return True


class RepositorioGenero(RepositorioCSVBase[Genero]):
  """Guarda los géneros disponibles en el catálogo."""

  def __init__(self) -> None:
    super().__init__("generos.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "nombre"]

  def _a_fila(self, entidad: Genero) -> List[str]:
    return [str(entidad.id), entidad.nombre]

  def _desde_fila(self, fila: Dict[str, str]) -> Genero:
    return Genero(nombre=fila["nombre"], id=int(fila["id"]))


class RepositorioEditorial(RepositorioCSVBase[Editorial]):
  """Mantiene los datos de las editoriales."""

  def __init__(self) -> None:
    super().__init__("editoriales.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "nombre", "pais"]

  def _a_fila(self, entidad: Editorial) -> List[str]:
    return [str(entidad.id), entidad.nombre, entidad.pais]

  def _desde_fila(self, fila: Dict[str, str]) -> Editorial:
    return Editorial(
      nombre=fila["nombre"],
      pais=fila["pais"],
      id=int(fila["id"]),
    )


class RepositorioMoneda(RepositorioCSVBase[Moneda]):
  """Persiste las monedas habilitadas para los precios."""

  def __init__(self) -> None:
    super().__init__("monedas.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "codigo", "nombre"]

  def _a_fila(self, entidad: Moneda) -> List[str]:
    return [str(entidad.id), entidad.codigo, entidad.nombre]

  def _desde_fila(self, fila: Dict[str, str]) -> Moneda:
    return Moneda(
      codigo=fila["codigo"],
      nombre=fila["nombre"],
      id=int(fila["id"]),
    )


class RepositorioTipoCotizacion(
  RepositorioCSVBase[TipoCotizacion]
):
  """Almacena las variantes de cotización configuradas."""

  def __init__(self) -> None:
    super().__init__("tipos_cotizacion.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "nombre"]

  def _a_fila(self, entidad: TipoCotizacion) -> List[str]:
    return [str(entidad.id), entidad.nombre]

  def _desde_fila(
    self, fila: Dict[str, str]
  ) -> TipoCotizacion:
    return TipoCotizacion(
      nombre=fila["nombre"], id=int(fila["id"])
    )


class RepositorioLibro(RepositorioCSVBase[Libro]):
  """Persiste libros junto con sus referencias de catálogo."""

  def __init__(
    self,
    repo_editorial: RepositorioEditorial,
    repo_genero: RepositorioGenero,
  ) -> None:
    self._repo_editorial = repo_editorial
    self._repo_genero = repo_genero
    super().__init__("libros.csv")

  def _encabezados(self) -> List[str]:
    return [
      "id", "isbn", "titulo", "autor",
      "editorial_id", "genero_id",
    ]

  def _a_fila(self, entidad: Libro) -> List[str]:
    return [
      str(entidad.id),
      entidad.isbn,
      entidad.titulo,
      entidad.autor,
      str(entidad.editorial.id),
      str(entidad.genero.id),
    ]

  def _desde_fila(self, fila: Dict[str, str]) -> Libro:
    editorial: Optional[Editorial] = (
      self._repo_editorial.leer_por_id(
        int(fila["editorial_id"])
      )
    )
    genero: Optional[Genero] = (
      self._repo_genero.leer_por_id(int(fila["genero_id"]))
    )
    return Libro(
      isbn=fila["isbn"],
      titulo=fila["titulo"],
      autor=fila["autor"],
      editorial=editorial,
      genero=genero,
      id=int(fila["id"]),
    )


class RepositorioPrecio(RepositorioCSVBase[Precio]):
  """Registra el importe asociado a cada libro y moneda."""

  def __init__(
    self,
    repo_libro: RepositorioLibro,
    repo_moneda: RepositorioMoneda,
  ) -> None:
    self._repo_libro = repo_libro
    self._repo_moneda = repo_moneda
    super().__init__("precios.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "libro_id", "moneda_id", "monto"]

  def _a_fila(self, entidad: Precio) -> List[str]:
    return [
      str(entidad.id),
      str(entidad.libro.id),
      str(entidad.moneda.id),
      str(entidad.monto),
    ]

  def _desde_fila(self, fila: Dict[str, str]) -> Precio:
    libro: Optional[Libro] = (
      self._repo_libro.leer_por_id(int(fila["libro_id"]))
    )
    moneda: Optional[Moneda] = (
      self._repo_moneda.leer_por_id(int(fila["moneda_id"]))
    )
    return Precio(
      libro=libro,
      moneda=moneda,
      monto=float(fila["monto"]),
      id=int(fila["id"]),
    )


class RepositorioStock(
  RepositorioCSVBase[Stock], IRepositorioStock
):
  """Guarda existencias y permite consultarlas por libro."""

  def __init__(self, repo_libro: RepositorioLibro) -> None:
    self._repo_libro = repo_libro
    super().__init__("stocks.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "libro_id", "cantidad"]

  def _a_fila(self, entidad: Stock) -> List[str]:
    return [
      str(entidad.id),
      str(entidad.libro.id),
      str(entidad.cantidad),
    ]

  def _desde_fila(self, fila: Dict[str, str]) -> Stock:
    libro: Optional[Libro] = (
      self._repo_libro.leer_por_id(int(fila["libro_id"]))
    )
    return Stock(
      libro=libro,
      cantidad=int(fila["cantidad"]),
      id=int(fila["id"]),
    )

  def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
    for stock in self._datos.values():
      if stock.libro.id == libro_id:
        return stock
    return None

  def eliminar(self, libro_id: int) -> bool:
    stock: Optional[Stock] = self.leer_por_libro(libro_id)
    if stock is None:
      return False
    return super().eliminar(stock.id)


class RepositorioCotizacionDolar(
  RepositorioCSVBase[CotizacionDolar],
  IRepositorioCotizacionDolar,
):
  """Conserva los valores de compra y venta en el tiempo."""

  def __init__(
    self, repo_tipo: RepositorioTipoCotizacion
  ) -> None:
    self._repo_tipo = repo_tipo
    super().__init__("cotizaciones.csv")

  def _encabezados(self) -> List[str]:
    return [
      "id", "tipo_id", "fecha",
      "valor_compra", "valor_venta",
    ]

  def _a_fila(self, entidad: CotizacionDolar) -> List[str]:
    return [
      str(entidad.id),
      str(entidad.tipo.id),
      entidad.fecha,
      str(entidad.valor_compra),
      str(entidad.valor_venta),
    ]

  def _desde_fila(
    self, fila: Dict[str, str]
  ) -> CotizacionDolar:
    tipo: Optional[TipoCotizacion] = (
      self._repo_tipo.leer_por_id(int(fila["tipo_id"]))
    )
    return CotizacionDolar(
      tipo=tipo,
      fecha=fila["fecha"],
      valor_compra=float(fila["valor_compra"]),
      valor_venta=float(fila["valor_venta"]),
      id=int(fila["id"]),
    )

  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: str
  ) -> Optional[CotizacionDolar]:
    for cot in self._datos.values():
      if cot.tipo.id == tipo_id and cot.fecha == fecha:
        return cot
    return None

  def leer_historico_por_tipo(
    self, tipo_id: int
  ) -> List[CotizacionDolar]:
    return [
      cot for cot in self._datos.values()
      if cot.tipo.id == tipo_id
    ]

  def eliminar(self, tipo_id: int, fecha: str) -> bool:
    cot: Optional[CotizacionDolar] = (
      self.leer_por_tipo_y_fecha(tipo_id, fecha)
    )
    if cot is None:
      return False
    return super().eliminar(cot.id)
