# Book Manager
> Licenciatura en Ciencia de Datos — Universidad del Gran Rosario
> (V.CLCD.EL1) SEMINARIO DE ACTUALIZACIÓN I
> Trabajo Práctico 1

## Grupo 54
- Carla Carrizo
- Julian Sobrino

## Instrucciones
```powershell
git clone https://github.com/sobrinojulian/book_manager
cd .\book_manager\
$env:PYTHONPATH = "src"
python -m book_manager.main
```
## Sprint 1

### Introducción y Contexto del problema

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


### Ejercicio 01

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

### Ejercicio 02

> Puntos: 2

Definir la/s clase/s entidad necesarias para el uso del sistema (Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock, CotizacionDolar). Se debe representar todo con objetos y se deben aplicar las facilidades que nos permiten una mejor programación. Se debe aplicar la encapsulación.

Archivo/s de trabajo:
- book_manager/entities/entities.py

### Ejercicio 03

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

### Ejercicio 04

> Puntos: 2

Definir la/s clase/s responsables de la lógica que se debe aplicar a cada operación/método de las clases.

Archivo/s de trabajo:
- book_manager/services/services.py


### Ejercicio 05

> Puntos: 1

Crear archivos para la importación de datos, escribirlos dentro de la carpeta `migrations/csv`.

Cada clase debe tener un mínimo de 10 registros.

Archivo/s de trabajo:
- book_manager/preload_data/preload_data.py


### Ejercicio 06

> Puntos: 1

Armar las interfaces gráficas del sistema, estas deben operar con los CRUD de cada clase.

Archivo/s de trabajo:
- book_manager/ui/console.py

### Ejercicio 07

> Puntos: 1

Crear el archivo main.py que se encarga de ejecutar el sistema.

Archivo/s de trabajo:
- book_manager/main.py

### Devolucion
Ejercicios:
* Observaciones generales:
    - Se trabajó sobre la rama main y se debe trabajar sobre "Sprint_1".
    - No se realizó el commit por día, el error se arrastra en todos los ejercicios.

Calificación por ejercicios y puntos:
- Ejercicio 01: 0,3 pto.
- Ejercicio 02: 1,8 pto.
- Ejercicio 03: 1,8 pto.
- Ejercicio 04: 1,4 pto.
**Observaciones**: Los Servicios que manejan clases con relación entre clases (por ejemplo Libro) no válidan que las clases relanacionadas sean válidas.
- Ejercicio 05: 0,8 pto.
- Ejercicio 06: 0,8 pto.
- Ejercicio 07: 0,8 pto.

Descuenta por nombre de archivo incorrecto. -0,5 pto.
Descuenta por no ejecutar completo (run all) y no se continua con la corrección. -0,25 pto.
Descuenta por no subir ejecutado -0,25 pto.
Descuenta por no utilizar la plantilla del trabajo práctico. -0,5 pto.
Descuenta por no entregar el archivo "ipynb" -1 pto.

## Sprint 2
### Ejercicio 01

> Puntos: 1

Inicialización y configuración de la herramienta de versionado. Vamos a trabajar sobre la rama llamada "Sprint_2" y debemos partir de la rama "Sprint_1".

La estructura de directorios es:

```
book_manager/
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py
│       ├── entities/
│       │   └── entities.py
│       ├── models/
│       │   └── models.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── services/
│       │   └── services.py
│       ├── migrations
│       │   ├── csv
│       │   └── sql
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── .env
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

### Ejercicio 02

> Puntos: 1

Crear una clase ConexionDB que maneje la conexión usando SQLAlchemy.

Archivo/s de trabajo:
- book_manager/database/connection.py

### Ejercicio 03

> Puntos: 1

Crear un context manager para manejar las transacciones a la base de datos.

Archivo/s de trabajo:
- book_manager/database/connection.py


### Ejercicio 04

> Puntos: 1

Crear las tablas del sistema con sus tipos de datos y relaciones.

Archivo/s de trabajo:
- book_manager/models/models.py

### Ejercicio 05

> Puntos: 1

Migración de datos.

Leer el/los archivos del TP1 y poblar la base de datos.

Durante la migración se deben generar archivos `.sql` con las sentencias de la inserción de datos y se deben almacenar dentro de la estructura planteada.

Archivo/s de trabajo:
- book_manager/migrations/migrations.py


Tomar como base el siguiente código:

```python
def migrar_datos(carpeta_csvs: str, carpeta_sqls: str):
  """ Función encargada de la migración de datos de csv a sql.
  Se encarga de leer los archivos csv y crear los archivos sql
  para la inserción en la base de datos.

  Args:
      carpeta_csvs (str): Carpeta donde se encuentran los archivos csv de origen.
      carpeta_sqls (str): Carpeta donde se deben guardar los archivos sql generados.
  """
  pass
```

### Ejercicio 06

> Puntos: 2

Realizar la modificaciones necesarias para que todo el sistema utilice base de datos.

Archivo/s de trabajo:
- book_manager/repositories/repositories.py


### Ejercicio 07

> Puntos: 2

API del dólar + dotenv

Crear un archivo `.env` con URL de la API.
```
API_URL=https://dolarapi.com/v1/dolares
```

Crear una función `obtener_cotizaciones` dentro del servicio `ServicioCotizacionDolar` capaz de buscar, descargar y registrar las cotizaciones en la base de datos.

Archivo/s de trabajo:
- book_manager/services/services.py


### Ejercicio 08

> Puntos: 1

Agregar las siguientes opciones de menú:

- Obtener las cotizaciones por api

- Ver la lista de precios bimonetaria de los libros, es decir, en pesos y en otra moneda seleccionada

- Exportar los precios a archivo CSV para todos los tipos de monedas

Archivo/s de trabajo:
- book_manager/ui/console.py

## Sprint 3

En esta tercer entrega vamos a descargar y obtener datos de la web para trabajar con ellos.

La idea es obtener precios de nuestros competidores (librerías con venta online) y de esta forma poder compararnos con ellos y competir de forma más informada.

Para todo esto debemos partir del último push que se realizó en la entrega 2.

### Ejercicio 01

> Puntos: 1

Inicialización y configuración de la herramienta de versionado. Vamos a trabajar sobre la rama llamada "Sprint_3" y debemos partir de la rama "Sprint_2".

La estructura de directorios es:

```
book_manager/
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py
│       ├── entities/
│       │   └── entities.py
│       ├── models/
│       │   └── models.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   └── repositories.py
│       ├── scraper
│       │   └── (estructura del scraper scrapy)
│       ├── services/
│       │   └── services.py
│       ├── migrations
│       │   ├── csv
│       │   └── sql
│       ├── reportes
│       │   └── (reportes excel generados)
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── .env
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

### Ejercicio 02

> Puntos: 1

Crear una función para cargar los datos desde un sql.

### Ejercicio 03

> Puntos: 3

Implementar un scraper (CuspideSpider) con scrapy que obtenga del sitio de Cúspide los siguientes datos:
- Precio.
- url de la img.
- Formas de pago y precio.
- Descripción detallada.

Solo vamos a trabajar con nuestros libros, es decir, solo debo buscar los 10 primeros resultados de cada búsqueda (por título). No puedo buscar libros que no tengo en mi catálogo.

Implementar:
 - Loaders
 - Pipelines
