"""
Airflow DAG - Configuration-Driven Pipeline
Flexible pipeline that can ingest from multiple external sources
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-platform',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 2, 1),
    'email_on_failure': False,
}

dag = DAG(
    'config_driven_pipeline',
    default_args=default_args,
    description='Configuration-driven external data pipeline',
    schedule_interval='@hourly',
    catchup=False,
)

# Configuration for different data sources
SOURCES_CONFIG = {
    'social_media': {
        'enabled': True,
        'type': 'api',
        'endpoint': 'https://api.twitter.com/2/tweets/search',
        'batch_size': 100,
        'platforms': ['twitter', 'instagram', 'tiktok']
    },
    'market_data': {
        'enabled': True,
        'type': 'api',
        'endpoint': 'https://api.example.com/market',
        'batch_size': 50
    },
    'news_feed': {
        'enabled': True,
        'type': 'rss',
        'feeds': ['https://news.google.com/rss', 'https://bbc.com/news/rss.xml'],
        'batch_size': 50
    }
}

def fetch_from_source(source_name, source_config, **context):
    """Generic function to fetch data from any configured source"""
    
    if not source_config.get('enabled'):
        logger.info(f"⏭️  Source {source_name} is disabled, skipping...")
        return
    
    logger.info(f"🔄 Fetching data from {source_name}...")
    
    fetched_data = []
    
    try:
        # Simulate data fetching from different sources
        for i in range(source_config.get('batch_size', 50)):
            record = {
                'external_data_id': f"{source_name}_{i}_{datetime.now().timestamp()}",
                'source': source_name,
                'source_type': source_config['type'],
                'data': {
                    'content': f'Sample data {i} from {source_name}',
                    'metadata': source_config.get('metadata', {})
                },
                'ingestion_timestamp': datetime.now().isoformat()
            }
            fetched_data.append(record)
        
        logger.info(f"✅ Fetched {len(fetched_data)} records from {source_name}")
        context['task_instance'].xcom_push(
            key=f'{source_name}_data',
            value=fetched_data
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching from {source_name}: {e}")
        raise

def process_and_validate(**context):
    """Process and validate data from all sources"""
    
    processed_data = []
    
    for source_name in SOURCES_CONFIG.keys():
        if not SOURCES_CONFIG[source_name].get('enabled'):
            continue
        
        try:
            data = context['task_instance'].xcom_pull(
                task_ids=f'fetch_{source_name}',
                key=f'{source_name}_data'
            )
            
            if data:
                for record in data:
                    # Add processing metadata
                    record['processed_at'] = datetime.now().isoformat()
                    record['validated'] = True
                    processed_data.append(record)
                
                logger.info(f"✅ Processed {len(data)} records from {source_name}")
                
        except Exception as e:
            logger.error(f"❌ Error processing {source_name}: {e}")
    
    context['task_instance'].xcom_push(key='processed_data', value=processed_data)
    logger.info(f"✅ Total processed records: {len(processed_data)}")
    return processed_data

def publish_to_kafka(**context):
    """Publish all processed data to Kafka"""
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    import json
    
    processed_data = context['task_instance'].xcom_pull(
        task_ids='process_and_validate',
        key='processed_data'
    )
    
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        published_count = 0
        for data in processed_data:
            future = producer.send('topic_external_data', value=data)
            future.get(timeout=10)
            published_count += 1
        
        producer.close()
        logger.info(f"✅ Published {published_count} records to Kafka")
        
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")
        raise

# Create fetch tasks for each source
fetch_tasks = {}
for source_name, source_config in SOURCES_CONFIG.items():
    fetch_tasks[source_name] = PythonOperator(
        task_id=f'fetch_{source_name}',
        python_callable=fetch_from_source,
        op_kwargs={
            'source_name': source_name,
            'source_config': source_config
        },
        dag=dag,
    )

# Processing task
process_task = PythonOperator(
    task_id='process_and_validate',
    python_callable=process_and_validate,
    dag=dag,
)

# Publishing task
publish_task = PythonOperator(
    task_id='publish_to_kafka',
    python_callable=publish_to_kafka,
    dag=dag,
)

# Set dependencies
for fetch_task in fetch_tasks.values():
    fetch_task >> process_task

process_task >> publish_task
