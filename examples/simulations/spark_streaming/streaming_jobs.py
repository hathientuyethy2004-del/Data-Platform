"""
Spark Streaming Job - Real-time Event Processing
Processes application events, clickstream, and CDC changes
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, schema_of_json, window, 
    count, avg, max, explode, split, lower, trim
)
from pyspark.sql.types import StructType, StructField, StringType, LongType, MapType

def create_spark_session():
    """Create Spark session with Kafka connector"""
    return SparkSession \
        .builder \
        .appName("DataPlatform-RealTimeProcessing") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()

def define_app_event_schema():
    """Define schema for application events"""
    return StructType([
        StructField("event_id", StringType()),
        StructField("event_type", StringType()),
        StructField("user_id", StringType()),
        StructField("session_id", StringType()),
        StructField("app_type", StringType()),
        StructField("timestamp", StringType()),
        StructField("properties", MapType(StringType(), StringType()))
    ])

def process_app_events():
    """Process application events from Kafka"""
    spark = create_spark_session()
    
    # Read from Kafka topic
    df_kafka = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "topic_app_events") \
        .option("startingOffsets", "latest") \
        .option("maxOffsetsPerTrigger", 10000) \
        .load()
    
    # Parse JSON
    schema = define_app_event_schema()
    df_events = df_kafka \
        .select(from_json(col("value").cast("string"), schema).alias("event")) \
        .select("event.*")
    
    # Basic transformations
    df_processed = df_events \
        .withColumn("app_type_lower", lower(col("app_type"))) \
        .withColumn("event_hour", 
                   window(col("timestamp"), "1 hour").getItem("start"))
    
    # Aggregations per window
    df_aggregated = df_processed \
        .groupBy(window(col("timestamp"), "5 minutes"), col("event_type")) \
        .agg(
            count("event_id").alias("event_count"),
            count("user_id").alias("unique_users")
        )
    
    # Write to console (for debugging)
    query = df_aggregated \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("checkpointLocation", "/tmp/app_events_checkpoint") \
        .start()
    
    # Also write to Kafka for downstream consumers
    query_kafka = df_processed \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("topic", "topic_processed_events") \
        .option("checkpointLocation", "/tmp/processed_events_checkpoint") \
        .start()
    
    return query, query_kafka

def process_clickstream():
    """Process clickstream events in real-time"""
    spark = create_spark_session()
    
    # Read clickstream data
    df_clickstream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "topic_clickstream") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parse and enrich clickstream data
    schema = StructType([
        StructField("click_id", StringType()),
        StructField("user_id", StringType()),
        StructField("session_id", StringType()),
        StructField("page_url", StringType()),
        StructField("element_id", StringType()),
        StructField("x_coordinate", StringType()),
        StructField("y_coordinate", StringType()),
        StructField("timestamp", StringType()),
        StructField("device_type", StringType())
    ])
    
    df_parsed = df_clickstream \
        .select(from_json(col("value").cast("string"), schema).alias("click")) \
        .select("click.*")
    
    # Window-based aggregations
    df_windowed = df_parsed \
        .groupBy(
            window(col("timestamp"), "10 minutes"),
            col("page_url")
        ) \
        .agg(
            count("click_id").alias("click_count"),
            count("user_id").alias("unique_users")
        )
    
    # Write results
    query = df_windowed \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("checkpointLocation", "/tmp/clickstream_checkpoint") \
        .start()
    
    return query

def process_cdc_changes():
    """Process CDC changes from PostgreSQL"""
    spark = create_spark_session()
    
    # Read CDC changes
    df_cdc = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "topic_cdc_changes") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parse CDC schema
    schema = StructType([
        StructField("change_id", StringType()),
        StructField("table_name", StringType()),
        StructField("operation", StringType()),
        StructField("primary_key", MapType(StringType(), StringType())),
        StructField("before_values", MapType(StringType(), StringType())),
        StructField("after_values", MapType(StringType(), StringType())),
        StructField("timestamp", StringType()),
        StructField("source_database", StringType())
    ])
    
    df_changes = df_cdc \
        .select(from_json(col("value").cast("string"), schema).alias("change")) \
        .select("change.*")
    
    # Track operations per table
    df_ops_per_table = df_changes \
        .groupBy(
            window(col("timestamp"), "5 minutes"),
            col("table_name"),
            col("operation")
        ) \
        .agg(count("change_id").alias("change_count"))
    
    # Write to console
    query = df_ops_per_table \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("checkpointLocation", "/tmp/cdc_checkpoint") \
        .start()
    
    return query

def main():
    """Run all streaming jobs"""
    print("🚀 Starting Spark Streaming Jobs...")
    
    try:
        # Start all jobs
        query1, query2 = process_app_events()
        query3 = process_clickstream()
        query4 = process_cdc_changes()
        
        # Wait for streams
        query1.awaitTermination()
        
    except KeyboardInterrupt:
        print("⏹️  Streaming jobs stopped")
    except Exception as e:
        print(f"❌ Error in Spark Streaming: {e}")

if __name__ == "__main__":
    main()
