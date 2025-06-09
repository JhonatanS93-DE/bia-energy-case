# Bia Energy - Case

Autor: Jhonatan Andres Saldarriaga I.
GitHub: [JhonatanS93-DE](https://github.com/JhonatanS93-DE)

---

## Objetivo del Proyecto

Desarrollar una solución de punta a punta para enriquecer datos geoespaciales usando la API de [postcodes.io](https://postcodes.io), integrarlos a una base de datos PostgreSQL, y generar reportes optimizados que permitan análisis rápido y calidad de datos.

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

1. **Ingesta de CSV**: Se eliminan duplicados, se validan columnas lat/lon.
2. **Enriquecimiento con API**: Se consulta `postcodes.io` para obtener el código postal y país correspondiente. 
   - Control de errores por timeouts, fallas HTTP y respuestas vacías.
   - Se respeta el rate limit con `sleep(1)`.
3. **Carga en PostgreSQL**: Se crea la tabla `enriched_postcodes`.
4. **Generación de reportes**:
   - `top_postcodes.csv`: los códigos postales más comunes.
   - `quality_stats.csv`: % de coordenadas no enriquecidas.

---

## Porque esta solucion?
- Se eligió **PostgreSQL** por su robustez y rendimiento para operaciones analíticas.
- El proyecto está contenedorizado para asegurar portabilidad y reproducibilidad.
- La arquitectura puede escalarse en un entorno de Airflow o pipeline cloud en AWS.
- Se aplicaron principios de observabilidad mediante logs estructurados.

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

## Explicacion final

Este proyecto refleja prácticas de ingeniería de datos modernas: pipelines modulares, manejo  de APIs, almacenamiento eficiente y entrega de reportes. Se desarrolló con enfoque en calidad, mantenibilidad y ejecución realista bajo condiciones de producción controlada.

---

Para dudas o retroalimentación: **jhonatan1393@gmail.com**
