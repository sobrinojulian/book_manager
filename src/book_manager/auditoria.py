"""Decoradores y utilidades para registrar operaciones del sistema."""
from __future__ import annotations

import json
import logging
from functools import wraps
from inspect import signature
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
_LOGGER = logging.getLogger(__name__)


def _resumir(valor: Any) -> Any:
  if valor is None or isinstance(valor, (bool, int, float, str)):
    return valor if not isinstance(valor, str) or len(valor) <= 500 else valor[:500]
  if isinstance(valor, (list, tuple)):
    return {
      "cantidad": len(valor),
      "elementos": [_resumir(elemento) for elemento in valor[:10]],
    }
  return repr(valor)[:500]


def auditar_operacion(metodo: F) -> F:
  """Registra parámetros, resultado o error de una operación de repositorio."""
  @wraps(metodo)
  def envoltura(self: Any, *args: Any, **kwargs: Any) -> Any:
    parametros = signature(metodo).bind(self, *args, **kwargs)
    parametros.apply_defaults()
    detalles: dict[str, Any] = {
      "parametros": {
        nombre: _resumir(valor)
        for nombre, valor in parametros.arguments.items()
        if nombre != "self"
      }
    }
    accion = f"{type(self).__name__}.{metodo.__name__}"

    try:
      resultado = metodo(self, *args, **kwargs)
    except Exception as error:
      detalles["estado"] = "error"
      detalles["error"] = f"{type(error).__name__}: {error}"
      try:
        self._registrar_auditoria(accion, detalles)
      except Exception:
        _LOGGER.exception("No se pudo registrar la auditoría de %s", accion)
      raise

    detalles["estado"] = "correcto"
    detalles["resultado"] = _resumir(resultado)
    self._registrar_auditoria(accion, detalles)
    return resultado

  return envoltura  # type: ignore[return-value]


def detalles_a_json(detalles: dict[str, Any]) -> str:
  """Serializa detalles de auditoría de forma legible y tolerante."""
  return json.dumps(detalles, ensure_ascii=False, default=str)