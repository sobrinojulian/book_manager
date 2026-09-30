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
