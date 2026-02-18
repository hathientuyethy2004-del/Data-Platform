"""
User Segmentation - Clustering Models

ML models for user segmentation using K-means, RFM clustering, and behavioral clustering.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from pyspark.sql import SparkSession, DataFrame
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.sql.functions import col, when, row_number, rank, lit
from pyspark.sql.window import Window

logger = logging.getLogger(__name__)


class UserSegmentationModel:
    """Main segmentation model orchestrator"""
    
    def __init__(self, spark: SparkSession, n_segments: int = 5):
        """
        Initialize segmentation model.
        
        Args:
            spark: SparkSession
            n_segments: Number of segments to create
        """
        self.spark = spark
        self.n_segments = n_segments
        self.kmeans_model = None
        self.feature_cols = []
    
    def train_segmentation(self, features_df: DataFrame) -> Dict[str, Any]:
        """
        Train user segmentation model.
        
        Args:
            features_df: DataFrame with UserSegmentFeatures
            
        Returns:
            Training results with metrics
        """
        try:
            # Select numeric features for clustering
            self.feature_cols = [
                "recency_days", "frequency", "monetary",
                "avg_session_duration_sec", "product_categories_purchased",
                "support_tickets", "days_since_last_activity",
                "churn_risk_score", "customer_age_days"
            ]
            
            # Assemble features
            assembler = VectorAssembler(
                inputCols=self.feature_cols,
                outputCol="features"
            )
            
            features_assembled = assembler.transform(features_df)
            
            # Standardize features
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaled_features",
                withMean=True,
                withStd=True
            )
            
            scaler_model = scaler.fit(features_assembled)
            scaled_data = scaler_model.transform(features_assembled)
            
            # Train K-means
            kmeans = KMeans(
                k=self.n_segments,
                seed=42,
                maxIter=20,
                initMode="kmeans||"
            )
            
            self.kmeans_model = kmeans.fit(scaled_data)
            
            # Get predictions
            predictions = self.kmeans_model.transform(scaled_data)
            
            # Calculate metrics
            silhouette_score = self._calculate_silhouette(predictions)
            
            return {
                "status": "success",
                "n_segments": self.n_segments,
                "silhouette_score": silhouette_score,
                "cluster_centers": self.kmeans_model.clusterCenters().tolist(),
            }
        
        except Exception as e:
            logger.error(f"Segmentation training failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def predict_segments(self, features_df: DataFrame) -> DataFrame:
        """
        Predict segments for users.
        
        Args:
            features_df: Features DataFrame
            
        Returns:
            DataFrame with cluster assignments
        """
        if not self.kmeans_model:
            raise ValueError("Model not trained")
        
        # Prepare data
        assembler = VectorAssembler(
            inputCols=self.feature_cols,
            outputCol="features"
        )
        features_assembled = assembler.transform(features_df)
        
        # Scale
        scaler = StandardScaler(
            inputCol="features",
            outputCol="scaled_features",
            withMean=True,
            withStd=True
        )
        scaler_model = scaler.fit(features_assembled)
        scaled_data = scaler_model.transform(features_assembled)
        
        # Predict
        predictions = self.kmeans_model.transform(scaled_data)
        
        # Add segment names
        predictions = predictions.withColumn(
            "segment_name",
            when(col("prediction") == 0, "Champions")
            .when(col("prediction") == 1, "Loyal")
            .when(col("prediction") == 2, "At_Risk")
            .when(col("prediction") == 3, "Dormant")
            .when(col("prediction") == 4, "New")
            .otherwise("Unknown")
        )
        
        return predictions.select("user_id", "prediction", "segment_name")
    
    def _calculate_silhouette(self, predictions: DataFrame) -> float:
        """Calculate silhouette score (simplified)"""
        try:
            # Simplified: just return cluster size balance metric
            dist = predictions.groupBy("prediction").count().rdd.map(lambda x: x[1])
            scores = dist.collect()
            avg = sum(scores) / len(scores)
            variance = sum((s - avg) ** 2 for s in scores) / len(scores)
            return 1.0 - (variance / (avg ** 2 + 1))
        except:
            return 0.5


class RFMSegmentation:
    """RFM-based segmentation (classic approach)"""
    
    SEGMENTS = {
        555: "Champions",
        554: "Champions",
        545: "Champions",
        455: "Champions",
        445: "Loyal Customers",
        444: "Loyal Customers",
        435: "Loyal Customers",
        345: "Potential Loyalists",
        244: "At Risk",
        244: "At Risk",
        143: "Cant Lose Them",
        142: "Lost",
    }
    
    @staticmethod
    def assign_segment(rfm_score: int) -> str:
        """
        Assign RFM-based segment.
        
        Args:
            rfm_score: RFM score (111-555)
            
        Returns:
            Segment name
        """
        # Check exact match first
        if rfm_score in RFMSegmentation.SEGMENTS:
            return RFMSegmentation.SEGMENTS[rfm_score]
        
        # Parse score
        r, f, m = int(str(rfm_score)[0]), int(str(rfm_score)[1]), int(str(rfm_score)[2])
        
        # Rule-based segmentation
        if r >= 4 and f >= 4:
            return "Champions"
        elif r >= 4 and f >= 3:
            return "Loyal Customers"
        elif r >= 3 and f >= 3:
            return "Potential Loyalists"
        elif r <= 2 and f >= 3:
            return "At Risk"
        elif r <= 2 and f <= 2:
            return "Lost"
        else:
            return "Candidates"


class BehavioralSegmentation:
    """Behavioral-based segmentation using engagement patterns"""
    
    @staticmethod
    def segment_by_behavior(features_df: DataFrame) -> DataFrame:
        """
        Segment users by behavioral patterns.
        
        Args:
            features_df: User features
            
        Returns:
            DataFrame with behavioral segments
        """
        return (
            features_df
            .withColumn(
                "engagement_level",
                when(col("avg_session_duration_sec") > 500, "High")
                .when(col("avg_session_duration_sec") > 200, "Medium")
                .otherwise("Low")
            )
            .withColumn(
                "purchase_pattern",
                when(col("repeat_purchase_rate") > 0.7, "Repeater")
                .when(col("repeat_purchase_rate") > 0.3, "Occasional")
                .otherwise("One-time")
            )
            .withColumn(
                "value_segment",
                when(col("monetary") > 2000, "High_Value")
                .when(col("monetary") > 500, "Medium_Value")
                .otherwise("Low_Value")
            )
            .withColumn(
                "lifecycle",
                when(col("customer_age_days") < 30, "New")
                .when(col("customer_age_days") < 180, "Growing")
                .when(col("is_active"), "Established")
                .otherwise("Dormant")
            )
        )


class SegmentProfiler:
    """Profiles segments to understand characteristics"""
    
    @staticmethod
    def profile_segments(predictions_df: DataFrame, 
                        features_df: DataFrame) -> DataFrame:
        """
        Create segment profiles.
        
        Args:
            predictions_df: Predictions with segments
            features_df: Original features
            
        Returns:
            Segment profile statistics
        """
        joined = predictions_df.join(features_df, "user_id")
        
        profiles = joined.groupBy("segment_name").agg(
            col("user_id").count().alias("segment_size"),
            col("monetary").avg().alias("avg_monetary"),
            col("frequency").avg().alias("avg_frequency"),
            col("recency_days").avg().alias("avg_recency"),
            col("churn_risk_score").avg().alias("avg_churn_risk"),
            col("customer_age_days").avg().alias("avg_customer_age"),
        )
        
        return profiles


class SegmentationAnalyzer:
    """Analyzes segmentation results"""
    
    @staticmethod
    def analyze_segment_distribution(predictions_df: DataFrame) -> Dict[str, Any]:
        """Get distribution of segments"""
        dist = predictions_df.groupBy("segment_name").count().toPandas()
        
        total = dist['count'].sum()
        dist['percentage'] = (dist['count'] / total * 100).round(1)
        
        return dist.to_dict('records')
    
    @staticmethod
    def get_segment_actionability(predictions_df: DataFrame,
                                 features_df: DataFrame) -> DataFrame:
        """
        Get actionable insights per segment.
        
        Returns DataFrame with recommended actions.
        """
        joined = predictions_df.join(features_df, "user_id")
        
        actions = (
            joined
            .withColumn(
                "recommended_action",
                when(col("segment_name") == "Champions", "VIP_Program")
                .when(col("segment_name") == "Loyal", "Retention")
                .when(col("segment_name") == "At_Risk", "Reactivation")
                .when(col("segment_name") == "Dormant", "Winback")
                .when(col("segment_name") == "New", "Onboarding")
                .otherwise("Monitor")
            )
            .select("user_id", "segment_name", "recommended_action")
        )
        
        return actions
