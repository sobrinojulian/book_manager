"""Arranque de la aplicación y conexión de sus componentes."""
from __future__ import annotations

from book_manager.preload_data.preload_data import (
  cargar_datos_iniciales,
)
from book_manager.repositories.repositories import (
  RepositorioAuditoria,
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
from book_manager.ui.console import (
  menu_cotizaciones,
  menu_editoriales,
  menu_ejecutar_scraper_cuspide,
  menu_generos,
  menu_generar_reporte,
  menu_historial_auditoria,
  menu_libros,
  menu_monedas,
  menu_obtener_cotizaciones,
  menu_exportar_precios_csv,
  menu_precios,
  menu_precios_bimonetarios,
  menu_stock,
  menu_tipos_cotizacion,
)

OPCIONES_MENU: str = """
===== Book Manager =====
1) Géneros
2) Editoriales
3) Monedas
4) Tipos de Cotización
5) Libros
6) Precios
7) Stock
8) Obtener las cotizaciones por API
9) Ver precios bimonetarios
10) Exportar precios a CSV
11) Ejecutar scraping
12) Generar reporte
13) Ver historial de auditoría
0) Salir
========================="""


def main(import_default_data: bool = True) -> None:
  """Prepara repositorios y servicios, carga datos y atiende el menú."""
  repo_genero = RepositorioGenero()
  repo_editorial = RepositorioEditorial()
  repo_moneda = RepositorioMoneda()
  repo_tipo = RepositorioTipoCotizacion()
  repo_libro = RepositorioLibro(repo_editorial, repo_genero)
  repo_precio = RepositorioPrecio(repo_libro, repo_moneda)
  repo_stock = RepositorioStock(repo_libro)
  repo_cotizacion = RepositorioCotizacionDolar(repo_tipo)
  repo_auditoria = RepositorioAuditoria(repo_genero._conexion)

  servicio_cotizacion = ServicioCotizacion(
    repo_cotizacion, repo_tipo
  )
  servicio_precio = ServicioPrecio(
    repo_precio, repo_moneda, servicio_cotizacion
  )
  servicio_stock = ServicioStock(repo_stock)
  servicio_libro = ServicioLibro(
    repo_libro, repo_precio, repo_stock
  )

  if import_default_data and not repo_libro.leer_todos():
    cargar_datos_iniciales(
      repo_genero,
      repo_editorial,
      repo_moneda,
      repo_tipo,
      servicio_libro,
      servicio_cotizacion,
    )

  while True:
    print(OPCIONES_MENU)
    opcion: str = input("Elija una opción del menú: ").strip()

    if opcion == "1":
      menu_generos(repo_genero)
    elif opcion == "2":
      menu_editoriales(repo_editorial)
    elif opcion == "3":
      menu_monedas(repo_moneda)
    elif opcion == "4":
      menu_tipos_cotizacion(repo_tipo)
    elif opcion == "5":
      menu_libros(
        servicio_libro, repo_libro, repo_editorial,
        repo_genero, repo_moneda,
      )
    elif opcion == "6":
      menu_precios(
        servicio_precio, servicio_cotizacion, repo_precio,
        repo_libro, repo_tipo,
      )
    elif opcion == "7":
      menu_stock(servicio_stock, repo_stock)
    elif opcion == "8":
      menu_obtener_cotizaciones(servicio_cotizacion)
    elif opcion == "9":
      menu_precios_bimonetarios(
        repo_precio, repo_libro, repo_moneda
      )
    elif opcion == "10":
      menu_exportar_precios_csv(repo_precio)
    elif opcion == "11":
      menu_ejecutar_scraper_cuspide()
    elif opcion == "12":
      menu_generar_reporte()
    elif opcion == "13":
      menu_historial_auditoria(repo_auditoria)
    elif opcion == "0":
      print("La sesión ha finalizado. ¡Hasta la próxima!")
      break
    else:
      print("Esa opción no está disponible. Pruebe con otra.")


if __name__ == "__main__":
  main()
