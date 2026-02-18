#!/usr/bin/env python3
"""
Create sample data mimicking processing layer outputs for lakehouse ingestion testing.
This simulates what the Spark processing layer would output to Parquet files.
"""

from datetime import datetime, timedelta
import random
import json
import os
from pathlib import Path

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import (
        StructType, StructField, StringType, IntegerType, 
        FloatType, TimestampType, ArrayType
    )
    import pyspark.sql.functions as F
except ImportError:
    print("Warning: PySpark not available, will skip Spark operations")

def create_spark_session():
    """Create Spark session for data generation."""
    return SparkSession.builder \
        .appName("SampleDataGenerator") \
        .master("local[4]") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()

def generate_sample_app_events(spark, num_records=1000):
    """Generate sample app events data."""
    data = []
    base_time = datetime.now() - timedelta(days=1)
    
    event_types = ["app_open", "page_view", "click", "scroll", "share", "purchase"]
    app_types = ["ios", "android", "web"]
    
    for i in range(num_records):
        event_time = base_time + timedelta(minutes=random.randint(0, 1440))
        data.append({
            "event_id": f"evt_{i:06d}",
            "user_id": f"user_{random.randint(1, 500):04d}",
            "event_type": random.choice(event_types),
            "app_type": random.choice(app_types),
            "event_timestamp": event_time,
            "properties": json.dumps({
                "session_id": f"session_{random.randint(1, 100):03d}",
                "page_name": f"page_{random.choice(['home', 'profile', 'feed', 'settings'])}",
                "value": round(random.uniform(0, 100), 2),
                "duration_ms": random.randint(100, 5000)
            }),
            "device_info": json.dumps({
                "device_type": random.choice(["phone", "tablet", "desktop"]),
                "os": random.choice(["iOS", "Android", "Windows", "MacOS"]),
                "app_version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.0"
            })
        })
    
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("user_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("app_type", StringType(), False),
        StructField("event_timestamp", TimestampType(), False),
        StructField("properties", StringType(), True),
        StructField("device_info", StringType(), True),
    ])
    
    df = spark.createDataFrame(data, schema=schema)
    return df

def generate_sample_clickstream(spark, num_records=500):
    """Generate sample clickstream session data."""
    data = []
    base_time = datetime.now() - timedelta(days=1)
    
    pages = ["home", "products", "product_detail", "cart", "checkout", "thank_you"]
    
    for i in range(num_records):
        session_time = base_time + timedelta(minutes=random.randint(0, 1440))
        num_pages = random.randint(2, 8)
        page_sequence = [random.choice(pages) for _ in range(num_pages)]
        
        data.append({
            "click_id": f"click_{i:06d}",
            "session_id": f"session_{i:06d}",
            "user_id": f"user_{random.randint(1, 500):04d}",
            "page_name": page_sequence[-1],  # last page visited
            "event_timestamp": session_time,
            "session_duration_sec": random.randint(30, 3600),
            "page_views": num_pages,
            "click_count": random.randint(1, 20),
            "scroll_depth": round(random.uniform(0, 1), 2),
            "page_sequence": ",".join(page_sequence)
        })
    
    schema = StructType([
        StructField("click_id", StringType(), False),
        StructField("session_id", StringType(), False),
        StructField("user_id", StringType(), False),
        StructField("page_name", StringType(), False),
        StructField("event_timestamp", TimestampType(), False),
        StructField("session_duration_sec", IntegerType(), True),
        StructField("page_views", IntegerType(), True),
        StructField("click_count", IntegerType(), True),
        StructField("scroll_depth", FloatType(), True),
        StructField("page_sequence", StringType(), True),
    ])
    
    df = spark.createDataFrame(data, schema=schema)
    return df

