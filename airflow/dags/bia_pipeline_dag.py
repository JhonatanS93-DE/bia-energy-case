
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import pandas as pd
import requests
from sqlalchemy import create_engine

default_args = {
    'owner': 'Jhonatan Saldarriaga',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='bia_pipeline_dag',
    default_args=default_args,
    description='Pipeline modular para caso técnico Bia Energy',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['bia', 'etl', 'airflow'],
) as dag:

    def ingest_data():
        df = pd.read_csv('/opt/airflow/data/postcodesgeo.csv')
        df.columns = df.columns.str.strip().str.lower()

    if 'lat' in df.columns and 'lon' in df.columns:
        df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
    else:
        raise ValueError("El archivo no contiene las columnas 'lat' y 'lon' requeridas.")

    df.drop_duplicates(inplace=True)
    df.dropna(subset=['latitude', 'longitude'], inplace=True)
    df.to_pickle('/opt/airflow/data/validated.pkl')

    
    def ingest_data():
    df = pd.read_csv('/opt/airflow/data/postcodesgeo.csv')
    df.columns = df.columns.str.strip().str.lower()

    if 'lat' in df.columns and 'lon' in df.columns:
        df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
    else:
        raise ValueError("El archivo no contiene las columnas 'lat' y 'lon' requeridas.")

    df.drop_duplicates(inplace=True)
    df.dropna(subset=['latitude', 'longitude'], inplace=True)
    df.to_pickle('/opt/airflow/data/validated.pkl')

    def enrich_data():
        df = pd.read_pickle('/opt/airflow/data/validated.pkl')
        enriched = []
        chunk_size = 100  # (Limitacion de la API)
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            payload = {
                "geolocations": chunk[['longitude', 'latitude']].to_dict(orient='records')
            }
            try:
                response = requests.post("https://api.postcodes.io/postcodes", json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json().get("result", [])
                    for item in data:
                        query = item.get("query", {})
                        result = item.get("result")
                        if result:
                            record = {
                                "latitude": query.get("latitude"),
                                "longitude": query.get("longitude"),
                                "postcode": result[0].get("postcode") if result[0] else None,
                                "country": result[0].get("country") if result[0] else None,
                                "distance": result[0].get("distance") if result[0] else None
                            }
                        else:
                            record = {
                                "latitude": query.get("latitude"),
                                "longitude": query.get("longitude"),
                                "postcode": None,
                                "country": None,
                                "distance": None
                            }
                        enriched.append(record)
                else:
                    raise Exception(f"API error {response.status_code}")
            except Exception as e:
                print(f"Fallo en la petición a la API: {e}")
        pd.DataFrame(enriched).to_pickle('/opt/airflow/data/enriched.pkl')

    def store_data():
        df = pd.read_pickle('/opt/airflow/data/enriched.pkl')
        engine = create_engine('postgresql://bia_user:bia_password@bia_postgres:5432/bia_db')
        df.to_sql('enriched_postcodes', engine, if_exists='replace', index=False)

    def generate_reports():
        engine = create_engine('postgresql://bia_user:bia_password@bia_postgres:5432/bia_db')
        with engine.connect() as conn:
            top = pd.read_sql("""
                SELECT postcode, COUNT(*) AS count
                FROM enriched_postcodes
                WHERE postcode IS NOT NULL
                GROUP BY postcode
                ORDER BY count DESC
                LIMIT 10;
            """, conn)
            stats = pd.read_sql("""
                SELECT COUNT(*) FILTER (WHERE postcode IS NULL)*100.0/COUNT(*) AS pct_null
                FROM enriched_postcodes;
            """, conn)
            top.to_csv('/opt/airflow/reports/top_postcodes.csv', index=False)
            stats.to_csv('/opt/airflow/reports/quality_stats.csv', index=False)

    start = DummyOperator(task_id='start')
    ingest = PythonOperator(task_id='ingest_data', python_callable=ingest_data)
    enrich = PythonOperator(task_id='enrich_data', python_callable=enrich_data)
    store = PythonOperator(task_id='store_data', python_callable=store_data)
    report = PythonOperator(task_id='generate_reports', python_callable=generate_reports)
    end = DummyOperator(task_id='end')

    start >> ingest >> enrich >> store >> report >> end
