# Book Manager
> Licenciatura en Ciencia de Datos — Universidad del Gran Rosario
> (V.CLCD.EL1) SEMINARIO DE ACTUALIZACIÓN I
> Trabajo Práctico 1

## Grupo 54
- Carla Carrizo
- Julian Sobrino

## Introducción y Contexto del problema

Una librería con venta al público necesita modernizar su sistema de gestión de inventario de libros. Debido a la fluctuación en los costos de importación de material bibliográfico, el sistema debe gestionar precios en diferentes monedas y seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.

El objetivo es desarrollar una aplicación de consola (CLI) robusta en Python que permita gestionar el inventario de una librería, cotizar los libros en tiempo real según el valor del dólar y comparar precios automáticamente con la competencia web.

Descripción de las Entidades

Para cumplir con el requerimiento, se han identificado las siguientes entidades:

- Libro: representa cada título del catálogo de la librería (isbn, título, autor, editorial, género, etc.).
- Genero: categoría literaria a la que pertenece un libro (novela, ensayo, infantil, técnico, etc.).
- Editorial: proveedor/distribuidora que provee los libros a la librería.
- Moneda: las distintas monedas en las que se puede expresar un precio (ARS, USD, etc.).
- TipoCotizacion: los distintos tipos de cotización del dólar (Oficial, Blue, MEP, etc.).
- Precio: valor monetario asociado a un libro en una moneda determinada.
- Stock: cantidad disponible de cada libro.
- Cotizacion: registro histórico de las cotizaciones por tipo y fecha.

## ✅ Ejercicio 01

> Puntos: 1

Inicialización y configuración de la herramienta de versionado. Vamos a trabajar sobre la rama llamada "Sprint_1".

*La estructura de directorios* es:

```
book_manager/
├── src/
│   └── book_manager/
│       ├── entities/
│       │   └── entities.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── services/
│       │   └── services.py
│       ├── migrations
│       │   └── csv
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

## ✅ Ejercicio 02

> Puntos: 2

Definir la/s clase/s entidad necesarias para el uso del sistema (Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock, CotizacionDolar). Se debe representar todo con objetos y se deben aplicar las facilidades que nos permiten una mejor programación. Se debe aplicar la encapsulación.

Archivo/s de trabajo:
- book_manager/entities/entities.py

## ✅ Ejercicio 03

> Puntos: 2

Definir la/s clase/s responsables de la persistencia de datos.

Todas las clases deben tener su propio CRUD (Create/Read/Update/Delete o Alta/Lectura/Modificación/Borrado).

Archivo/s de trabajo:
- book_manager/repositories/repositories.py

Tomar como base el siguiente código.

```python
import abc
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T', bound=EntidadBase)


class IRepositorio(abc.ABC, Generic[T]):
  """Interfaz para repositorios que manejan entidades con operaciones CRUD básicas."""

  @abc.abstractmethod
  def crear(self, entidad: T) -> T:
    """Crea una nueva entidad en el repositorio.

    Args:
        entidad (T): La entidad a crear.

    Returns:
        T: La entidad creada.

    Raises:
        ValueError: Si ya existe una entidad con el mismo ID.
    """
    pass

  @abc.abstractmethod
  def leer_por_id(self, id: int) -> Optional[T]:
    """Lee una entidad del repositorio por su ID.

    Args:
        id (int): El ID de la entidad a leer.

    Returns:
        Optional[T]: La entidad si se encuentra, None en caso contrario.
    """
    pass

  @abc.abstractmethod
  def leer_todos(self) -> List[T]:
    """Lee todas las entidades del repositorio.

    Returns:
        List[T]: Una lista de todas las entidades.
    """
    pass

  @abc.abstractmethod
  def actualizar(self, entidad: T) -> T:
    """Actualiza una entidad existente en el repositorio.

    Args:
        entidad (T): La entidad a actualizar (debe tener un ID existente).

    Returns:
        T: La entidad actualizada.

    Raises:
        ValueError: Si no se encuentra la entidad para actualizar.
    """
    pass

  @abc.abstractmethod
  def eliminar(self, id: int) -> bool:
    """Elimina una entidad del repositorio por su ID.

    Args:
        id (int): El ID de la entidad a eliminar.

    Returns:
        bool: True si la entidad fue eliminada, False si no se encontró.
    """
    pass


