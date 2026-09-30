"""Operaciones de negocio que coordinan entidades y repositorios."""
from __future__ import annotations

import json
import urllib.request
from datetime import date
from typing import Dict, List, Optional, Tuple

from book_manager.entities.entities import (
  CotizacionDolar,
  Editorial,
  Genero,
  Libro,
  Moneda,
  Precio,
  Stock,
  TipoCotizacion,
)
from book_manager.repositories.repositories import (
  RepositorioCotizacionDolar,
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioLibro,
  RepositorioMoneda,
  RepositorioPrecio,
  RepositorioStock,
  RepositorioTipoCotizacion,
)

URL_API_DOLAR: str = "https://dolarapi.com/v1/dolares"


class ServicioCotizacion:
  """Consulta y administra valores históricos del dólar.

  La consulta remota puede fallar; el registro manual permite mantener
  la operatoria disponible en ese caso.
  """

  def __init__(
    self,
    repo_cotizacion: RepositorioCotizacionDolar,
    repo_tipo: RepositorioTipoCotizacion,
  ) -> None:
    self._repo_cotizacion = repo_cotizacion
    self._repo_tipo = repo_tipo

  def obtener_cotizacion_automatica(
    self, nombre_tipo: str
  ) -> Optional[Tuple[float, float]]:
    """Busca en la API los valores de compra y venta del tipo indicado."""
    peticion = urllib.request.Request(
      URL_API_DOLAR,
      headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
      with urllib.request.urlopen(
        peticion, timeout=5
      ) as respuesta:
        datos: List[Dict] = json.loads(respuesta.read())
      for item in datos:
        if str(item.get("nombre", "")).lower() == (
          nombre_tipo.lower()
        ):
          compra: float = float(item.get("compra", 0.0) or 0.0)
          venta: float = float(item.get("venta", 0.0) or 0.0)
          return compra, venta
      return None
    except Exception:
      return None

  def registrar_cotizacion(
    self,
    tipo_id: int,
    valor_compra: float,
    valor_venta: float,
    fecha: Optional[str] = None,
  ) -> CotizacionDolar:
    """Guarda una cotización y usa la fecha actual si no se especifica."""
    tipo: Optional[TipoCotizacion] = self._repo_tipo.leer_por_id(
      tipo_id
    )
    if tipo is None:
      raise ValueError(f"No existe el tipo id={tipo_id}.")
    fecha_real: str = fecha or date.today().isoformat()
    cotizacion: CotizacionDolar = CotizacionDolar(
      tipo=tipo,
      fecha=fecha_real,
      valor_compra=valor_compra,
      valor_venta=valor_venta,
    )
    return self._repo_cotizacion.crear(cotizacion)

  def obtener_ultima_cotizacion(
    self, tipo_id: int
  ) -> Optional[CotizacionDolar]:
    """Devuelve el registro más reciente del tipo solicitado."""
    historico: List[CotizacionDolar] = (
      self._repo_cotizacion.leer_historico_por_tipo(tipo_id)
    )
    if not historico:
      return None
    return max(historico, key=lambda c: c.fecha)


class ServicioPrecio:
  """Consulta y actualiza precios expresados en distintas monedas."""

  def __init__(
    self,
    repo_precio: RepositorioPrecio,
    repo_moneda: RepositorioMoneda,
    servicio_cotizacion: ServicioCotizacion,
  ) -> None:
    self._repo_precio = repo_precio
    self._repo_moneda = repo_moneda
    self._servicio_cotizacion = servicio_cotizacion

  def precios_de_libro(self, libro_id: int) -> List[Precio]:
    """Lista los importes asociados al identificador del libro."""
    return [
      p for p in self._repo_precio.leer_todos()
      if p.libro.id == libro_id
    ]

  def precio_por_moneda(
    self, libro_id: int, codigo_moneda: str
  ) -> Optional[Precio]:
    """Encuentra el precio del libro correspondiente a una divisa."""
    for precio in self.precios_de_libro(libro_id):
      if precio.moneda.codigo == codigo_moneda.upper():
        return precio
    return None

  def sugerir_precio_ars(
    self, libro_id: int, tipo_cotizacion_id: int
  ) -> float:
    """Calcula un valor en ARS a partir del precio en USD y el dólar."""
    precio_usd: Optional[Precio] = self.precio_por_moneda(
      libro_id, "USD"
    )
    if precio_usd is None:
      raise ValueError("El libro no tiene precio en USD.")
    cotizacion: Optional[CotizacionDolar] = (
      self._servicio_cotizacion.obtener_ultima_cotizacion(
        tipo_cotizacion_id
      )
    )
    if cotizacion is None:
      raise ValueError("No hay cotización registrada.")
    return round(precio_usd.monto * cotizacion.valor_venta, 2)

  def comparar_ars_vs_sugerido(
    self, libro_id: int, tipo_cotizacion_id: int
  ) -> Tuple[float, float, float]:
    """Devuelve el precio actual, el calculado y la diferencia entre ambos."""
    precio_ars: Optional[Precio] = self.precio_por_moneda(
      libro_id, "ARS"
    )
    if precio_ars is None:
      raise ValueError("El libro no tiene precio en ARS.")
    sugerido: float = self.sugerir_precio_ars(
      libro_id, tipo_cotizacion_id
    )
    diferencia: float = round(sugerido - precio_ars.monto, 2)
    return precio_ars.monto, sugerido, diferencia

  def aplicar_precio_ars(
    self, libro_id: int, monto_ars: float
  ) -> Precio:
    """Reemplaza el importe en pesos y persiste la modificación."""
    precio_ars: Optional[Precio] = self.precio_por_moneda(
      libro_id, "ARS"
    )
    if precio_ars is None:
      raise ValueError("El libro no tiene precio en ARS.")
    precio_ars.monto = monto_ars
    return self._repo_precio.actualizar(precio_ars)


class ServicioStock:
  """Coordina ingresos y egresos de unidades del inventario."""

  def __init__(self, repo_stock: RepositorioStock) -> None:
    self._repo_stock = repo_stock

  def ingresar(self, libro_id: int, cantidad: int) -> Stock:
    """Suma unidades disponibles para el libro indicado."""
    stock: Optional[Stock] = self._repo_stock.leer_por_libro(
      libro_id
    )
    if stock is None:
      raise ValueError(
        f"No existe stock para el libro id={libro_id}."
      )
    stock.cantidad = stock.cantidad + cantidad
    return self._repo_stock.actualizar(stock)

  def egresar(self, libro_id: int, cantidad: int) -> Stock:
    """Descuenta unidades solo cuando hay cantidad suficiente."""
    stock: Optional[Stock] = self._repo_stock.leer_por_libro(
      libro_id
    )
    if stock is None:
      raise ValueError(
        f"No existe stock para el libro id={libro_id}."
      )
    if stock.cantidad < cantidad:
      raise ValueError("Stock insuficiente para el egreso.")
    stock.cantidad = stock.cantidad - cantidad
    return self._repo_stock.actualizar(stock)


class ServicioLibro:
  """Coordina el alta de títulos y las consultas del catálogo."""

  def __init__(
    self,
    repo_libro: RepositorioLibro,
    repo_precio: RepositorioPrecio,
    repo_stock: RepositorioStock,
  ) -> None:
    self._repo_libro = repo_libro
    self._repo_precio = repo_precio
    self._repo_stock = repo_stock

  def registrar_libro(
    self,
    isbn: str,
    titulo: str,
    autor: str,
    editorial: Editorial,
    genero: Genero,
    precio_ars: float,
    precio_usd: float,
    moneda_ars: Moneda,
    moneda_usd: Moneda,
    cantidad_inicial: int,
  ) -> Libro:
    """Registra un título junto con sus precios y existencias iniciales."""
    libro: Libro = self._repo_libro.crear(
      Libro(
        isbn=isbn,
        titulo=titulo,
        autor=autor,
        editorial=editorial,
        genero=genero,
      )
    )
    self._repo_precio.crear(
      Precio(libro=libro, moneda=moneda_ars, monto=precio_ars)
    )
    self._repo_precio.crear(
      Precio(libro=libro, moneda=moneda_usd, monto=precio_usd)
    )
    self._repo_stock.crear(
      Stock(libro=libro, cantidad=cantidad_inicial)
    )
    return libro

  def buscar_por_genero(self, genero_id: int) -> List[Libro]:
    """Filtra el catálogo por el identificador de género."""
    return [
      l for l in self._repo_libro.leer_todos()
      if l.genero.id == genero_id
    ]
