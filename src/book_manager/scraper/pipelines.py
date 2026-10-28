import json
from datetime import datetime
from pathlib import Path
from typing import Any

from scrapy import Spider


class CuspideJsonPipeline:
  """Guarda cada resultado extraído en un archivo JSON Lines."""

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
    spider.logger.info("Los resultados se guardan en %s", self._archivo.name)

  def process_item(self, item: Any, spider: Spider) -> Any:
    self._archivo.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
    return item

  def close_spider(self, spider: Spider) -> None:
    self._archivo.close()