class IRepositorioStock(abc.ABC):
  """Interfaz para repositorios del tipo Stock."""

  @abc.abstractmethod
  def crear(self, stock: Stock) -> Stock:
    """Crea un nuevo registro de stock.

    Args:
        stock (Stock): El objeto Stock a crear.

    Returns:
        Stock: El objeto Stock creado.

    Raises:
        ValueError: Si ya existe un registro de stock para el mismo libro.
    """
    pass

  @abc.abstractmethod
  def leer_por_libro(self, libro_id: int) -> Optional['Stock']:
    """Lee un registro de stock por ID de libro.

    Args:
        libro_id (int): El ID del libro asociado al stock.

    Returns:
        Optional[Stock]: El objeto Stock si se encuentra, None en caso contrario.
    """
    pass

  @abc.abstractmethod
  def actualizar(self, stock: 'Stock') -> 'Stock':
    """Actualiza un registro de stock existente.

    Args:
        stock (Stock): El objeto Stock a actualizar (debe tener un libro_id existente).

    Returns:
        Stock: El objeto Stock actualizado.

    Raises:
        ValueError: Si no se encuentra el stock para actualizar.
    """
    pass

  @abc.abstractmethod
  def eliminar(self, libro_id: int) -> bool:
    """Elimina un registro de stock por ID de libro.

    Args:
        libro_id (int): El ID del libro asociado al stock a eliminar.

    Returns:
        bool: True si el stock fue eliminado, False si no se encontró.
    """
    pass


class IRepositorioCotizacionDolar(abc.ABC):
  """Interfaz para repositorios del tipo RepositorioCotizacionDolar."""

  @abc.abstractmethod
  def crear(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
    """Crea una nueva cotización de dólar.

    Args:
        cotizacion (CotizacionDolar): El objeto CotizacionDolar a crear.

    Returns:
        CotizacionDolar: El objeto CotizacionDolar creado.

    Raises:
        ValueError: Si ya existe una cotización para el mismo tipo y fecha.
    """
    pass

  @abc.abstractmethod
  def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date) -> Optional['CotizacionDolar']:
    """Lee una cotización de dólar por tipo y fecha.

    Args:
        tipo_id (int): El ID del tipo de cotización (e.g., 'Oficial', 'Blue').
        fecha (datetime.date): La fecha de la cotización.

    Returns:
        Optional[CotizacionDolar]: La cotización si se encuentra, None en caso contrario.
    """
    pass

  @abc.abstractmethod
  def leer_historico_por_tipo(self, tipo_id: int) -> List['CotizacionDolar']:
    """Lee el histórico de cotizaciones para un tipo específico.

    Args:
        tipo_id (int): El ID del tipo de cotización.

    Returns:
        List[CotizacionDolar]: Una lista de cotizaciones históricas para el tipo dado.
    """
    pass

  @abc.abstractmethod
  def actualizar(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
    """Actualiza una cotización de dólar existente.

    Args:
        cotizacion (CotizacionDolar): El objeto CotizacionDolar a actualizar.

    Returns:
        CotizacionDolar: El objeto CotizacionDolar actualizado.
    """
    pass

  @abc.abstractmethod
  def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
    """Elimina una cotización de dólar por tipo y fecha.

    Args:
        tipo_id (int): El ID del tipo de cotización.
        fecha (datetime.date): La fecha de la cotización a eliminar.

    Returns:
        bool: True si la cotización fue eliminada, False si no se encontró.
    """
    pass
```

## ✅ Ejercicio 04

> Puntos: 2

Definir la/s clase/s responsables de la lógica que se debe aplicar a cada operación/método de las clases.

Archivo/s de trabajo:
- book_manager/services/services.py


## ✅ Punto 05

> Puntos: 1

Crear archivos para la importación de datos, escribirlos dentro de la carpeta `migrations/csv`.

Cada clase debe tener un mínimo de 10 registros.

Archivo/s de trabajo:
- book_manager/preload_data/preload_data.py


## ✅ Punto 06

> Puntos: 1

Armar las interfaces gráficas del sistema, estas deben operar con los CRUD de cada clase.

Archivo/s de trabajo:
- book_manager/ui/console.py

## ✅ Punto 07

> Puntos: 1

Crear el archivo main.py que se encarga de ejecutar el sistema.

Archivo/s de trabajo:
- book_manager/main.py
