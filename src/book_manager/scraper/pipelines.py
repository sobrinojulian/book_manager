import csv
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font
from scrapy import Spider


def _parse_precio(valor: Any) -> Decimal | None:
  if valor is None:
    return None

  normalizado = re.sub(r"[^\d,.-]", "", str(valor))
  if not normalizado:
    return None

  separador_decimal = None
  if "," in normalizado and "." in normalizado:
    separador_decimal = (
      "," if normalizado.rfind(",") > normalizado.rfind(".") else "."
    )
    separador_miles = "." if separador_decimal == "," else ","
    normalizado = normalizado.replace(separador_miles, "")
    normalizado = normalizado.replace(separador_decimal, ".")
  elif "," in normalizado or "." in normalizado:
    separador = "," if "," in normalizado else "."
    parte_entera, parte_decimal = normalizado.rsplit(separador, 1)
    if len(parte_decimal) in (1, 2):
      normalizado = f"{parte_entera.replace(separador, '')}.{parte_decimal}"
    else:
      normalizado = normalizado.replace(separador, "")

  try:
    precio = Decimal(normalizado)
  except InvalidOperation:
    return None
  return precio if precio.is_finite() and precio >= 0 else None


class CuspideJsonPipeline:
  """Guarda resultados JSONL y alertas de diferencias en archivos CSV."""

  def open_spider(self, spider: Spider) -> None:
    directorio = Path(
      spider.settings.get(
        "CUSPIDE_OUTPUT_DIR",
        Path(__file__).resolve().parents[1] / "reportes",
      )
    )
    directorio.mkdir(parents=True, exist_ok=True)
    nombre = datetime.now().astimezone().strftime(
      "cuspide_%Y%m%d_%H%M%S_%f.jsonl"
    )
    self._archivo = (directorio / nombre).open("w", encoding="utf-8")
    nombre_alertas = nombre.replace("cuspide_", "alertas_cuspide_").replace(
      ".jsonl", ".csv"
    )
    self._archivo_alertas = (directorio / nombre_alertas).open(
      "w", newline="", encoding="utf-8-sig"
    )
    self._escritor_alertas = csv.writer(self._archivo_alertas)
    self._escritor_alertas.writerow([
      "libro_id",
      "isbn",
      "titulo_catalogo",
      "titulo_cuspide",
      "precio_interno_ars",
      "precio_web_ars",
      "diferencia_ars",
      "url_producto",
    ])
    self._filas_reporte = []
    self._fecha_extraccion = datetime.now().astimezone().replace(tzinfo=None)
    self._umbral = getattr(spider, "diferencia_minima_ars")
    spider.logger.info("Los resultados se guardan en %s", self._archivo.name)
    spider.logger.info(
      "Las alertas CSV se guardan en %s", self._archivo_alertas.name
    )

  def process_item(self, item: Any, spider: Spider) -> Any:
    self._archivo.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
    precio_interno = _parse_precio(item.get("precio_interno_ars"))
    precio_web = _parse_precio(item.get("precio"))
    diferencia = (
      precio_web - precio_interno
      if precio_interno is not None and precio_web is not None
      else None
    )
    self._filas_reporte.append((
      item.get("titulo_catalogo") or item.get("titulo_cuspide", ""),
      float(precio_interno) if precio_interno is not None else None,
      float(precio_web) if precio_web is not None else None,
      float(diferencia) if diferencia is not None else None,
      self._fecha_extraccion,
    ))
    if precio_interno is not None and precio_web is not None:
      assert diferencia is not None
      if abs(diferencia) > self._umbral:
        self._escritor_alertas.writerow([
          item.get("libro_id", ""),
          item.get("isbn_catalogo", ""),
          item.get("titulo_catalogo", ""),
          item.get("titulo_cuspide", ""),
          f"{precio_interno:.2f}",
          f"{precio_web:.2f}",
          f"{diferencia:.2f}",
          item.get("url_producto", ""),
        ])
    return item

  def close_spider(self, spider: Spider) -> None:
    self._archivo.close()
    self._archivo_alertas.close()
    libro = Workbook()
    hoja: Any = libro.active
    hoja.title = "Comparación de precios"
    hoja.append([
      "Libro",
      "Precio interno",
      "Precio web",
      "Diferencia",
      "Fecha de extracción",
    ])
    for fila in self._filas_reporte:
      hoja.append(fila)

    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions
    for celda in hoja[1]:
      celda.font = Font(bold=True)
    for fila in hoja.iter_rows(min_row=2, min_col=2, max_col=4):
      for celda in fila:
        celda.number_format = '"$"#,##0.00;[Red]-"$"#,##0.00'
    for celda in hoja["E"][1:]:
      celda.number_format = "yyyy-mm-dd hh:mm:ss"
    for columna, ancho in {
      "A": 45,
      "B": 18,
      "C": 18,
      "D": 18,
      "E": 22,
    }.items():
      hoja.column_dimensions[columna].width = ancho

    ruta_excel = Path(self._archivo.name).with_name(
      Path(self._archivo.name).name.replace(
        "cuspide_", "reporte_precios_cuspide_"
      ).replace(".jsonl", ".xlsx")
    )
    libro.save(ruta_excel)
    spider.logger.info("El reporte Excel se guarda en %s", ruta_excel)