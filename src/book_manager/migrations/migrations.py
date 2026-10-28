"""Migración de los CSV del TP1 a la base de datos SQLAlchemy."""
from __future__ import annotations

import csv
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import Date, Integer, Numeric, insert, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import UniqueConstraint

from book_manager.database.connection import ConexionDB
from book_manager.models.models import (
  Base,
  CotizacionDolar,
  Editorial,
  Genero,
  Libro,
  Moneda,
  Precio,
  Stock,
  TipoCotizacion,
)

_MIGRACIONES = (
  ("generos.csv", Genero),
  ("editoriales.csv", Editorial),
  ("monedas.csv", Moneda),
  ("tipos_cotizacion.csv", TipoCotizacion),
  ("libros.csv", Libro),
  ("precios.csv", Precio),
  ("stocks.csv", Stock),
  ("cotizaciones.csv", CotizacionDolar),
)


def _claves_unicas(modelo: type[Base]) -> list[tuple[str, ...]]:
  """Obtiene las claves únicas naturales, excluyendo la clave primaria."""
  claves: list[tuple[str, ...]] = []
  for restriccion in modelo.__table__.constraints:
    if isinstance(restriccion, UniqueConstraint):
      columnas = tuple(columna.name for columna in restriccion.columns)
      if columnas and columnas != ("id",):
        claves.append(columnas)
  return claves


def _convertir_fila(
  fila: dict[str, str], modelo: type[Base]
) -> dict[str, Any]:
  """Convierte valores CSV según los tipos definidos en el modelo ORM."""
  columnas = {columna.name: columna for columna in modelo.__table__.columns}
  encabezados = set(fila)
  esperados = set(columnas)
  if encabezados != esperados:
    raise ValueError(
      f"Columnas inválidas para {modelo.__tablename__}: "
      f"faltan {sorted(esperados - encabezados)}; "
      f"sobran {sorted(encabezados - esperados)}."
    )

  valores: dict[str, Any] = {}
  for nombre, valor in fila.items():
    tipo = columnas[nombre].type
    if isinstance(tipo, Integer):
      valores[nombre] = int(valor)
    elif isinstance(tipo, Numeric):
      valores[nombre] = Decimal(valor)
    elif isinstance(tipo, Date):
      valores[nombre] = date.fromisoformat(valor)
    else:
      valores[nombre] = valor
  return valores


def _normalizar_filas(
  ruta_csv: Path, modelo: type[Base], id_por_tabla: dict[str, dict[int, int]]
) -> tuple[list[dict[str, Any]], list[str]]:
  """Deduplica claves naturales y remapea claves foráneas a sus IDs canónicos."""
  tabla = modelo.__table__
  claves_unicas = _claves_unicas(modelo)
  canonicos: dict[tuple[str, tuple[Any, ...]], dict[str, Any]] = {}
  id_canonico: dict[int, int] = {}
  filas: list[dict[str, Any]] = []
  notas: list[str] = []

  with ruta_csv.open("r", newline="", encoding="utf-8-sig") as archivo:
    lector = csv.DictReader(archivo)
    if lector.fieldnames is None:
      raise ValueError(f"El archivo CSV está vacío: {ruta_csv}")

    for numero_fila, fila_csv in enumerate(lector, start=2):
      fila = _convertir_fila(fila_csv, modelo)
      for columna in tabla.columns:
        if not columna.foreign_keys:
          continue
        referencia = next(iter(columna.foreign_keys)).target_fullname
        tabla_referenciada = referencia.split(".", maxsplit=1)[0]
        ids_referenciados = id_por_tabla.get(tabla_referenciada, {})
        fila[columna.name] = ids_referenciados.get(
          fila[columna.name], fila[columna.name]
        )

      clave_duplicada: tuple[str, tuple[Any, ...]] | None = None
      for columnas in claves_unicas:
        clave = (columnas, tuple(fila[nombre] for nombre in columnas))
        if clave in canonicos:
          clave_duplicada = clave
          break

      if clave_duplicada is None:
        filas.append(fila)
        for columnas in claves_unicas:
          clave = (columnas, tuple(fila[nombre] for nombre in columnas))
          canonicos[clave] = fila
        continue

      fila_canonica = canonicos[clave_duplicada]
      id_origen = fila["id"]
      id_destino = fila_canonica["id"]
      id_canonico[id_origen] = id_destino
      columnas_clave, valores_clave = clave_duplicada
      descripcion_clave = ", ".join(
        f"{nombre}={valor!r}"
        for nombre, valor in zip(columnas_clave, valores_clave)
      )

      if modelo is Stock:
        fila_canonica["cantidad"] += fila["cantidad"]
        notas.append(
          f"-- Fila {numero_fila}: stock duplicado; se sumó "
          f"{fila['cantidad']} a libro_id={fila_canonica['libro_id']} "
          f"(id={id_destino})."
        )
      else:
        notas.append(
          f"-- Fila {numero_fila}: registro duplicado por "
          f"{descripcion_clave}; se conservó id={id_destino} "
          f"en lugar de id={id_origen}."
        )

  id_por_tabla[tabla.name] = id_canonico
  return filas, notas


