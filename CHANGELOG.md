# Changelog

## Trabajo Práctico 3

## Ejercicio 01 — Estructura y versionado
- Se creó los directorios `scraper` y `reportes`.

## Ejercicio 02 — Carga desde archivos `.sql`

- Se incorporó una función para cargar mediante SQLAlchemy los datos de los archivos `.sql` de migración, respetando el orden de dependencias y ejecutando la carga en una única transacción.

## Ejercicio 03 — Scraper de Cúspide

- Se incorporó `CuspideSpider` para buscar únicamente los títulos existentes en el catálogo, con un máximo de 10 productos únicos por búsqueda.
- Se agregaron un item y un loader para normalizar el precio, la URL de imagen, los medios de pago y la descripción detallada de cada producto.
- Se añadió un pipeline que exporta los resultados a archivos JSON Lines dentro de `reportes/`, junto con la configuración del proyecto Scrapy y su dependencia.
- Se verificaron el descubrimiento del spider, el límite de resultados, la extracción de datos y la escritura del pipeline con respuestas simuladas; no se ejecutó una búsqueda contra la base de datos ni el sitio en vivo.

## Ejercicio 04 — Comparación de precios y alertas

- Se agregó una opción de menú que solicita en cada ejecución la diferencia mínima en ARS y lanza el scraper con ese umbral.
- Se incorporó la comparación entre precio interno y precio web, y la generación por ejecución de un CSV fechado en `reportes/` con las diferencias que superan el umbral.
- Se verificaron el parseo de importes, el filtrado por umbral, la escritura del CSV y el descubrimiento del spider con pruebas simuladas; no se realizó una búsqueda real contra la base de datos ni el sitio.

## Ejercicio 05 — Reporte de precios en Excel

- Se agregó la generación de un archivo Excel por ejecución del scraper, con el libro, el precio interno, el precio web, la diferencia y la fecha de extracción.
- Los reportes se guardan en `reportes/`; se añadió `openpyxl` a las dependencias del proyecto.
- Se verificó la generación y reapertura de un reporte de prueba, incluyendo sus encabezados, valores y fecha.

## Ejercicio 06 — Auditoría del sistema

- Se incorporó el decorador `auditar_operacion` para registrar las operaciones de los repositorios, incluyendo su acción, fecha y detalles en formato JSON.
- Se agregó la tabla `auditorias` y un repositorio para consultar los eventos más recientes; la opción **Ver historial de auditoría** quedó disponible en el menú.
- Se verificaron con SQLite en memoria el registro de altas, consultas y eliminaciones, incluso cuando la consulta no encuentra un registro.

## Ejercicio 07 — Opciones de menú

- Se agregaron las opciones **Ejecutar scraping**, **Generar reporte** y **Ver historial de auditoría** al menú principal.
- La opción **Generar reporte** crea el Excel de comparación a partir de la extracción JSONL más reciente guardada en `reportes/`.


## Trabajo Práctico 2
Registro de avances del Trabajo Práctico 2, organizado según los ejercicios
planteados en el README.

### Ejercicio 01 — Estructura y versionado

- Se inicializó el proyecto Book Manager y se organizó el código bajo `src/book_manager`.
- Se prepararon los módulos de entidades, repositorios, servicios, datos iniciales, interfaz de consola y punto de entrada.
- Se creó la carpeta `migrations/csv` para los archivos de persistencia.

### Ejercicio 02 — Entidades

- Se definieron las entidades `Libro`, `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Precio`, `Stock` y `CotizacionDolar`.
- Se representaron sus relaciones mediante referencias a objetos y atributos encapsulados.

### Ejercicio 03 — Persistencia

- Se implementaron repositorios CSV con operaciones CRUD para las entidades.
- Se agregaron búsquedas específicas para stock por libro e histórico de cotizaciones por tipo.
- Se incorporó la asignación de identificadores y la persistencia de cambios en `migrations/csv`.

### Ejercicio 04 — Lógica de negocio

- Se añadieron servicios para gestionar libros, precios, existencias y cotizaciones.
- Se integró la consulta de cotizaciones del dólar mediante una API, con alternativa de carga manual.
- Se incluyeron cálculos para sugerir precios en ARS a partir del valor en USD y una cotización.

### Ejercicio 05 — Datos iniciales

- Se preparó la carga inicial de géneros, editoriales, monedas, tipos de cotización y libros.
- Se agregaron registros de ejemplo para poblar los archivos CSV al iniciar la aplicación.

### Ejercicio 06 — Interfaz de consola

- Se implementaron menús para consultar y gestionar las entidades desde la CLI.
- Se incorporaron opciones de consola para consultar y modificar los datos del inventario.

### Ejercicio 07 — Punto de entrada

- Se conectaron repositorios, servicios y menús desde `main.py`.
- Se incorporó la inicialización de datos cuando el catálogo todavía está vacío y la opción para salir del sistema.

### Tareas auxiliares

- Se añadió `.gitignore` para excluir cachés de Python, entornos virtuales y artefactos locales.
- Se configuró `.vscode/settings.json` para ocultar cachés y salidas generadas en el Explorador de VS Code.

### Integración con base de datos y nuevas funciones

- Se incorporó `ConexionDB` con SQLAlchemy para administrar sesiones y transacciones, cargar la configuración desde `.env` y conectarse a PostgreSQL/Supabase mediante `psycopg`.
- Se normalizó la URL de conexión para descartar el parámetro `pgbouncer`, que no es una opción válida del driver PostgreSQL.
- Se definieron los modelos ORM de las ocho entidades, con tipos de datos, relaciones, claves foráneas y restricciones de integridad.
- Se reemplazó la persistencia CSV de los repositorios por operaciones CRUD en la base de datos, conservando las entidades de dominio y las consultas de stock e historial de cotizaciones.
- Se agregó la migración desde los CSV del TP1: genera scripts `.sql`, crea las tablas faltantes e importa los datos. Para claves naturales duplicadas conserva el primer registro, remapea referencias y suma las cantidades de stock.
- Se incorporó la URL configurable de la API del dólar desde `.env` y el servicio para descargar y guardar cotizaciones, actualizar los registros del mismo tipo y fecha y reconocer variantes conocidas de la API.
- Se añadieron opciones de consola para obtener cotizaciones por API, consultar precios en pesos y otra moneda seleccionada, y exportar a CSV los precios de todas las monedas.
- Se declararon SQLAlchemy, `psycopg` y `python-dotenv` como dependencias del proyecto.
- Se validaron la creación de tablas, las operaciones CRUD, la integridad referencial, la migración y las nuevas funciones con pruebas locales sobre SQLite y respuestas de API simuladas.
