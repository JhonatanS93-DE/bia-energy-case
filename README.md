# Bia Energy - Case

Autor: Jhonatan Andres Saldarriaga I.
GitHub: [JhonatanS93-DE](https://github.com/JhonatanS93-DE)

Este archivo contiene la solución al implementar un pipeline modular para ingestión, enriquecimiento, almacenamiento y generación de reportes sobre datos geoespaciales.
---

## Objetivo del Proyecto

Desarrollar una solución de punta a punta para enriquecer coordenadas geoespaciales (`latitude`, `longitude`) usando la API de [postcodes.io](https://postcodes.io), transformarlas en códigos postales, integrarlas a una base de datos PostgreSQL, y generar reportes optimizados que permitan análisis rápido y control de calidad de datos.


---

## Tecnologías y herramientas utilizadas
- **Python 3.10**
- **Docker + Docker Compose**
- **PostgreSQL 14**
- **Pandas, Requests, SQLAlchemy**
- **Postcodes.io API**
- **Git y GitHub**

---

## Estructura del Proyecto

```
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── data/
│   └── postcodes_geo.csv
├── reports/
│   ├── top_postcodes.csv
│   └── quality_stats.csv
├── src/
│   ├── bia_pipeline.py
│   └── utils.py
├── airflow/
│   └── dags/
│       └── bia_pipeline_dag.py
```

---

## Ejecución del Proyecto (Local via Docker)

### 1. Clona el repositorio
```bash
git clone https://github.com/JhonatanS93-DE/bia-energy-case.git
cd bia-energy-case
```

### 2. Coloca el archivo `postcodes_geo.csv` en la carpeta `data/`

### 3. Construye y ejecuta los contenedores:
```bash
docker-compose up --build
```

---

## Flujo de datos

1. **Ingesta de datos**: se toma un archivo `CSV` que contiene columnas `latitude` y `longitude`.
2. **Enriquecimiento**:
   - Se utiliza el endpoint de *Bulk Reverse Geocode* de `postcodes.io`, lo que permite enriquecer múltiples coordenadas en una sola petición.
   - Se controlan errores de red, fallos HTTP y respuestas vacías.
   - Permite escalar sin problema gracias a procesamiento por lotes (chunks de 100).
3. **Almacenamiento**: los datos enriquecidos se guardan en PostgreSQL en la tabla `enriched_postcodes`.
4. **Reportes**:
   - `top_postcodes.csv`: los 10 códigos postales más frecuentes.
   - `quality_stats.csv`: porcentaje de registros no enriquecidos.


---

## Porque esta solucion?
- Se eligió **PostgreSQL** por su robustez y rendimiento para operaciones analíticas.
- El proyecto está contenedorizado para asegurar portabilidad y reproducibilidad.
- La arquitectura puede escalarse en un entorno de Airflow o pipeline cloud en AWS.
- Se aplicaron principios de observabilidad mediante logs estructurados.

---
## Logging centralizado

Se implementa un sistema de logging reutilizable en `src/utils.py`, que permite capturar y formatear eventos clave del pipeline:

```
2024-06-09 12:00:00 - INFO - Archivo CSV cargado con 1000 filas
2024-06-09 12:01:02 - ERROR - Fallo en la petición a la API: Timeout
```

Esto permite monitorear fácilmente el comportamiento del pipeline en entornos reales.

---

## Mejoras para hacerlo una solucion escalable

### Escalabilidad con Airflow (implementación adicional)
Como mejora pensada para entornos productivos y escalables, se propone integrar Apache Airflow para orquestar el pipeline. Esto permitirá:

- Ejecutar tareas de ingestión, enriquecimiento, almacenamiento y reporte de forma secuencial y automatizada.
- Monitorizar y programar la ejecución diaria/semanal de procesamiento de datos.
- Manejar reintentos automáticos ante errores.

Esta versión con Airflow se entrega como una carpeta adicional (`airflow/`) que contiene un DAG de ejemplo para ejecutar el flujo completo, permitiendo demostrar cómo se adapta la solución a escenarios reales de orquestación de datos.

- Incorporar cache local para evitar peticiones duplicadas a la API.
- Test unitarios con `pytest`.

---

## Diagrama de Arquitectura

El siguiente diagrama muestra el flujo de datos completo del pipeline:

📄 [Ver diagrama editable en draw.io](docs/diagrama_arquitectura_bia.drawio.png)

Puedes abrirlo desde [https://app.diagrams.net](https://app.diagrams.net) arrastrando el archivo aqui se podria editar una mejora futura.

---

## Explicacion final

Este proyecto refleja prácticas de ingeniería de datos modernas: pipelines modulares, manejo de APIs, almacenamiento eficiente y entrega de reportes. Se desarrolló con enfoque en calidad, mantenibilidad y ejecución realista bajo condiciones de producción controlada.

---

Para dudas o retroalimentación: **jhonatan1393@gmail.com** o escribir un comentario en el repositorio de github
