#!/usr/bin/env python3
"""
Simplified Silver Layer Transformation using Pandas
Reads Bronze layers and creates cleaned, deduplicated Silver layer
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
BRONZE_PATH = Path(os.getenv("BRONZE_PATH", LAKEHOUSE_BASE / "bronze"))
SILVER_PATH = Path(os.getenv("SILVER_PATH", LAKEHOUSE_BASE / "silver"))
LOGS_DIR = Path(os.getenv("LOGS_DIR", LAKEHOUSE_BASE / "logs"))

# Create directories
SILVER_PATH.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "="*80)
print("🥈 SILVER LAYER TRANSFORMATION JOB (SIMPLIFIED)")
print("="*80 + "\n")

def transform_app_events() -> Dict[str, Any]:
    """Transform app events - deduplication and validation."""
    print("🔄 Transforming App Events...")
    
    source_path = BRONZE_PATH / "app_events" / "data.parquet"
    target_path = SILVER_PATH / "app_events"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Bronze
        df = pd.read_parquet(source_path)
        print(f"  ✓ Read {len(df):,} records from Bronze")
        
        # Extract date/hour from timestamp
        df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
        df['event_date'] = df['event_timestamp'].dt.date
        df['event_hour'] = df['event_timestamp'].dt.hour
        
        # Deduplication by event_id (keep latest)
        initial_count = len(df)
        df = df.sort_values('event_timestamp').drop_duplicates(subset=['event_id'], keep='last')
        dedup_count = initial_count - len(df)
        print(f"  ✓ Deduplicated {dedup_count} duplicate records")
        
        # Validation: mark invalid records
        df['is_valid'] = True
        df.loc[df['event_id'].isnull(), 'is_valid'] = False
        df.loc[df['user_id'].isnull(), 'is_valid'] = False
        
        invalid_count = (~df['is_valid']).sum()
        print(f"  ✓ Flagged {invalid_count} invalid records")
        
        # Add quality checks metadata
        df['quality_checks'] = df.apply(lambda row: json.dumps({
            "null_fields": sum([row[col] is None or pd.isna(row[col]) for col in ['event_id', 'user_id', 'event_type']]),
            "validated_at": datetime.now().isoformat()
        }), axis=1)
        
        df['transformed_timestamp'] = datetime.now()
        
        # Write to Silver
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        df.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}")
        print(f"  ✓ Final records: {len(df):,}\n")
        
        return {
            "status": "success",
            "table": "app_events_silver",
            "records": len(df),
            "deduped": dedup_count,
            "invalid": invalid_count,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def transform_clickstream() -> Dict[str, Any]:
    """Transform clickstream - session-level aggregation."""
    print("🔄 Transforming Clickstream...")
    
    source_path = BRONZE_PATH / "clickstream" / "data.parquet"
    target_path = SILVER_PATH / "clickstream"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Bronze
        df = pd.read_parquet(source_path)
        print(f"  ✓ Read {len(df):,} records from Bronze")
        
        # Convert timestamp
        df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
        
        # Group by session and aggregate
        session_data = df.groupby('session_id').agg({
            'user_id': 'first',
            'event_timestamp': ['min', 'max', 'count'],
            'page_sequence': lambda x: '->'.join(x.astype(str)),
            'page_views': 'sum',
            'click_count': 'sum',
            'scroll_depth': 'mean'
        }).reset_index()
        
        # Flatten column names
        session_data.columns = ['session_id', 'user_id', 'session_start', 'session_end', 
                               'event_count', 'page_sequence', 'total_page_views', 
                               'total_clicks', 'avg_scroll_depth']
        
        # Calculate session duration
        session_data['session_duration_sec'] = (
            (session_data['session_end'] - session_data['session_start']).dt.total_seconds()
        ).astype(int)
        
        session_data['transformed_timestamp'] = datetime.now()
        
        print(f"  ✓ Aggregated to {len(session_data):,} sessions")
        
        # Write to Silver
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        session_data.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}\n")
        
        return {
            "status": "success",
            "table": "clickstream_silver",
            "records": len(session_data),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def build_users_dimension() -> Dict[str, Any]:
    """Build user dimension from app events."""
    print("🔄 Building Users Dimension...")
    
    source_path = BRONZE_PATH / "app_events" / "data.parquet"
    target_path = SILVER_PATH / "users"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Bronze
        df = pd.read_parquet(source_path)
        df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
        
        # Aggregate by user
        users = df.groupby('user_id').agg({
            'event_timestamp': ['min', 'max', 'count'],
            'event_type': lambda x: x.nunique(),
            'event_id': 'count'
        }).reset_index()
        
        # Flatten columns
        users.columns = ['user_id', 'first_seen', 'last_seen', 'total_sessions',
                        'event_types_count', 'total_events']
        
        # Add engagement metrics
        users['is_active'] = users['last_seen'] > (pd.Timestamp.now() - pd.Timedelta(days=30))
        users['days_since_last_event'] = (
            (pd.Timestamp.now() - users['last_seen']).dt.days
        )
        
        users['created_at'] = datetime.now()
        
        print(f"  ✓ Created dimension for {len(users):,} users")
        print(f"  ✓ Active users (30d): {users['is_active'].sum():,}")
        
        # Write to Silver
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        users.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}\n")
        
        return {
            "status": "success",
            "table": "users_silver",
            "records": len(users),
            "active_users": int(users['is_active'].sum()),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def main():
    """Main transformation orchestration."""
    results = []
    
    print(f"📁 Bronze Input:  {BRONZE_PATH}/")
    print(f"📁 Silver Output: {SILVER_PATH}/\n")
    
    # Run all transformations
    results.append(transform_app_events())
    results.append(transform_clickstream())
    results.append(build_users_dimension())
    
    # Summary
    print("="*80)
    print("✅ SILVER LAYER TRANSFORMATION COMPLETE")
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
    print(f"  • Total records: {total_records:,}")
    print(f"  • Successful transformations: {successful}\n")
    
    # Save report
    report_path = LOGS_DIR / f"silver_transformation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {"total_records": total_records, "successful": successful}
        }, f, indent=2, default=str)
    
    print(f"📄 Report saved: {report_path}\n")
    
    return 0 if successful == 3 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
