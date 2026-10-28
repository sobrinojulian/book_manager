import re

from itemloaders import ItemLoader
from itemloaders.processors import Identity, MapCompose, TakeFirst

from book_manager.scraper.items import CuspideItem


def _limpiar_texto(valor: str) -> str:
  return re.sub(r"\s+", " ", valor).strip()


def _valores_unicos(valores: list[str]) -> list[str]:
  return list(dict.fromkeys(valor for valor in valores if valor))


class CuspideLoader(ItemLoader):
  default_item_class = CuspideItem
  default_input_processor = MapCompose(_limpiar_texto)
  default_output_processor = TakeFirst()
  libro_id_in = Identity()
  formas_pago_in = MapCompose(_limpiar_texto)
  formas_pago_out = _valores_unicos