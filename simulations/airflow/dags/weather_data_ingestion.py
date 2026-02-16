"""
Airflow DAG - Weather API Data Ingestion
Fetches weather data from external API and publishes to Kafka
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import requests
import json
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
    'weather_data_ingestion',
    default_args=default_args,
    description='Fetch weather data from external API',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
)

CITIES = ["Ha Noi", "Ho Chi Minh", "Da Nang", "Can Tho", "Hai Phong"]
WEATHER_API = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = "demo_key"

def fetch_weather_data(**context):
    """Fetch weather data from external API"""
    execution_date = context['execution_date']
    weather_data = []
    
    for city in CITIES:
        try:
            params = {
                'q': city,
                'appid': API_KEY,
                'units': 'metric'
            }
            
            # Simulate API call (in real scenario, would call actual API)
            response = {
                'city': city,
                'temperature': 25 + (hash(city) % 10),
                'humidity': 60 + (hash(city) % 30),
                'condition': 'Clear',
                'timestamp': execution_date.isoformat(),
                'wind_speed': 5 + (hash(city) % 10)
            }
            
            weather_data.append(response)
            logger.info(f"✅ Fetched weather for {city}")
            
        except Exception as e:
            logger.error(f"❌ Error fetching weather for {city}: {e}")
    
    # Store in XCom for downstream tasks
    context['task_instance'].xcom_push(key='weather_data', value=weather_data)
    return weather_data

def transform_weather_data(**context):
    """Transform weather data"""
    weather_data = context['task_instance'].xcom_pull(
        task_ids='fetch_weather_data', 
        key='weather_data'
    )
    
    transformed = []
    for data in weather_data:
        transformed.append({
            'external_data_id': f"weather_{data['city']}_{datetime.now().timestamp()}",
            'source': 'weather_api',
            'city': data['city'],
            'temperature': data['temperature'],
            'humidity': data['humidity'],
            'wind_speed': data['wind_speed'],
            'condition': data['condition'],
            'ingestion_timestamp': datetime.now().isoformat()
        })
    
    context['task_instance'].xcom_push(key='transformed_data', value=transformed)
    logger.info(f"✅ Transformed {len(transformed)} weather records")
    return transformed

def publish_to_kafka(**context):
    """Publish weather data to Kafka"""
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    
    transformed_data = context['task_instance'].xcom_pull(
        task_ids='transform_weather_data',
        key='transformed_data'
    )
    
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        for data in transformed_data:
            future = producer.send('topic_external_data', value=data)
            future.get(timeout=10)
        
        producer.close()
        logger.info(f"✅ Published {len(transformed_data)} weather records to Kafka")
        
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")
        raise

# Define tasks
fetch_task = PythonOperator(
    task_id='fetch_weather_data',
    python_callable=fetch_weather_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_weather_data',
    python_callable=transform_weather_data,
    dag=dag,
)

publish_task = PythonOperator(
    task_id='publish_to_kafka',
    python_callable=publish_to_kafka,
    dag=dag,
)

# Define dependencies
fetch_task >> transform_task >> publish_task
