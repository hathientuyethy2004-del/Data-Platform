"""
Airflow DAG - Maps API Data Ingestion
Fetches maps/geolocation data from external API
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-platform',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 2, 1),
    'email_on_failure': False,
}

dag = DAG(
    'maps_data_ingestion',
    default_args=default_args,
    description='Fetch maps/geolocation data from external API',
    schedule_interval='0 0 * * *',  # Daily at midnight
    catchup=False,
)

DESTINATIONS = [
    {"name": "Ha Noi", "lat": 21.0285, "lon": 105.8542},
    {"name": "Ho Chi Minh", "lat": 10.7769, "lon": 106.7009},
    {"name": "Da Nang", "lat": 16.0544, "lon": 108.2022},
    {"name": "Can Tho", "lat": 10.0379, "lon": 105.7869},
    {"name": "Hai Phong", "lat": 20.8448, "lon": 106.6883}
]

def fetch_maps_data(**context):
    """Fetch maps data from external API"""
    maps_data = []
    
    for dest in DESTINATIONS:
        try:
            # Simulate maps API call
            response = {
                'destination': dest['name'],
                'latitude': dest['lat'],
                'longitude': dest['lon'],
                'popularity_score': 70 + (hash(dest['name']) % 30),
                'nearby_hotels': 50 + (hash(dest['name']) % 50),
                'avg_rating': 4.0 + (hash(dest['name']) % 10) / 10,
                'timestamp': context['execution_date'].isoformat()
            }
            
            maps_data.append(response)
            logger.info(f"✅ Fetched maps data for {dest['name']}")
            
        except Exception as e:
            logger.error(f"❌ Error fetching maps data for {dest['name']}: {e}")
    
    context['task_instance'].xcom_push(key='maps_data', value=maps_data)
    return maps_data

def enrich_with_metadata(**context):
    """Enrich maps data with metadata"""
    maps_data = context['task_instance'].xcom_pull(
        task_ids='fetch_maps_data',
        key='maps_data'
    )
    
    enriched = []
    for data in maps_data:
        enriched.append({
            'external_data_id': f"maps_{data['destination']}_{datetime.now().timestamp()}",
            'source': 'maps_api',
            'destination': data['destination'],
            'coordinates': {
                'latitude': data['latitude'],
                'longitude': data['longitude']
            },
            'metrics': {
                'popularity': data['popularity_score'],
                'hotels_count': data['nearby_hotels'],
                'avg_rating': data['avg_rating']
            },
            'ingestion_timestamp': datetime.now().isoformat()
        })
    
    context['task_instance'].xcom_push(key='enriched_data', value=enriched)
    logger.info(f"✅ Enriched {len(enriched)} maps records")
    return enriched

def publish_to_kafka(**context):
    """Publish enriched maps data to Kafka"""
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    import json
    
    enriched_data = context['task_instance'].xcom_pull(
        task_ids='enrich_with_metadata',
        key='enriched_data'
    )
    
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        for data in enriched_data:
            future = producer.send('topic_external_data', value=data)
            future.get(timeout=10)
        
        producer.close()
        logger.info(f"✅ Published {len(enriched_data)} maps records to Kafka")
        
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")
        raise

# Define tasks
fetch_task = PythonOperator(
    task_id='fetch_maps_data',
    python_callable=fetch_maps_data,
    dag=dag,
)

enrich_task = PythonOperator(
    task_id='enrich_with_metadata',
    python_callable=enrich_with_metadata,
    dag=dag,
)

publish_task = PythonOperator(
    task_id='publish_to_kafka',
    python_callable=publish_to_kafka,
    dag=dag,
)

# Define dependencies
fetch_task >> enrich_task >> publish_task