def _crear_sentencias(
  modelo: type[Base], filas: list[dict[str, Any]]
) -> list[str]:
  """Compila sentencias INSERT con literales válidos para PostgreSQL."""
  sentencias = []
  for fila in filas:
    sentencia = insert(modelo.__table__).values(**fila).compile(
      dialect=postgresql.dialect(),
      compile_kwargs={"literal_binds": True},
    )
    sentencias.append(str(sentencia))
  return sentencias


def cargar_datos_sql(carpeta_sqls: str) -> dict[str, int]:
  """Carga los INSERT de los archivos SQL en el orden de sus dependencias.

  Cada sentencia debe ocupar una línea; las líneas vacías y los comentarios
  SQL se ignoran. Toda la carga se ejecuta en una única transacción.
  """
  origen = Path(carpeta_sqls)
  archivos: list[tuple[str, Path]] = []
  for nombre_csv, modelo in _MIGRACIONES:
    ruta_sql = origen / Path(nombre_csv).with_suffix(".sql")
    if not ruta_sql.is_file():
      raise FileNotFoundError(f"No se encontró el archivo SQL: {ruta_sql}")
    archivos.append((modelo.__tablename__, ruta_sql))

  resumen = {tabla: 0 for tabla, _ in archivos}
  conexion = ConexionDB()
  try:
    Base.metadata.create_all(conexion.engine)
    with conexion.engine.begin() as transaccion:
      for tabla, ruta_sql in archivos:
        for linea in ruta_sql.read_text(encoding="utf-8").splitlines():
          sentencia = linea.strip()
          if not sentencia or sentencia.startswith("--"):
            continue
          transaccion.execute(text(sentencia.removesuffix(";")))
          resumen[tabla] += 1

      if conexion.engine.dialect.name == "postgresql":
        for _, modelo in _MIGRACIONES:
          tabla = modelo.__tablename__
          transaccion.exec_driver_sql(
            "SELECT setval("
            f"pg_get_serial_sequence('{tabla}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {tabla}), 1), "
            f"EXISTS(SELECT 1 FROM {tabla}))"
          )
  finally:
    conexion.cerrar()

  logging.info("Carga SQL completada: %s", resumen)
  return resumen


def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> dict[str, int]:
  """Genera archivos SQL e importa los CSV en la base configurada.

  Deduplica por las restricciones únicas del esquema. Las referencias a filas
  duplicadas se cambian al ID canónico y los stocks equivalentes se suman.

  Args:
      carpeta_csvs: Carpeta con los CSV de origen.
      carpeta_sqls: Carpeta donde se escriben los archivos SQL generados.

  Returns:
      Cantidad de filas insertadas por tabla.
  """
  origen = Path(carpeta_csvs)
  destino = Path(carpeta_sqls)
  destino.mkdir(parents=True, exist_ok=True)

  id_por_tabla: dict[str, dict[int, int]] = {}
  cargas: list[tuple[type[Base], list[dict[str, Any]], list[str]]] = []
  for nombre_csv, modelo in _MIGRACIONES:
    ruta_csv = origen / nombre_csv
    if not ruta_csv.is_file():
      raise FileNotFoundError(f"No se encontró el archivo de origen: {ruta_csv}")
    filas, notas = _normalizar_filas(ruta_csv, modelo, id_por_tabla)
    cargas.append((modelo, filas, notas))

  for (nombre_csv, _), (modelo, filas, notas) in zip(_MIGRACIONES, cargas):
    nombre_salida = Path(nombre_csv).with_suffix(".sql")
    sentencias = _crear_sentencias(modelo, filas)
    contenido = [*notas, *[f"{sentencia};" for sentencia in sentencias]]
    (destino / nombre_salida).write_text(
      "\n".join(contenido) + ("\n" if contenido else ""),
      encoding="utf-8",
    )

  return cargar_datos_sql(str(destino))


if __name__ == "__main__":
  carpeta_migraciones = Path(__file__).resolve().parent
  migrar_datos(
    str(carpeta_migraciones / "csv"),
    str(carpeta_migraciones / "sql"),
  )