def generate_sample_cdc(spark, num_records=200):
    """Generate sample CDC (Change Data Capture) data."""
    data = []
    base_time = datetime.now() - timedelta(days=1)
    
    operations = ["INSERT", "UPDATE", "DELETE"]
    table_names = ["users", "orders", "products", "reviews"]
    
    for i in range(num_records):
        cdc_time = base_time + timedelta(minutes=random.randint(0, 1440))
        operation = random.choice(operations)
        
        before_val = json.dumps({"id": i, "value": f"old_{i}"}) if operation in ["UPDATE", "DELETE"] else None
        after_val = json.dumps({"id": i, "value": f"new_{i}", "processed": True}) if operation in ["INSERT", "UPDATE"] else None
        
        data.append({
            "cdc_id": f"cdc_{i:06d}",
            "table_name": random.choice(table_names),
            "operation_type": operation,
            "before_values": before_val,
            "after_values": after_val,
            "cdc_timestamp": cdc_time,
            "source_system": "production_db"
        })
    
    schema = StructType([
        StructField("cdc_id", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("operation_type", StringType(), False),
        StructField("before_values", StringType(), True),
        StructField("after_values", StringType(), True),
        StructField("cdc_timestamp", TimestampType(), False),
        StructField("source_system", StringType(), True),
    ])
    
    df = spark.createDataFrame(data, schema=schema)
    return df

def write_parquet_data(df, output_path, table_name):
    """Write DataFrame to Parquet format."""
    output_dir = Path(output_path) / table_name
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"  Writing {table_name} to {output_dir}...")
    df.coalesce(1).write.mode("overwrite").parquet(str(output_dir))
    
    # Count records
    record_count = df.count()
    print(f"  ✓ {table_name}: {record_count} records written")
    return record_count

def main():
    """Generate and write sample data."""
    print("\n" + "="*80)
    print("📊 SAMPLE DATA GENERATOR FOR LAKEHOUSE INGESTION")
    print("="*80 + "\n")
    
    # Create output directory
    output_path = "/workspaces/Data-Platform/processing_layer/outputs"
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    print(f"Output location: {output_path}\n")
    
    try:
        # Initialize Spark
        print("🔥 Initializing Spark session...")
        spark = create_spark_session()
        spark.sparkContext.setLogLevel("ERROR")
        print("✓ Spark session created\n")
        
        # Generate and write data
        print("📝 Generating sample data...\n")
        
        print("1️⃣  App Events Data:")
        app_events_df = generate_sample_app_events(spark, num_records=1500)
        app_count = write_parquet_data(app_events_df, output_path, "events_aggregated_realtime")
        
        print("\n2️⃣  Clickstream Data:")
        clickstream_df = generate_sample_clickstream(spark, num_records=800)
        click_count = write_parquet_data(clickstream_df, output_path, "clickstream_sessions")
        
        print("\n3️⃣  CDC Data:")
        cdc_df = generate_sample_cdc(spark, num_records=300)
        cdc_count = write_parquet_data(cdc_df, output_path, "cdc_transformed")
        
        # Stop Spark
        spark.stop()
        print("\n✓ Spark session stopped\n")
        
        # Print summary
        print("="*80)
        print("✅ SAMPLE DATA GENERATION COMPLETE")
        print("="*80)
        print(f"📊 Total Records Generated:")
        print(f"   • App Events:     {app_count:,} records")
        print(f"   • Clickstream:    {click_count:,} records")
        print(f"   • CDC Changes:    {cdc_count:,} records")
        print(f"   • TOTAL:          {app_count + click_count + cdc_count:,} records\n")
        print(f"📁 Files available in: {output_path}/")
        print("   ├─ events_aggregated_realtime/")
        print("   ├─ clickstream_sessions/")
        print("   └─ cdc_transformed/\n")
        print("🚀 Ready for lakehouse ingestion!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nFallback: Creating JSON sample data...")
        
        # Fallback to JSON if Spark not available
        create_json_sample_data(output_path)

def create_json_sample_data(output_path):
    """Fallback: Create sample data as JSON files."""
    import json
    from pathlib import Path
    
    # Create directories
    for subdir in ["events_aggregated_realtime", "clickstream_sessions", "cdc_transformed"]:
        Path(output_path) / subdir
        (Path(output_path) / subdir).mkdir(parents=True, exist_ok=True)
    
    # Sample events
    base_time = datetime.now() - timedelta(days=1)
    events = []
    for i in range(100):
        events.append({
            "event_id": f"evt_{i:06d}",
            "user_id": f"user_{random.randint(1, 50):04d}",
            "event_type": random.choice(["app_open", "page_view", "click", "purchase"]),
            "app_type": random.choice(["ios", "android", "web"]),
            "event_timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "properties": {"session_id": f"session_{random.randint(1, 10)}"},
            "device_info": {"device_type": "phone"}
        })
    
    events_file = Path(output_path) / "events_aggregated_realtime" / "part-00000.json"
    with open(events_file, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    
    print(f"✓ Created sample events: {len(events)} records")
    print(f"  Location: {events_file.parent}/")

if __name__ == "__main__":
    main()
