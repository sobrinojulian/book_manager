import scrapy


class CuspideItem(scrapy.Item):
  libro_id = scrapy.Field()
  isbn_catalogo = scrapy.Field()
  titulo_catalogo = scrapy.Field()
  titulo_cuspide = scrapy.Field()
  url_producto = scrapy.Field()
  precio = scrapy.Field()
  url_imagen = scrapy.Field()
  formas_pago = scrapy.Field()
  descripcion = scrapy.Field()