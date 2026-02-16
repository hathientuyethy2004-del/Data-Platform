#!/usr/bin/env python3
"""
Simplified Bronze Layer Ingestion using Python DataFrame libraries
Reads Parquet files from processing layer and writes to Delta Lake
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import pyarrow.dataset as ds

# Setup paths
WORKSPACE_BASE = Path("/workspaces/Data-Platform")
PROCESSING_OUTPUT_BASE = WORKSPACE_BASE / "processing_layer" / "outputs"
LAKEHOUSE_BASE = Path(os.getenv("LAKEHOUSE_BASE_PATH", WORKSPACE_BASE / "lakehouse_data"))
BRONZE_PATH = Path(os.getenv("BRONZE_PATH", LAKEHOUSE_BASE / "bronze"))
LOGS_DIR = Path(os.getenv("LOGS_DIR", LAKEHOUSE_BASE / "logs"))

# Create directories
BRONZE_PATH.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "="*80)
print("🥉 BRONZE LAYER INGESTION JOB (SIMPLIFIED)")
print("="*80 + "\n")

def ingest_app_events() -> Dict[str, Any]:
    """Ingest app events from processing layer."""
    print("📥 Ingesting App Events...")
    
    source_path = PROCESSING_OUTPUT_BASE / "events_aggregated_realtime" / "data.parquet"
    target_path = BRONZE_PATH / "app_events"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source file not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Parquet file
        df = pd.read_parquet(source_path)
        print(f"  ✓ Read {len(df):,} records from {source_path.name}")
        
        # Add load timestamp
        df['load_timestamp'] = datetime.now()
        
        # Simple quality checks
        null_counts = df.isnull().sum()
        print(f"  ✓ Null values check:")
        for col, count in null_counts.items():
            if count > 0:
                pct = (count / len(df)) * 100
                print(f"    • {col}: {count} ({pct:.2f}%)")
        
        # Write to Parquet (Delta-style)
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        df.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}")
        print(f"  ✓ Compression: snappy")
        print(f"  ✓ Total records: {len(df):,}\n")
        
        return {
            "status": "success",
            "table": "app_events_bronze",
            "records": len(df),
            "source": str(source_path),
            "target": str(target_path),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def ingest_clickstream() -> Dict[str, Any]:
    """Ingest clickstream from processing layer."""
    print("📥 Ingesting Clickstream Data...")
    
    source_path = PROCESSING_OUTPUT_BASE / "clickstream_sessions" / "data.parquet"
    target_path = BRONZE_PATH / "clickstream"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source file not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Parquet file
        df = pd.read_parquet(source_path)
        print(f"  ✓ Read {len(df):,} records from {source_path.name}")
        
        # Add load timestamp
        df['load_timestamp'] = datetime.now()
        
        # Quality checks
        null_counts = df.isnull().sum()
        print(f"  ✓ Null values check:")
        for col, count in null_counts.items():
            if count > 0:
                pct = (count / len(df)) * 100
                print(f"    • {col}: {count} ({pct:.2f}%)")
        
        # Write to Parquet
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        df.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}")
        print(f"  ✓ Compression: snappy")
        print(f"  ✓ Total records: {len(df):,}\n")
        
        return {
            "status": "success",
            "table": "clickstream_bronze",
            "records": len(df),
            "source": str(source_path),
            "target": str(target_path),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def ingest_cdc() -> Dict[str, Any]:
    """Ingest CDC changes from processing layer."""
    print("📥 Ingesting CDC Data...")
    
    source_path = PROCESSING_OUTPUT_BASE / "cdc_transformed" / "data.parquet"
    target_path = BRONZE_PATH / "cdc_changes"
    
    try:
        if not source_path.exists():
            print(f"  ⚠️  Source file not found: {source_path}")
            return {"status": "skipped", "records": 0}
        
        # Read Parquet file
        df = pd.read_parquet(source_path)
        print(f"  ✓ Read {len(df):,} records from {source_path.name}")
        
        # Add load timestamp
        df['load_timestamp'] = datetime.now()
        
        # Quality checks
        null_counts = df.isnull().sum()
        print(f"  ✓ Null values check:")
        for col, count in null_counts.items():
            if count > 0:
                pct = (count / len(df)) * 100
                print(f"    • {col}: {count} ({pct:.2f}%)")
        
        # Write to Parquet
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "data.parquet"
        df.to_parquet(output_file, index=False, compression="snappy")
        
        print(f"  ✓ Written to {target_path}")
        print(f"  ✓ Compression: snappy")
        print(f"  ✓ Total records: {len(df):,}\n")
        
        return {
            "status": "success",
            "table": "cdc_changes_bronze",
            "records": len(df),
            "source": str(source_path),
            "target": str(target_path),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return {"status": "failed", "error": str(e)}

def main():
    """Main ingestion orchestration."""
    results = []
    
    print(f"📁 Processing Input:  {PROCESSING_OUTPUT_BASE}/")
    print(f"📁 Lakehouse Output:  {BRONZE_PATH}/\n")
    
    # Run all ingestions
    results.append(ingest_app_events())
    results.append(ingest_clickstream())
    results.append(ingest_cdc())
    
    # Summary
    print("="*80)
    print("✅ BRONZE LAYER INGESTION COMPLETE")
    print("="*80)
    print(f"\n📊 Results Summary:")
    
    total_records = 0
    successful = 0
    failed = 0
    
    for result in results:
        status = result.get("status", "unknown")
        records = result.get("records", 0)
        table = result.get("table", "unknown")
        
        if status == "success":
            print(f"  ✓ {table}: {records:,} records ingested")
            total_records += records
            successful += 1
        elif status == "skipped":
            print(f"  ⊘ {table}: skipped (source not found)")
        else:
            print(f"  ✗ {table}: failed")
            failed += 1
    
    print(f"\n📈 Statistics:")
    print(f"  • Total records ingested: {total_records:,}")
    print(f"  • Successful tables: {successful}")
    print(f"  • Failed tables: {failed}\n")
    
    # Save ingestion report
    report_path = LOGS_DIR / f"bronze_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total_records": total_records,
                "successful": successful,
                "failed": failed
            }
        }, f, indent=2, default=str)
    
    print(f"📄 Report saved: {report_path}\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
