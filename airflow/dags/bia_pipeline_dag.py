from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import pandas as pd
import requests
import time
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
    tags=['bia', 'etl'],
) as dag:

    def ingest_data():
        df = pd.read_csv('/opt/airflow/data/postcodes_geo.csv')
        df.drop_duplicates(inplace=True)
        df.dropna(subset=['latitude', 'longitude'], inplace=True)
        df.to_pickle('/opt/airflow/data/validated.pkl')

    def enrich_data():
        df = pd.read_pickle('/opt/airflow/data/validated.pkl')
        enriched = []
        for _, row in df.iterrows():
            lat, lon = row['latitude'], row['longitude']
            try:
                response = requests.get(f'https://api.postcodes.io/postcodes?lon={lon}&lat={lat}', timeout=5)
                if response.status_code == 200 and response.json().get('result'):
                    result = response.json()['result'][0]
                    enriched.append({
                        'latitude': lat,
                        'longitude': lon,
                        'postcode': result['postcode'],
                        'country': result['country']
                    })
                else:
                    enriched.append({'latitude': lat, 'longitude': lon, 'postcode': None, 'country': None})
            except:
                enriched.append({'latitude': lat, 'longitude': lon, 'postcode': None, 'country': None})
            time.sleep(1)
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
