import csv
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from typing import Any

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
    self._umbral = spider.diferencia_minima_ars
    spider.logger.info("Los resultados se guardan en %s", self._archivo.name)
    spider.logger.info(
      "Las alertas CSV se guardan en %s", self._archivo_alertas.name
    )

  def process_item(self, item: Any, spider: Spider) -> Any:
    self._archivo.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
    precio_interno = _parse_precio(item.get("precio_interno_ars"))
    precio_web = _parse_precio(item.get("precio"))
    if precio_interno is not None and precio_web is not None:
      diferencia = precio_web - precio_interno
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