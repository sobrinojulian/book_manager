"""Menús de texto para operar el inventario de la librería."""
from __future__ import annotations

import csv
import os
from pathlib import Path
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from book_manager.entities.entities import (
  Editorial, Genero, Libro, Moneda, TipoCotizacion,
)
from book_manager.repositories.repositories import (
  RepositorioCotizacionDolar,
  RepositorioAuditoria,
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
from book_manager.scraper.pipelines import generar_reporte_desde_jsonl


def _confirmar_accion(mensaje: str) -> bool:
  """Solicita confirmación antes de continuar con una operación."""
  respuesta: str = input(f"{mensaje} [s/n]: ").strip().lower()
  return respuesta == "s"


def menu_ejecutar_scraper_cuspide() -> None:
  """Solicita el umbral y ejecuta el spider en un proceso independiente."""
  valor_ingresado = input(
    "Alertar cuando la diferencia supere este valor (ARS): "
  ).strip().replace(",", ".")
  try:
    umbral = Decimal(valor_ingresado)
  except InvalidOperation:
    print("La diferencia debe ser un número válido.")
    return
  if not umbral.is_finite() or umbral < 0:
    print("La diferencia debe ser mayor o igual a cero.")
    return

  raiz_proyecto = Path(__file__).resolve().parents[3]
  entorno = os.environ.copy()
  ruta_src = str(raiz_proyecto / "src")
  rutas_python = [ruta_src, entorno.get("PYTHONPATH", "")]
  entorno["PYTHONPATH"] = os.pathsep.join(
    ruta for ruta in rutas_python if ruta
  )
  comando = [
    sys.executable,
    "-m",
    "scrapy",
    "crawl",
    "cuspide",
    "-a",
    f"diferencia_minima_ars={umbral}",
  ]

  try:
    resultado = subprocess.run(
      comando, cwd=raiz_proyecto, env=entorno, check=False
    )
  except OSError as error:
    print(f"No se pudo ejecutar el scraper: {error}")
    return

  if resultado.returncode != 0:
    print("El scraper finalizó con errores; revise el registro anterior.")
    return

  print(
    "La ejecución finalizó. El CSV de alertas está en: "
    f"{raiz_proyecto / 'src' / 'book_manager' / 'reportes'}"
  )


def menu_historial_auditoria(repo_auditoria: RepositorioAuditoria) -> None:
  """Muestra los eventos más recientes registrados en el sistema."""
  print("\n--- Historial de auditoría ---")
  registros = repo_auditoria.leer_todos()
  if not registros:
    print("Todavía no hay operaciones auditadas.")
    return
  for registro in registros:
    print(
      f"[{registro.fecha.isoformat()}] {registro.accion}: "
      f"{registro.detalles}"
    )


def menu_generar_reporte() -> None:
  """Regenera el Excel de la extracción de Cúspide más reciente."""
  directorio_reportes = (
    Path(__file__).resolve().parents[2] / "reportes"
  )
  extracciones = list(directorio_reportes.glob("cuspide_*.jsonl"))
  if not extracciones:
    print("No hay extracciones guardadas para generar un reporte.")
    return

  ultima_extraccion = max(extracciones, key=lambda ruta: ruta.stat().st_mtime)
  try:
    ruta_reporte = generar_reporte_desde_jsonl(ultima_extraccion)
  except (OSError, ValueError) as error:
    print(f"No se pudo generar el reporte: {error}")
    return
  print(f"Reporte generado: {ruta_reporte}")


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


def menu_obtener_cotizaciones(
  servicio_cotizacion: ServicioCotizacion,
) -> None:
  """Descarga cotizaciones de la API y las registra en la base de datos."""
  print("\n--- Actualización de cotizaciones por API ---")
  try:
    cotizaciones = servicio_cotizacion.obtener_cotizaciones()
  except (OSError, ValueError, SQLAlchemyError) as error:
    print(f"No se pudieron obtener o guardar las cotizaciones: {error}")
    return

  if not cotizaciones:
    print("La API no devolvió cotizaciones para los tipos configurados.")
    return

  print(f"Se registraron {len(cotizaciones)} cotizaciones:")
  for cotizacion in cotizaciones:
    print(f"  {cotizacion}")


def menu_precios_bimonetarios(
  repo_precio: RepositorioPrecio,
  repo_libro: RepositorioLibro,
  repo_moneda: RepositorioMoneda,
) -> None:
  """Muestra los precios en ARS y en una moneda elegida."""
  monedas = [
    moneda for moneda in repo_moneda.leer_todos()
    if moneda.codigo != "ARS"
  ]
  if not monedas:
    print("No hay monedas disponibles además de ARS.")
    return

  print("\n--- Monedas para la consulta bimonetaria ---")
  for moneda in monedas:
    print(f"  [{moneda.id}] {moneda.codigo} - {moneda.nombre}")
  try:
    moneda_id = int(input("Identificador de la moneda: "))
  except ValueError:
    print("El identificador debe ser un número.")
    return

  moneda_seleccionada = next(
    (moneda for moneda in monedas if moneda.id == moneda_id),
    None,
  )
  if moneda_seleccionada is None:
    print(f"No se encontró una moneda con identificador {moneda_id}.")
    return

  libros = repo_libro.leer_todos()
  precios_por_libro_y_moneda = {
    (precio.libro.id, precio.moneda.codigo): precio.monto
    for precio in repo_precio.leer_todos()
  }
  print(
    f"\n--- Precios en ARS y {moneda_seleccionada.codigo} ---"
  )
  if not libros:
    print("No hay libros registrados.")
    return

  for libro in libros:
    precio_ars = precios_por_libro_y_moneda.get((libro.id, "ARS"))
    precio_otro = precios_por_libro_y_moneda.get(
      (libro.id, moneda_seleccionada.codigo)
    )
    importe_ars = (
      f"{precio_ars:.2f}" if precio_ars is not None else "Sin precio"
    )
    importe_otro = (
      f"{precio_otro:.2f}" if precio_otro is not None else "Sin precio"
    )
    print(
      f"  [{libro.id}] {libro.titulo}: "
      f"ARS {importe_ars} | {moneda_seleccionada.codigo} {importe_otro}"
    )


def menu_exportar_precios_csv(
  repo_precio: RepositorioPrecio,
) -> None:
  """Exporta todos los precios registrados, sin filtrar por moneda."""
  ruta_ingresada = input(
    "Ruta del archivo CSV [precios_exportados.csv]: "
  ).strip()
  ruta = Path(ruta_ingresada or "precios_exportados.csv")

  try:
    precios = sorted(
      repo_precio.leer_todos(),
      key=lambda precio: (
        precio.libro.id or 0,
        precio.moneda.codigo,
      ),
    )
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
      escritor = csv.writer(archivo)
      escritor.writerow([
        "libro_id",
        "isbn",
        "titulo",
        "autor",
        "codigo_moneda",
        "nombre_moneda",
        "monto",
      ])
      for precio in precios:
        escritor.writerow([
          precio.libro.id,
          precio.libro.isbn,
          precio.libro.titulo,
          precio.libro.autor,
          precio.moneda.codigo,
          precio.moneda.nombre,
          f"{precio.monto:.2f}",
        ])
  except (OSError, SQLAlchemyError) as error:
    print(f"No se pudo exportar el archivo CSV: {error}")
    return

  print(f"Se exportaron {len(precios)} precios a: {ruta.resolve()}")


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
