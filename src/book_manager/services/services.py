"""Operaciones de negocio que coordinan entidades y repositorios."""
from __future__ import annotations

import json
import os
import unicodedata
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

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

_RUTA_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=_RUTA_ENV)
URL_API_DOLAR: str = os.getenv(
  "API_URL", "https://dolarapi.com/v1/dolares"
)

_ALIAS_TIPOS_API = {
  "bolsa": "mep",
  "dolarbolsa": "mep",
  "contadoconliqui": "ccl",
  "contadoconliquidacion": "ccl",
  "solidario": "ahorro",
}


def _normalizar_nombre_tipo(nombre: str) -> str:
  normalizado = unicodedata.normalize("NFKD", nombre.casefold())
  return "".join(caracter for caracter in normalizado if caracter.isalnum())


def _fecha_cotizacion(item: Dict, fecha_actual: date) -> date:
  fecha = item.get("fechaActualizacion") or item.get("fecha")
  if not fecha:
    return fecha_actual
  try:
    return datetime.fromisoformat(
      str(fecha).replace("Z", "+00:00")
    ).date()
  except ValueError as error:
    raise ValueError(
      f"Fecha de cotización inválida recibida de la API: {fecha!r}."
    ) from error


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
      if not isinstance(datos, list):
        raise ValueError("La API del dólar devolvió un formato inesperado.")
      nombre_normalizado = _normalizar_nombre_tipo(nombre_tipo)
      for item in datos:
        if not isinstance(item, dict):
          continue
        nombre_api = _normalizar_nombre_tipo(
          str(item.get("nombre", ""))
        )
        nombre_api = _ALIAS_TIPOS_API.get(nombre_api, nombre_api)
        if nombre_api == nombre_normalizado:
          return float(item["compra"]), float(item["venta"])
      return None
    except (OSError, ValueError, KeyError, TypeError):
      return None

  def obtener_cotizaciones(self) -> List[CotizacionDolar]:
    """Descarga y registra las cotizaciones para los tipos configurados."""
    peticion = urllib.request.Request(
      URL_API_DOLAR,
      headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(peticion, timeout=5) as respuesta:
      datos = json.loads(respuesta.read())
    if not isinstance(datos, list):
      raise ValueError("La API del dólar devolvió un formato inesperado.")

    tipos_por_nombre = {
      _normalizar_nombre_tipo(tipo.nombre): tipo
      for tipo in self._repo_tipo.leer_todos()
    }
    cotizaciones: List[CotizacionDolar] = []
    hoy = date.today()

    for item in datos:
      if not isinstance(item, dict):
        continue
      nombre_api = _normalizar_nombre_tipo(str(item.get("nombre", "")))
      nombre_tipo = _ALIAS_TIPOS_API.get(nombre_api, nombre_api)
      tipo = tipos_por_nombre.get(nombre_tipo)
      if tipo is None:
        continue

      try:
        valor_compra = float(item["compra"])
        valor_venta = float(item["venta"])
      except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
          f"La cotización recibida para {tipo.nombre!r} no contiene "
          "valores válidos de compra y venta."
        ) from error

      fecha = _fecha_cotizacion(item, hoy)
      existente = self._repo_cotizacion.leer_por_tipo_y_fecha(
        tipo.id, fecha.isoformat()
      )
      if existente is None:
        cotizacion = CotizacionDolar(
          tipo=tipo,
          fecha=fecha,
          valor_compra=valor_compra,
          valor_venta=valor_venta,
        )
        cotizacion = self._repo_cotizacion.crear(cotizacion)
      else:
        existente.valor_compra = valor_compra
        existente.valor_venta = valor_venta
        cotizacion = self._repo_cotizacion.actualizar(existente)
      cotizaciones.append(cotizacion)

    return cotizaciones

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
    existente = self._repo_cotizacion.leer_por_tipo_y_fecha(
      tipo_id, fecha_real
    )
    if existente is not None:
      existente.valor_compra = valor_compra
      existente.valor_venta = valor_venta
      return self._repo_cotizacion.actualizar(existente)
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


ServicioCotizacionDolar = ServicioCotizacion


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
