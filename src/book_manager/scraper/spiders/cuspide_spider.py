from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

import scrapy
from w3lib.url import safe_url_string

from book_manager.repositories.repositories import (
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioLibro,
  RepositorioMoneda,
  RepositorioPrecio,
)
from book_manager.scraper.loaders import CuspideLoader


class CuspideSpider(scrapy.Spider):
  name = "cuspide"
  allowed_domains = ["cuspide.com"]
  base_url = "https://cuspide.com/"
  max_resultados_por_libro = 10

  def __init__(
    self,
    diferencia_minima_ars: str = "0",
    *args,
    **kwargs,
  ):
    try:
      self.diferencia_minima_ars = Decimal(diferencia_minima_ars)
    except InvalidOperation as error:
      raise ValueError("La diferencia mínima debe ser un número válido.") from error
    if not self.diferencia_minima_ars.is_finite() or self.diferencia_minima_ars < 0:
      raise ValueError("La diferencia mínima debe ser mayor o igual a cero.")
    super().__init__(*args, **kwargs)

  def start_requests(self):
    repo_libros = RepositorioLibro(
      RepositorioEditorial(), RepositorioGenero()
    )
    libros = repo_libros.leer_todos()
    if not libros:
      self.logger.warning("El catálogo no contiene libros para buscar.")
      return

    repo_precio = RepositorioPrecio(repo_libros, RepositorioMoneda())
    precios_ars = {
      precio.libro.id: precio.monto
      for precio in repo_precio.leer_todos()
      if precio.moneda.codigo == "ARS"
    }

    for libro in libros:
      url = safe_url_string(
        f"{self.base_url}?{urlencode({'s': libro.titulo, 'post_type': 'product'})}"
      )
      yield scrapy.Request(
        url,
        callback=self.parse_busqueda,
        cb_kwargs={
          "libro": {
            "id": libro.id,
            "isbn": libro.isbn,
            "titulo": libro.titulo,
            "precio_interno_ars": (
              f"{precios_ars[libro.id]:.2f}"
              if libro.id in precios_ars
              else None
            ),
          }
        },
      )

  def parse_busqueda(self, response, libro):
    tarjetas = response.css("ul.products li.product, .products .product")
    enlaces = []
    for tarjeta in tarjetas:
      enlace = tarjeta.css("a[href*='/producto/']::attr(href)").get()
      if enlace and enlace not in enlaces:
        enlaces.append(enlace)

    if not enlaces:
      enlaces = response.css("a[href*='/producto/']::attr(href)").getall()

    enlaces_unicos = list(dict.fromkeys(enlaces))
    for enlace in enlaces_unicos[:self.max_resultados_por_libro]:
      yield response.follow(
        enlace,
        callback=self.parse_producto,
        cb_kwargs={"libro": libro},
      )

  def parse_producto(self, response, libro):
    loader = CuspideLoader()
    loader.add_value("libro_id", libro["id"])
    loader.add_value("isbn_catalogo", libro["isbn"])
    loader.add_value("titulo_catalogo", libro["titulo"])
    loader.add_value("precio_interno_ars", libro["precio_interno_ars"])
    loader.add_value(
      "titulo_cuspide",
      response.css("h1.product_title::text, h1.entry-title::text").get(),
    )
    loader.add_value("url_producto", response.url)

    precios = response.css(
      ".summary .price .amount::text, .summary p.price::text, .product .price .amount::text"
    ).getall()
    loader.add_value("precio", precios)

    imagen = (
      response.css(
        ".woocommerce-product-gallery__image img::attr(data-large_image)"
      ).get()
      or response.css(
        ".woocommerce-product-gallery__image img::attr(data-src)"
      ).get()
      or response.css(
        ".woocommerce-product-gallery__image img::attr(src)"
      ).get()
      or response.css(
        ".woocommerce-product-gallery__image a::attr(href)"
      ).get()
    )
    loader.add_value("url_imagen", response.urljoin(imagen) if imagen else None)

    formas_pago = response.css(
      "[class*='payment'], [id*='payment'], [class*='pago'], [id*='pago'], "
      "[class*='cuota'], [id*='cuota'], a[href*='medios-de-pago']"
    ).xpath("string(.)").getall()
    loader.add_value("formas_pago", formas_pago)

    descripcion = ""
    for selector in (
      "#tab-description",
      ".woocommerce-Tabs-panel--description",
      ".woocommerce-Tabs-panel--sinopsis",
      ".woocommerce-product-details__short-description",
    ):
      nodo = response.css(selector)
      texto = " ".join(nodo.xpath(".//text()[normalize-space()]").getall())
      if texto.strip():
        descripcion = texto
        break
    loader.add_value("descripcion", descripcion)
    yield loader.load_item()