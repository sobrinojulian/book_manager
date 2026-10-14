"""Administración de conexiones y sesiones de base de datos."""
from __future__ import annotations

import os
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker


class ConexionDB:
  """Conecta con Supabase y administra sus transacciones SQLAlchemy."""

  def __init__(self, url: str | URL | None = None) -> None:
    ruta_env = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(dotenv_path=ruta_env)

    database_url = url or os.getenv("SUPABASE_DATABASE_URL") or os.getenv(
      "DATABASE_URL"
    )
    if database_url is None:
      raise RuntimeError(
        "Configure SUPABASE_DATABASE_URL o DATABASE_URL con la URL "
        "de conexión PostgreSQL de Supabase."
      )

    parsed_url = database_url if isinstance(database_url, URL) else make_url(
      database_url
    )
    parsed_url = parsed_url.difference_update_query(["pgbouncer"])
    if parsed_url.drivername in ("postgres", "postgresql"):
      parsed_url = parsed_url.set(drivername="postgresql+psycopg")

    self.engine: Engine = create_engine(parsed_url)
    self._session_factory = sessionmaker(
      bind=self.engine, expire_on_commit=False
    )

  @contextmanager
  def transaccion(self) -> Iterator[Session]:
    """Confirma al salir normalmente y revierte si ocurre una excepción."""
    with self._session_factory.begin() as session:
      yield session

  def sesion(self) -> AbstractContextManager[Session]:
    """Alias de compatibilidad para el context manager transaccional."""
    return self.transaccion()

  def cerrar(self) -> None:
    """Libera las conexiones mantenidas por el motor."""
    self.engine.dispose()
