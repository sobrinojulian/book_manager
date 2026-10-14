# Changelog

Registro de avances del Trabajo Práctico 1, organizado según los ejercicios
planteados en el README.

## Ejercicio 01 — Estructura y versionado

- Se inicializó el proyecto Book Manager y se organizó el código bajo `src/book_manager`.
- Se prepararon los módulos de entidades, repositorios, servicios, datos iniciales, interfaz de consola y punto de entrada.
- Se creó la carpeta `migrations/csv` para los archivos de persistencia.

## Ejercicio 02 — Entidades

- Se definieron las entidades `Libro`, `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Precio`, `Stock` y `CotizacionDolar`.
- Se representaron sus relaciones mediante referencias a objetos y atributos encapsulados.

## Ejercicio 03 — Persistencia

- Se implementaron repositorios CSV con operaciones CRUD para las entidades.
- Se agregaron búsquedas específicas para stock por libro e histórico de cotizaciones por tipo.
- Se incorporó la asignación de identificadores y la persistencia de cambios en `migrations/csv`.

## Ejercicio 04 — Lógica de negocio

- Se añadieron servicios para gestionar libros, precios, existencias y cotizaciones.
- Se integró la consulta de cotizaciones del dólar mediante una API, con alternativa de carga manual.
- Se incluyeron cálculos para sugerir precios en ARS a partir del valor en USD y una cotización.

## Ejercicio 05 — Datos iniciales

- Se preparó la carga inicial de géneros, editoriales, monedas, tipos de cotización y libros.
- Se agregaron registros de ejemplo para poblar los archivos CSV al iniciar la aplicación.

## Ejercicio 06 — Interfaz de consola

- Se implementaron menús para consultar y gestionar las entidades desde la CLI.
- Se incorporaron opciones de consola para consultar y modificar los datos del inventario.

## Ejercicio 07 — Punto de entrada

- Se conectaron repositorios, servicios y menús desde `main.py`.
- Se incorporó la inicialización de datos cuando el catálogo todavía está vacío y la opción para salir del sistema.

## Tareas auxiliares

- Se añadió `.gitignore` para excluir cachés de Python, entornos virtuales y artefactos locales.
- Se configuró `.vscode/settings.json` para ocultar cachés y salidas generadas en el Explorador de VS Code.

## Integración con base de datos y nuevas funciones

- Se incorporó `ConexionDB` con SQLAlchemy para administrar sesiones y transacciones, cargar la configuración desde `.env` y conectarse a PostgreSQL/Supabase mediante `psycopg`.
- Se normalizó la URL de conexión para descartar el parámetro `pgbouncer`, que no es una opción válida del driver PostgreSQL.
- Se definieron los modelos ORM de las ocho entidades, con tipos de datos, relaciones, claves foráneas y restricciones de integridad.
- Se reemplazó la persistencia CSV de los repositorios por operaciones CRUD en la base de datos, conservando las entidades de dominio y las consultas de stock e historial de cotizaciones.
- Se agregó la migración desde los CSV del TP1: genera scripts `.sql`, crea las tablas faltantes e importa los datos. Para claves naturales duplicadas conserva el primer registro, remapea referencias y suma las cantidades de stock.
- Se incorporó la URL configurable de la API del dólar desde `.env` y el servicio para descargar y guardar cotizaciones, actualizar los registros del mismo tipo y fecha y reconocer variantes conocidas de la API.
- Se añadieron opciones de consola para obtener cotizaciones por API, consultar precios en pesos y otra moneda seleccionada, y exportar a CSV los precios de todas las monedas.
- Se declararon SQLAlchemy, `psycopg` y `python-dotenv` como dependencias del proyecto.
- Se validaron la creación de tablas, las operaciones CRUD, la integridad referencial, la migración y las nuevas funciones con pruebas locales sobre SQLite y respuestas de API simuladas.
