"""Menús de texto para operar el inventario de la librería."""
from __future__ import annotations

from typing import Optional

from book_manager.entities.entities import (
  Editorial, Genero, Libro, Moneda, TipoCotizacion,
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
from book_manager.services.services import (
  ServicioCotizacion,
  ServicioLibro,
  ServicioPrecio,
  ServicioStock,
)


def _confirmar_accion(mensaje: str) -> bool:
  """Solicita confirmación antes de continuar con una operación."""
  respuesta: str = input(f"{mensaje} [s/n]: ").strip().lower()
  return respuesta == "s"


def menu_generos(repo_genero: RepositorioGenero) -> None:
  """Presenta los géneros guardados y ofrece agregar otro."""
  print("\n--- Géneros registrados ---")
  for genero in repo_genero.leer_todos():
    print(f"  {genero}")

  if not _confirmar_accion("\n¿Quiere agregar un género?"):
    print("No se hicieron cambios.")
    return

  nombre: str = input("Indique el nombre del género: ")
  nuevo: Genero = repo_genero.crear(Genero(nombre=nombre))
  print(f"Género incorporado: {nuevo}")


def menu_editoriales(repo_editorial: RepositorioEditorial) -> None:
  """Muestra las editoriales registradas y permite crear una."""
  print("\n--- Editoriales registradas ---")
  for editorial in repo_editorial.leer_todos():
    print(f"  {editorial}")

  if not _confirmar_accion("\n¿Quiere sumar una editorial?"):
    print("No se hicieron cambios.")
    return

  nombre: str = input("Indique el nombre de la editorial: ")
  pais: str = input("País de origen: ")
  nueva: Editorial = repo_editorial.crear(
    Editorial(nombre=nombre, pais=pais)
  )
  print(f"Editorial incorporada: {nueva}")


def menu_monedas(repo_moneda: RepositorioMoneda) -> None:
  """Enumera las monedas disponibles y permite incorporar otra."""
  print("\n--- Monedas disponibles ---")
  for moneda in repo_moneda.leer_todos():
    print(f"  {moneda}")

  if not _confirmar_accion("\n¿Quiere registrar otra moneda?"):
    print("No se hicieron cambios.")
    return

  codigo: str = input("Código de moneda (por ejemplo, ARS): ")
  nombre: str = input("Denominación de la moneda: ")
  nueva: Moneda = repo_moneda.crear(
    Moneda(codigo=codigo, nombre=nombre)
  )
  print(f"Moneda añadida: {nueva}")


def menu_tipos_cotizacion(
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Gestiona las variantes de cotización registradas."""
  print("\n--- Variantes de cotización configuradas ---")
  for tipo in repo_tipo.leer_todos():
    print(f"  {tipo}")

  if not _confirmar_accion(
    "\n¿Quiere agregar una variante de cotización?"
  ):
    print("No se hicieron cambios.")
    return

  nombre: str = input("Nombre de la variante: ")
  nuevo: TipoCotizacion = repo_tipo.crear(
    TipoCotizacion(nombre=nombre)
  )
  print(f"Variante registrada: {nuevo}")


def menu_libros(
  servicio_libro: ServicioLibro,
  repo_libro: RepositorioLibro,
  repo_editorial: RepositorioEditorial,
  repo_genero: RepositorioGenero,
  repo_moneda: RepositorioMoneda,
) -> None:
  """Muestra el catálogo y guía el alta de una nueva obra."""
  print("\n--- Libros del catálogo ---")
  for libro in repo_libro.leer_todos():
    print(f"  {libro}")

  if not _confirmar_accion("\n¿Quiere incorporar un libro nuevo?"):
    print("No se hicieron cambios.")
    return

  if not repo_editorial.leer_todos() or not repo_genero.leer_todos():
    print("Registre primero una editorial y un género para continuar.")
    return

  isbn: str = input("Código ISBN: ")
  titulo: str = input("Título de la obra: ")
  autor: str = input("Nombre del autor (opcional): ").strip() or "Desconocido"

  for e in repo_editorial.leer_todos():
    print(f"  [{e.id}] {e.nombre}")
  editorial_id: int = int(input("Identificador de la editorial: "))
  editorial: Optional[Editorial] = repo_editorial.leer_por_id(
    editorial_id
  )
  if editorial is None:
    print(f"No se encontró la editorial con identificador {editorial_id}.")
    return

  for g in repo_genero.leer_todos():
    print(f"  [{g.id}] {g.nombre}")
  genero_id: int = int(input("Identificador del género: "))
  genero: Optional[Genero] = repo_genero.leer_por_id(genero_id)
  if genero is None:
    print(f"No se encontró el género con identificador {genero_id}.")
    return

  precio_ars: float = float(input("Importe en pesos argentinos (ARS): "))
  precio_usd: float = float(input("Importe en dólares (USD): "))
  cantidad: int = int(input("Unidades iniciales disponibles: "))

  moneda_ars: Optional[Moneda] = next(
    (m for m in repo_moneda.leer_todos() if m.codigo == "ARS"),
    None,
  )
  moneda_usd: Optional[Moneda] = next(
    (m for m in repo_moneda.leer_todos() if m.codigo == "USD"),
    None,
  )

  nuevo: Libro = servicio_libro.registrar_libro(
    isbn=isbn,
    titulo=titulo,
    autor=autor,
    editorial=editorial,
    genero=genero,
    precio_ars=precio_ars,
    precio_usd=precio_usd,
    moneda_ars=moneda_ars,
    moneda_usd=moneda_usd,
    cantidad_inicial=cantidad,
  )
  print(f"Libro agregado al catálogo: {nuevo}")


def _obtener_o_cargar_cotizacion(
  servicio_cotizacion: ServicioCotizacion,
  tipo: TipoCotizacion,
) -> None:
  """Obtiene una cotización guardada o solicita una nueva."""
  cotizacion = servicio_cotizacion.obtener_ultima_cotizacion(
    tipo.id
  )
  if cotizacion is not None:
    return

  print(f"Todavía no hay valores guardados para \"{tipo.nombre}\".")
  print("Consultando la cotización actual...")
  resultado = servicio_cotizacion.obtener_cotizacion_automatica(
    tipo.nombre
  )

  if resultado is not None:
    valor_compra, valor_venta = resultado
    print(
      f"Valores recibidos de la fuente: "
      f"compra ${valor_compra}, venta ${valor_venta}"
    )
  else:
    print(
      "La consulta no devolvió valores.\n"
      "Cargue los importes de forma manual:"
    )
    valor_compra = float(input("Cotización de compra en ARS: "))
    valor_venta = float(input("Cotización de venta en ARS: "))

  servicio_cotizacion.registrar_cotizacion(
    tipo.id, valor_compra, valor_venta
  )


def menu_precios(
  servicio_precio: ServicioPrecio,
  servicio_cotizacion: ServicioCotizacion,
  repo_precio: RepositorioPrecio,
  repo_libro: RepositorioLibro,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Compara el precio en pesos con el cálculo basado en el dólar."""
  print("\n--- Precios registrados (ARS y USD) ---")
  for precio in repo_precio.leer_todos():
    print(f"  {precio}")

  if not _confirmar_accion(
    "\n¿Quiere recalcular el precio en ARS de un libro?"
  ):
    print("No se hicieron cambios.")
    return

  for l in repo_libro.leer_todos():
    print(f"  [{l.id}] {l.titulo}")
  libro_id: int = int(input("Identificador del libro: "))

  for t in repo_tipo.leer_todos():
    print(f"  [{t.id}] {t.nombre}")
  tipo_id: int = int(input("Identificador de la cotización: "))

  tipo: Optional[TipoCotizacion] = repo_tipo.leer_por_id(tipo_id)
  if tipo is None:
    print(f"No se encontró una cotización con identificador {tipo_id}.")
    return

  _obtener_o_cargar_cotizacion(servicio_cotizacion, tipo)

  try:
    actual, sugerido, diferencia = (
      servicio_precio.comparar_ars_vs_sugerido(libro_id, tipo_id)
    )
  except ValueError as error:
    print(f"No fue posible obtener el nuevo importe: {error}")
    return

  print(f"\nImporte vigente en ARS: ${actual}")
  print(f"Importe calculado con dólar {tipo.nombre}: ${sugerido}")
  print(f"Variación respecto al valor vigente: ${diferencia}")

  if _confirmar_accion("\n¿Guardar el importe calculado para este libro?"):
    actualizado = servicio_precio.aplicar_precio_ars(
      libro_id, sugerido
    )
    print(f"Nuevo precio guardado: {actualizado}")
  else:
    print("Se conservó el precio anterior.")


def menu_stock(
  servicio_stock: ServicioStock, repo_stock: RepositorioStock
) -> None:
  """Consulta las existencias y registra ingresos o egresos."""
  print("\n--- Existencias por libro ---")
  for stock in repo_stock.leer_todos():
    print(f"  {stock}")

  if not _confirmar_accion("\n¿Quiere ajustar las existencias?"):
    print("No se hicieron cambios.")
    return

  libro_id: int = int(input("Identificador del libro: "))
  cantidad: int = int(
    input("Unidades a ajustar (positivo para ingreso, negativo para egreso): ")
  )
  try:
    if cantidad >= 0:
      actualizado = servicio_stock.ingresar(libro_id, cantidad)
    else:
      actualizado = servicio_stock.egresar(
        libro_id, abs(cantidad)
      )
    print(f"Existencias actualizadas: {actualizado}")
  except ValueError as error:
    print(f"No se pudo ajustar el inventario: {error}")

def menu_cotizaciones(
  servicio_cotizacion: ServicioCotizacion,
  repo_cotizacion: RepositorioCotizacionDolar,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Revisa el historial y añade una cotización automática o manual."""
  print("\n--- Historial de cotizaciones ---")
  for cot in repo_cotizacion.leer_todos():
    print(f"  {cot}")

  if not _confirmar_accion(
    "\n¿Quiere añadir una nueva cotización?"
  ):
    print("No se hicieron cambios.")
    return

  for t in repo_tipo.leer_todos():
    print(f"  [{t.id}] {t.nombre}")
  tipo_id: int = int(input("Identificador de la variante: "))

  tipo: Optional[TipoCotizacion] = repo_tipo.leer_por_id(tipo_id)
  if tipo is None:
    print(f"No se encontró esa variante (identificador {tipo_id}).")
    return

  print(f"Buscando el valor actual para \"{tipo.nombre}\"...")
  resultado = servicio_cotizacion.obtener_cotizacion_automatica(
    tipo.nombre
  )

  if resultado is not None:
    valor_compra, valor_venta = resultado
    print(
      f"Cotización recibida de la fuente: "
      f"compra ${valor_compra}, venta ${valor_venta}"
    )
  else:
    print(
      "No se recibieron datos de la consulta.\n"
      "Puede ingresar los valores manualmente:"
    )
    valor_compra = float(input("Importe de compra en ARS: "))
    valor_venta = float(input("Importe de venta en ARS: "))

  try:
    nueva = servicio_cotizacion.registrar_cotizacion(
      tipo_id, valor_compra, valor_venta
    )
    print(f"Cotización incorporada al historial: {nueva}")
  except ValueError as error:
    print(f"No se pudo guardar la cotización: {error}")
