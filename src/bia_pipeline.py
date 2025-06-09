# Proyecto: Solución caso técnico Bia Energy
# Autor: Jhonatan Saldarriaga

# Paso 1: Leer CSV y validar datos
import pandas as pd
import logging
from src.utils import setup_logger

logger = setup_logger()

def load_and_validate_csv(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Archivo CSV cargado con {len(df)} filas")
        df.drop_duplicates(inplace=True)
        df.dropna(subset=['latitude', 'longitude'], inplace=True)
        df = df[(df['latitude'].apply(lambda x: isinstance(x, (float, int)))) &
                (df['longitude'].apply(lambda x: isinstance(x, (float, int))))]
        return df
    except Exception as e:
        logger.error(f"Error al leer y validar CSV: {e}")
        raise

# Paso 2: Enriquecimiento con API externa
import requests
import time

def enrich_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    enriched = []
    for index, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        try:
            response = requests.get(f"https://api.postcodes.io/postcodes?lon={lon}&lat={lat}", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('result'):
                    enriched.append({
                        'latitude': lat,
                        'longitude': lon,
                        'postcode': result['result'][0]['postcode'],
                        'country': result['result'][0]['country']
                    })
                else:
                    enriched.append({'latitude': lat, 'longitude': lon, 'postcode': None, 'country': None})
            else:
                logger.warning(f"Error en respuesta API para coordenadas ({lat},{lon}) - status: {response.status_code}")
        except Exception as e:
            logger.error(f"Fallo al conectar API: {e}")
        time.sleep(1)  # rate limiting
    return pd.DataFrame(enriched)

# Paso 3: Almacenamiento en base de datos PostgreSQL
from sqlalchemy import create_engine

def save_to_postgres(df: pd.DataFrame, db_url: str):
    try:
        engine = create_engine(db_url)
        df.to_sql('enriched_postcodes', engine, if_exists='replace', index=False)
        logger.info("Datos guardados exitosamente en PostgreSQL")
    except Exception as e:
        logger.error(f"Error guardando en PostgreSQL: {e}")

# Paso 4: Generar reportes
def generate_report(db_url: str):
    engine = create_engine(db_url)
    with engine.connect() as conn:
        top_postcodes = pd.read_sql("""
            SELECT postcode, COUNT(*) AS count FROM enriched_postcodes
            WHERE postcode IS NOT NULL
            GROUP BY postcode
            ORDER BY count DESC
            LIMIT 10
        """, conn)

        quality_stats = pd.read_sql("""
            SELECT COUNT(*) FILTER (WHERE postcode IS NULL)*100.0/COUNT(*) AS pct_null
            FROM enriched_postcodes;
        """, conn)

        top_postcodes.to_csv("reports/top_postcodes.csv", index=False)
        quality_stats.to_csv("reports/quality_stats.csv", index=False)

        logger.info("Reportes generados en /reports")

# Ejecución principal
if __name__ == "__main__":
    df = load_and_validate_csv("data/postcodes_geo.csv")
    enriched_df = enrich_coordinates(df)
    db_uri = "postgresql://bia_user:bia_password@postgres:5432/bia_db"
    save_to_postgres(enriched_df, db_uri)
    generate_report(db_uri)
