from urllib.parse import urlencode

import scrapy
from w3lib.url import safe_url_string

from book_manager.repositories.repositories import (
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioLibro,
)
from book_manager.scraper.loaders import CuspideLoader


class CuspideSpider(scrapy.Spider):
  name = "cuspide"
  allowed_domains = ["cuspide.com"]
  base_url = "https://cuspide.com/"
  max_resultados_por_libro = 10

  def start_requests(self):
    repo_libros = RepositorioLibro(
      RepositorioEditorial(), RepositorioGenero()
    )
    libros = repo_libros.leer_todos()
    if not libros:
      self.logger.warning("El catálogo no contiene libros para buscar.")
      return

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