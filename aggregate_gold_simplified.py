#!/usr/bin/env python3
"""
Simplified Gold Layer Aggregation using Pandas
Creates business-ready KPI tables from Silver layer
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np

# Setup paths
WORKSPACE_BASE = Path("/workspaces/Data-Platform")
LAKEHOUSE_BASE = Path(os.getenv("LAKEHOUSE_BASE_PATH", WORKSPACE_BASE / "lakehouse_data"))
SILVER_PATH = Path(os.getenv("SILVER_PATH", LAKEHOUSE_BASE / "silver"))
GOLD_PATH = Path(os.getenv("GOLD_PATH", LAKEHOUSE_BASE / "gold"))
LOGS_DIR = Path(os.getenv("LOGS_DIR", LAKEHOUSE_BASE / "logs"))

# Create directories
GOLD_PATH.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "="*80)
print("🏆 GOLD LAYER AGGREGATION JOB (SIMPLIFIED)")
print("="*80 + "\n")

def aggregate_event_metrics() -> Dict[str, Any]:
    """Aggregate event metrics by hour."""
    print("📊 Aggregating Event Metrics...")
    
    source_path = SILVER_PATH / "app_events" / "data.parquet"
    target_path = GOLD_PATH / "event_metrics"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Silver
        df = pd.read_parquet(source_path)
        df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
        
        # Group by hour and event type
        metrics = df.groupby([
            pd.Grouper(key='event_timestamp', freq='1h'),
            'event_type',
            'app_type'
        ]).agg({
            'event_id': 'count',
            'user_id': 'nunique'
        }).reset_index()
        
        metrics.columns = ['metric_hour', 'event_type', 'app_type', 'total_events', 'unique_users']
        metrics['metric_date'] = metrics['metric_hour'].dt.date
        
        # Calculate rates
        metrics['events_per_user'] = metrics['total_events'] / metrics['unique_users']
        metrics['created_at'] = datetime.now()
        
        print(f"  ✓ Created {len(metrics):,} hourly metrics")
        print(f"  ✓ Event types: {metrics['event_type'].nunique()}")
        print(f"  ✓ App types: {metrics['app_type'].nunique()}")
        
        # Write to Gold
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        metrics.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}\n")
        
        return {
            "status": "success",
            "table": "event_metrics_gold",
            "records": len(metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def create_user_segments() -> Dict[str, Any]:
    """Create user behavioral segments."""
    print("📋 Creating User Segments...")
    
    source_path = SILVER_PATH / "users" / "data.parquet"
    target_path = GOLD_PATH / "user_segments"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Silver
        users = pd.read_parquet(source_path)
        
        # Calculate engagement score (0-100)
        # Normalize: total_events, days_active, event_types_count
        score_components = pd.DataFrame()
        score_components['events_score'] = (users['total_events'] / users['total_events'].max()) * 30
        score_components['recency_score'] = ((30 - users['days_since_last_event'].clip(0, 30)) / 30) * 40
        score_components['diversity_score'] = (users['event_types_count'] / users['event_types_count'].max()) * 30
        
        users['engagement_score'] = (
            score_components['events_score'] + 
            score_components['recency_score'] + 
            score_components['diversity_score']
        ).round(2)
        
        # Define segments
        def segment_user(score):
            if score >= 80:
                return 'VIP'
            elif score >= 60:
                return 'Active'
            elif score >= 40:
                return 'Regular'
            else:
                return 'Inactive'
        
        users['segment'] = users['engagement_score'].apply(segment_user)
        
        # Calculate churn risk
        users['churn_risk'] = 100 - users['engagement_score']
        users['churn_risk_level'] = users['churn_risk'].apply(
            lambda x: 'High' if x >= 60 else ('Medium' if x >= 40 else 'Low')
        )
        
        users['created_at'] = datetime.now()
        
        # Summary stats
        segment_counts = users['segment'].value_counts()
        print(f"  ✓ Segmented {len(users):,} users:")
        for segment, count in segment_counts.items():
            pct = (count / len(users)) * 100
            print(f"    • {segment}: {count:,} ({pct:.1f}%)")
        
        # Write to Gold
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        users.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}\n")
        
        return {
            "status": "success",
            "table": "user_segments_gold",
            "records": len(users),
            "segments": dict(segment_counts),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def create_daily_summary() -> Dict[str, Any]:
    """Create daily KPI summary."""
    print("📈 Creating Daily Summary...")
    
    events_path = SILVER_PATH / "app_events" / "data.parquet"
    users_path = SILVER_PATH / "users" / "data.parquet"
    target_path = GOLD_PATH / "daily_summary"
    
    try:
        if not events_path.exists() or not users_path.exists():
            print(f"  ⚠️  Source not found")
            return {"status": "skipped", "records": 0}
        
        # Read Silver
        events = pd.read_parquet(events_path)
        users = pd.read_parquet(users_path)
        
        events['event_timestamp'] = pd.to_datetime(events['event_timestamp'])
        events['event_date'] = events['event_timestamp'].dt.date
        
        # Daily aggregation
        daily = events.groupby('event_date').agg({
            'user_id': 'nunique',
            'event_id': 'count',
            'event_type': lambda x: x.nunique()
        }).reset_index()
        
        daily.columns = ['summary_date', 'daily_users', 'total_events', 'event_types']
        
        # Calculate new users
        users['first_seen'] = pd.to_datetime(users['first_seen']).dt.date
        new_users_daily = users.groupby('first_seen').size().reset_index(name='new_users')
        new_users_daily.columns = ['summary_date', 'new_users']
        
        # Merge
        daily = daily.merge(new_users_daily, on='summary_date', how='left')
        daily['new_users'] = daily['new_users'].fillna(0).astype(int)
        
        # Metrics
        daily['returning_users'] = daily['daily_users'] - daily['new_users']
        daily['avg_events_per_user'] = (daily['total_events'] / daily['daily_users']).round(2)
        daily['created_at'] = datetime.now()
        
        print(f"  ✓ Created summary for {len(daily):,} days")
        if len(daily) > 0:
            print(f"  ✓ Avg daily users: {daily['daily_users'].mean():.0f}")
            print(f"  ✓ Avg daily events: {daily['total_events'].mean():.0f}")
        
        # Write to Gold
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        daily.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}\n")
        
        return {
            "status": "success",
            "table": "daily_summary_gold",
            "records": len(daily),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def create_hourly_metrics() -> Dict[str, Any]:
    """Create operational hourly metrics."""
    print("⏰ Creating Hourly Metrics...")
    
    source_path = SILVER_PATH / "app_events" / "data.parquet"
    target_path = GOLD_PATH / "hourly_metrics"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Silver
        df = pd.read_parquet(source_path)
        df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
        
        # Hourly metrics
        hourly = df.groupby(pd.Grouper(key='event_timestamp', freq='1h')).agg({
            'user_id': 'nunique',
            'event_id': 'count',
            'is_valid': lambda x: (~x).sum()  # Count of invalid records
        }).reset_index()
        
        hourly.columns = ['metric_hour', 'concurrent_users', 'event_count', 'error_count']
        hourly['metric_date'] = hourly['metric_hour'].dt.date
        
        # Operational metrics
        hourly['events_per_user'] = (hourly['event_count'] / hourly['concurrent_users']).round(2)
        hourly['error_rate_pct'] = (hourly['error_count'] / hourly['event_count'] * 100).round(2)
        hourly['health_status'] = hourly['error_rate_pct'].apply(
            lambda x: 'Healthy' if x < 5 else ('Degraded' if x < 10 else 'Unhealthy')
        )
        hourly['created_at'] = datetime.now()
        
        print(f"  ✓ Created {len(hourly):,} hourly records")
        print(f"  ✓ Avg events/hour: {hourly['event_count'].mean():.0f}")
        print(f"  ✓ Avg error rate: {hourly['error_rate_pct'].mean():.2f}%")
        
        # Write to Gold
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        hourly.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}\n")
        
        return {
            "status": "success",
            "table": "hourly_metrics_gold",
            "records": len(hourly),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def main():
    """Main aggregation orchestration."""
    results = []
    
    print(f"📁 Silver Input: {SILVER_PATH}/")
    print(f"📁 Gold Output:  {GOLD_PATH}/\n")
    
    # Run all aggregations
    results.append(aggregate_event_metrics())
    results.append(create_user_segments())
    results.append(create_daily_summary())
    results.append(create_hourly_metrics())
    
    # Summary
    print("="*80)
    print("✅ GOLD LAYER AGGREGATION COMPLETE")
    print("="*80)
    print(f"\n📊 Results Summary:")
    
    total_records = 0
    successful = 0
    
    for result in results:
        status = result.get("status", "unknown")
        records = result.get("records", 0)
        table = result.get("table", "unknown")
        
        if status == "success":
            print(f"  ✓ {table}: {records:,} records")
            total_records += records
            successful += 1
        elif status == "skipped":
            print(f"  ⊘ {table}: skipped")
        else:
            print(f"  ✗ {table}: failed")
    
    print(f"\n📈 Statistics:")
    print(f"  • Total Gold records: {total_records:,}")
    print(f"  • Successful aggregations: {successful}\n")
    
    # Save report
    report_path = LOGS_DIR / f"gold_aggregation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {"total_records": total_records, "successful": successful}
        }, f, indent=2, default=str)
    
    print(f"📄 Report saved: {report_path}\n")
    
    return 0 if successful == 4 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
