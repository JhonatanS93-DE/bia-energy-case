# Autor: Jhonatan Saldarriaga (Case Tecnico Bia Energy)
# Paso 1: Leer CSV y validar datos
import pandas as pd
import logging
import requests
from sqlalchemy import create_engine
import sys
sys.path.append("src")
from utils import setup_logger
import time
import random

logger = setup_logger()

def load_and_validate_csv(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip().str.lower()
        logger.info(f"Archivo CSV cargado con {len(df)} filas y columnas: {df.columns.tolist()}")

        if 'lat' in df.columns and 'lon' in df.columns:
            df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        else:
            raise ValueError("El archivo no contiene las columnas 'lat' y 'lon' requeridas.")

        df.drop_duplicates(inplace=True)
        df.dropna(subset=['latitude', 'longitude'], inplace=True)
        df = df[(df['latitude'].apply(lambda x: isinstance(x, (float, int)))) &
                (df['longitude'].apply(lambda x: isinstance(x, (float, int))))]
        return df
    except Exception as e:
        logger.error(f"Error al leer y validar CSV: {e}")
        raise

# Paso 2: Enriquecimiento con API externa (Se uso Bulk Reverse Geocode)
import time
import random

def enrich_coordinates_bulk(df: pd.DataFrame) -> pd.DataFrame:
    enriched = []
    chunk_size = 100

    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        payload = {
            "geolocations": chunk[['longitude', 'latitude']].to_dict(orient='records')
        }

        success = False
        retries = 5
        delay = 1

        for attempt in range(retries):
            try:
                response = requests.post("https://api.postcodes.io/postcodes", json=payload, timeout=10)

                if response.status_code == 200:
                    data = response.json().get("result", [])
                    for item in data:
                        query = item.get("query", {})
                        result = item.get("result")
                        if result:
                            enriched.append({
                                "latitude": query.get("latitude"),
                                "longitude": query.get("longitude"),
                                "postcode": result[0].get("postcode") if result[0] else None,
                                "country": result[0].get("country") if result[0] else None,
                                "admin_district": result[0].get("admin_district") if result[0] else None,
                                "nhs_ha": result[0].get("nhs_ha") if result[0] else None,
                                "distance": result[0].get("distance") if result[0] else None
                            })
                        else:
                            enriched.append({
                                "latitude": query.get("latitude"),
                                "longitude": query.get("longitude"),
                                "postcode": None,
                                "country": None,
                                "admin_district": None,
                                "nhs_ha": None,
                                "distance": None
                            })
                    success = True
                    break
                else:
                    logger.warning(f"Intento {attempt+1}: HTTP {response.status_code}")
            except Exception as e:
                logger.warning(f"Intento {attempt+1} falló: {e}")

            time.sleep(delay)
            delay *= 2  # backoff
            delay += random.uniform(0, 1)

        if not success:
            logger.error("Fallo permanente al consultar chunk, se marcará todo como None.")
            for row in chunk.itertuples():
                enriched.append({
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "postcode": None,
                    "country": None,
                    "distance": None
                })

    return pd.DataFrame(enriched)

# Paso 3: Almacenamiento en base de datos PostgreSQL
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
            SELECT COUNT(*) FILTER (WHERE postcode IS NULL)*100.0/COUNT(*) AS porcentaje_null 
            FROM enriched_postcodes;
        """, conn)

        top_postcodes.to_csv("reports/top_postcodes.csv", index=False)
        quality_stats.to_csv("reports/quality_stats.csv", index=False)

        logger.info("Reportes generados en /reports")

# Ejecución principal
if __name__ == "__main__":
    df = load_and_validate_csv("data/test_postcodes.csv")
    enriched_df = enrich_coordinates_bulk(df)
    enriched_df.to_csv("reports/enriched_postcodes.csv", index=False)
    # db_uri = "postgresql://bia_user:bia_password@postgres:5432/bia_db"
    db_uri = "postgresql://bia_user:bia_password@localhost:5432/bia_db"
    save_to_postgres(enriched_df, db_uri)
    generate_report(db_uri)
