"""
Data Transformation Utilities
Các hàm transformation phổ biến dùng cho Spark DataFrames
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from datetime import datetime
import json


class DataTransformations:
    """Common data transformation operations"""
    
    @staticmethod
    def parse_kafka_value_json(df: DataFrame, value_col: str = "value") -> DataFrame:
        """
        Parse Kafka message value as JSON
        
        Args:
            df: DataFrame with Kafka data (includes 'value' column)
            value_col: Column name containing JSON string
            
        Returns:
            DataFrame with parsed JSON columns
        """
        # Decode Kafka value from bytes to string and parse JSON
        return df.select(
            F.from_json(
                F.col(value_col).cast("string"),
                StructType([])  # Auto-infer schema
            ).alias("data")
        ).select("data.*")
    
    @staticmethod
    def add_processing_timestamp(df: DataFrame, new_col: str = "processing_timestamp") -> DataFrame:
        """Add processing timestamp to DataFrame"""
        return df.withColumn(new_col, F.current_timestamp())
    
    @staticmethod
    def add_window_time(
        df: DataFrame,
        timestamp_col: str,
        window_duration: str = "10 minutes",
        slide_duration: str = "10 minutes",
        output_col: str = "window"
    ) -> DataFrame:
        """
        Add tumbling/sliding window to DataFrame
        
        Args:
            df: Input DataFrame
            timestamp_col: Name of timestamp column
            window_duration: Window duration (e.g., "10 minutes", "1 hour")
            slide_duration: Slide duration (same as duration for tumbling)
            output_col: Output window column name
            
        Returns:
            DataFrame with window column
        """
        return df.withColumn(
            output_col,
            F.window(F.col(timestamp_col), window_duration, slide_duration)
        )
    
    @staticmethod
    def remove_duplicates(df: DataFrame, subset_cols: list = None) -> DataFrame:
        """Remove duplicate rows"""
        if subset_cols:
            return df.dropDuplicates(subset=subset_cols)
        return df.dropDuplicates()
    
    @staticmethod
    def filter_valid_records(df: DataFrame, user_id_col: str = "user_id") -> DataFrame:
        """Filter out records with null/empty critical fields"""
        return df.filter(
            (F.col(user_id_col).isNotNull()) &
            (F.col(user_id_col) != "")
        )
    
    @staticmethod
    def cast_timestamp(df: DataFrame, timestamp_col: str, fmt: str = "yyyy-MM-dd HH:mm:ss") -> DataFrame:
        """Cast string column to timestamp"""
        return df.withColumn(
            timestamp_col,
            F.to_timestamp(F.col(timestamp_col), fmt)
        )
    
    @staticmethod
    def enrich_with_user_segment(df: DataFrame, user_segments_df: DataFrame, user_id_col: str = "user_id") -> DataFrame:
        """
        Join with user segments for enrichment
        
        Args:
            df: Main DataFrame
            user_segments_df: User segments lookup table
            user_id_col: Column name for join key
            
        Returns:
            Enriched DataFrame
        """
        return df.join(
            user_segments_df,
            df[user_id_col] == user_segments_df["user_id"],
            "left"
        ).drop(user_segments_df["user_id"])
    
    @staticmethod
    def aggregate_by_user_window(
        df: DataFrame,
        user_id_col: str = "user_id",
        timestamp_col: str = "timestamp",
        window_duration: str = "1 hour"
    ) -> DataFrame:
        """
        Aggregate events by user and time window
        
        Args:
            df: Input DataFrame
            user_id_col: User ID column
            timestamp_col: Timestamp column
            window_duration: Window duration
            
        Returns:
            Aggregated DataFrame with count and min/max timestamps
        """
        return df.groupBy(
            F.col(user_id_col),
            F.window(F.col(timestamp_col), window_duration)
        ).agg(
            F.count("*").alias("event_count"),
            F.min(F.col(timestamp_col)).alias("first_event"),
            F.max(F.col(timestamp_col)).alias("last_event")
        )
    
    @staticmethod
    def aggregate_by_dimensions(
        df: DataFrame,
        group_by_cols: list,
        agg_col: str,
        agg_func: str = "count"
    ) -> DataFrame:
        """
        Generic aggregation by dimensions
        
        Args:
            df: Input DataFrame
            group_by_cols: Columns to group by
            agg_col: Column to aggregate on
            agg_func: Aggregation function (count, sum, avg, min, max)
            
        Returns:
            Aggregated DataFrame
        """
        agg_funcs = {
            "count": F.count,
            "sum": F.sum,
            "avg": F.avg,
            "min": F.min,
            "max": F.max
        }
        
        if agg_func not in agg_funcs:
            raise ValueError(f"Unknown aggregation function: {agg_func}")
        
        return df.groupBy(*group_by_cols).agg(
            agg_funcs[agg_func](F.col(agg_col)).alias(f"{agg_func}_{agg_col}")
        )
    
    @staticmethod
    def explode_array_column(df: DataFrame, array_col: str, output_col: str = None) -> DataFrame:
        """
        Explode array column into multiple rows
        
        Args:
            df: Input DataFrame
            array_col: Array column name
            output_col: Output column name (default: same as input)
            
        Returns:
            DataFrame with exploded column
        """
        if output_col is None:
            output_col = array_col
        
        return df.withColumn(output_col, F.explode(F.col(array_col)))
    
    @staticmethod
    def pivot_table(
        df: DataFrame,
        index_cols: list,
        pivot_col: str,
        agg_col: str,
        agg_func: str = "sum"
    ) -> DataFrame:
        """
        Pivot DataFrame (similar to pandas pivot_table)
        
        Args:
            df: Input DataFrame
            index_cols: Columns to keep as rows
            pivot_col: Column to pivot (becomes headers)
            agg_col: Column to aggregate
            agg_func: Aggregation function
            
        Returns:
            Pivoted DataFrame
        """
        agg_funcs = {
            "sum": F.sum,
            "count": F.count,
            "avg": F.avg,
            "min": F.min,
            "max": F.max
        }
        
        if agg_func not in agg_funcs:
            raise ValueError(f"Unknown aggregation function: {agg_func}")
        
        return df.groupBy(*index_cols).pivot(pivot_col).agg(
            agg_funcs[agg_func](F.col(agg_col))
        )
    
    @staticmethod
    def fill_nulls(df: DataFrame, fill_values: dict = None, default_value: any = None) -> DataFrame:
        """
        Fill null values
        
        Args:
            df: Input DataFrame
            fill_values: Dict mapping column names to fill values
            default_value: Default value for unmapped columns
            
        Returns:
            DataFrame with nulls filled
        """
        if fill_values:
            return df.fillna(fill_values)
        elif default_value is not None:
            return df.fillna(default_value)
        return df
    
    @staticmethod
    def select_and_rename(df: DataFrame, rename_map: dict) -> DataFrame:
        """
        Select and rename columns
        
        Args:
            df: Input DataFrame
            rename_map: Dict mapping old names to new names
            
        Returns:
            DataFrame with renamed columns
        """
        for old_name, new_name in rename_map.items():
            df = df.withColumnRenamed(old_name, new_name)
        return df
    
    @staticmethod
    def calculate_session_duration(
        df: DataFrame,
        user_id_col: str = "user_id",
        timestamp_col: str = "timestamp",
        output_col: str = "session_duration_seconds"
    ) -> DataFrame:
        """
        Calculate session duration (max - min timestamp per user)
        
        Args:
            df: Input DataFrame
            user_id_col: User ID column
            timestamp_col: Timestamp column
            output_col: Output column name
            
        Returns:
            DataFrame with calculated session duration
        """
        return df.groupBy(user_id_col).agg(
            (F.max(F.col(timestamp_col)) - F.min(F.col(timestamp_col))).alias(output_col)
        )
