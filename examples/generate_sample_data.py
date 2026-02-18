#!/usr/bin/env python3
"""
Generate sample data for lakehouse ingestion using Pandas and Parquet.
This mimics what the processing layer would output.
"""

from datetime import datetime, timedelta
import random
import json
from pathlib import Path
import pandas as pd

def generate_app_events(num_records=1500):
    """Generate sample app events data."""
    print("  Generating app events data...")
    
    event_types = ["app_open", "page_view", "click", "scroll", "share", "purchase"]
    app_types = ["ios", "android", "web"]
    base_time = datetime.now() - timedelta(days=1)
    
    data = {
        "event_id": [f"evt_{i:06d}" for i in range(num_records)],
        "user_id": [f"user_{random.randint(1, 500):04d}" for _ in range(num_records)],
        "event_type": [random.choice(event_types) for _ in range(num_records)],
        "app_type": [random.choice(app_types) for _ in range(num_records)],
        "event_timestamp": [base_time + timedelta(minutes=random.randint(0, 1440)) for _ in range(num_records)],
        "properties": [json.dumps({
            "session_id": f"session_{random.randint(1, 100):03d}",
            "page_name": random.choice(["home", "profile", "feed", "settings"]),
            "value": round(random.uniform(0, 100), 2),
            "duration_ms": random.randint(100, 5000)
        }) for _ in range(num_records)],
        "device_info": [json.dumps({
            "device_type": random.choice(["phone", "tablet", "desktop"]),
            "os": random.choice(["iOS", "Android", "Windows", "MacOS"]),
            "app_version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.0"
        }) for _ in range(num_records)]
    }
    
    return pd.DataFrame(data)

def generate_clickstream(num_records=800):
    """Generate sample clickstream session data."""
    print("  Generating clickstream data...")
    
    pages = ["home", "products", "product_detail", "cart", "checkout", "thank_you"]
    base_time = datetime.now() - timedelta(days=1)
    
    data = {
        "click_id": [f"click_{i:06d}" for i in range(num_records)],
        "session_id": [f"session_{i:06d}" for i in range(num_records)],
        "user_id": [f"user_{random.randint(1, 500):04d}" for _ in range(num_records)],
        "page_name": [random.choice(pages) for _ in range(num_records)],
        "event_timestamp": [base_time + timedelta(minutes=random.randint(0, 1440)) for _ in range(num_records)],
        "session_duration_sec": [random.randint(30, 3600) for _ in range(num_records)],
        "page_views": [random.randint(2, 8) for _ in range(num_records)],
        "click_count": [random.randint(1, 20) for _ in range(num_records)],
        "scroll_depth": [round(random.uniform(0, 1), 2) for _ in range(num_records)],
        "page_sequence": [",".join([random.choice(pages) for _ in range(random.randint(2, 8))]) for _ in range(num_records)]
    }
    
    return pd.DataFrame(data)

def generate_cdc(num_records=300):
    """Generate sample CDC (Change Data Capture) data."""
    print("  Generating CDC data...")
    
    operations = ["INSERT", "UPDATE", "DELETE"]
    table_names = ["users", "orders", "products", "reviews"]
    base_time = datetime.now() - timedelta(days=1)
    
    data = {
        "cdc_id": [f"cdc_{i:06d}" for i in range(num_records)],
        "table_name": [random.choice(table_names) for _ in range(num_records)],
        "operation_type": [random.choice(operations) for _ in range(num_records)],
        "before_values": [json.dumps({"id": i, "value": f"old_{i}"}) if random.random() > 0.3 else None for i in range(num_records)],
        "after_values": [json.dumps({"id": i, "value": f"new_{i}", "processed": True}) if random.random() > 0.2 else None for i in range(num_records)],
        "cdc_timestamp": [base_time + timedelta(minutes=random.randint(0, 1440)) for _ in range(num_records)],
        "source_system": ["production_db" for _ in range(num_records)]
    }
    
    return pd.DataFrame(data)

def write_parquet(df, output_dir, name):
    """Write DataFrame to Parquet format."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    parquet_path = output_dir / "data.parquet"
    df.to_parquet(parquet_path, engine="pyarrow", index=False)
    
    record_count = len(df)
    print(f"  ✓ {name}: {record_count:,} records")
    return record_count

def main():
    print("\n" + "="*80)
    print("📊 SAMPLE DATA GENERATOR FOR LAKEHOUSE INGESTION")
    print("="*80 + "\n")
    
    output_base = Path("/workspaces/Data-Platform/processing_layer/outputs")
    output_base.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output location: {output_base}\n")
    print("📝 Generating sample data...\n")
    
    # Generate data
    print("1️⃣  App Events Data:")
    app_events_df = generate_app_events(num_records=1500)
    app_count = write_parquet(app_events_df, output_base / "events_aggregated_realtime", "App Events")
    
    print("\n2️⃣  Clickstream Data:")
    clickstream_df = generate_clickstream(num_records=800)
    click_count = write_parquet(clickstream_df, output_base / "clickstream_sessions", "Clickstream")
    
    print("\n3️⃣  CDC Data:")
    cdc_df = generate_cdc(num_records=300)
    cdc_count = write_parquet(cdc_df, output_base / "cdc_transformed", "CDC")
    
    # Summary
    print("\n" + "="*80)
    print("✅ SAMPLE DATA GENERATION COMPLETE")
    print("="*80)
    print(f"\n📊 Total Records Generated:")
    print(f"   • App Events:     {app_count:,} records")
    print(f"   • Clickstream:    {click_count:,} records")
    print(f"   • CDC Changes:    {cdc_count:,} records")
    print(f"   • TOTAL:          {sum([app_count, click_count, cdc_count]):,} records\n")
    print(f"📁 Files available in: {output_base}/")
    print("   ├─ events_aggregated_realtime/data.parquet")
    print("   ├─ clickstream_sessions/data.parquet")
    print("   └─ cdc_transformed/data.parquet\n")
    print("🚀 Ready for lakehouse ingestion!\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
