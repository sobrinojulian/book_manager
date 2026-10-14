"""Administración de conexiones y sesiones de base de datos."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class ConexionDB:
  """Crea el motor SQLAlchemy y administra el ciclo de vida de sus sesiones."""

  def __init__(self, url: str | URL | None = None) -> None:
    database_url = (
      url or os.getenv("DATABASE_URL") or "sqlite:///book_manager.db"
    )
    self.engine: Engine = create_engine(database_url)
    self._session_factory = sessionmaker(
      bind=self.engine, expire_on_commit=False
    )

  @contextmanager
  def sesion(self) -> Iterator[Session]:
    """Proporciona una sesión y confirma o revierte su transacción."""
    with self._session_factory.begin() as session:
      yield session

  def cerrar(self) -> None:
    """Libera las conexiones mantenidas por el motor."""
    self.engine.dispose()
