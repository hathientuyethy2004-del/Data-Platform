#!/bin/bash
# Data Platform - Implementation Verification Script
# Checks that all components are correctly implemented

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║       DATA PLATFORM - DATA SOURCES LAYER VERIFICATION              ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

BASE_DIR="/workspaces/Data-Platform/simulations"
SUCCESS_COUNT=0
FAIL_COUNT=0

# Helper function
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo "✅ $description"
        ((SUCCESS_COUNT++))
    else
        echo "❌ MISSING: $description ($file)"
        ((FAIL_COUNT++))
    fi
}

check_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo "✅ $description"
        ((SUCCESS_COUNT++))
    else
        echo "❌ MISSING: $description ($dir)"
        ((FAIL_COUNT++))
    fi
}

echo "🔍 Checking Directory Structure..."
echo "─────────────────────────────────────"
check_dir "$BASE_DIR/apps/api" "FastAPI API Gateway directory"
check_dir "$BASE_DIR/apps/mobile" "Mobile Simulator directory"
check_dir "$BASE_DIR/apps/web" "Web Simulator directory"
check_dir "$BASE_DIR/kafka" "Kafka configuration directory"
check_dir "$BASE_DIR/schema_registry" "Schema Registry directory"
check_dir "$BASE_DIR/postgres_cdc" "PostgreSQL CDC directory"
check_dir "$BASE_DIR/spark_streaming" "Spark Streaming directory"
check_dir "$BASE_DIR/airflow/dags" "Airflow DAGs directory"
check_dir "$BASE_DIR/clickstream" "Clickstream Simulator directory"
check_dir "$BASE_DIR/external_data" "External Data Simulator directory"
echo ""

echo "🔍 Checking Application Layer Files..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/apps/api/main.py" "FastAPI main application"
check_file "$BASE_DIR/apps/api/Dockerfile" "FastAPI Dockerfile"
check_file "$BASE_DIR/apps/api/requirements.txt" "FastAPI requirements"
check_file "$BASE_DIR/apps/mobile/simulator.py" "Mobile app simulator"
check_file "$BASE_DIR/apps/mobile/Dockerfile" "Mobile simulator Dockerfile"
check_file "$BASE_DIR/apps/mobile/requirements.txt" "Mobile simulator requirements"
check_file "$BASE_DIR/apps/web/simulator.py" "Web app simulator"
check_file "$BASE_DIR/apps/web/Dockerfile" "Web simulator Dockerfile"
check_file "$BASE_DIR/apps/web/requirements.txt" "Web simulator requirements"
echo ""

echo "🔍 Checking CDC Layer Files..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/postgres_cdc/simulator.py" "CDC simulator"
check_file "$BASE_DIR/postgres_cdc/init.sql" "PostgreSQL initialization script"
check_file "$BASE_DIR/postgres_cdc/Dockerfile" "CDC simulator Dockerfile"
check_file "$BASE_DIR/postgres_cdc/requirements.txt" "CDC simulator requirements"
echo ""

echo "🔍 Checking Streaming Layer Files..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/spark_streaming/streaming_jobs.py" "Spark streaming jobs"
check_file "$BASE_DIR/spark_streaming/requirements.txt" "Spark requirements"
check_file "$BASE_DIR/clickstream/simulator.py" "Clickstream simulator"
check_file "$BASE_DIR/clickstream/requirements.txt" "Clickstream requirements"
echo ""

echo "🔍 Checking External Data Layer Files..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/airflow/dags/weather_data_ingestion.py" "Weather API DAG"
check_file "$BASE_DIR/airflow/dags/maps_data_ingestion.py" "Maps API DAG"
check_file "$BASE_DIR/airflow/dags/config_driven_pipeline.py" "Config-driven DAG"
check_file "$BASE_DIR/external_data/simulator.py" "External data simulator"
check_file "$BASE_DIR/external_data/requirements.txt" "External data requirements"
check_file "$BASE_DIR/airflow/.env" "Airflow environment config"
echo ""

echo "🔍 Checking Schema Registry Files..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/schema_registry/AppEvent.avsc" "AppEvent Avro schema"
check_file "$BASE_DIR/schema_registry/CDCChange.avsc" "CDCChange Avro schema"
check_file "$BASE_DIR/schema_registry/Clickstream.avsc" "Clickstream Avro schema"
check_file "$BASE_DIR/schema_registry/AppLog.avsc" "AppLog Avro schema"
echo ""

echo "🔍 Checking Kafka Configuration..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/kafka/config.py" "Kafka topics configuration"
echo ""

echo "🔍 Checking Infrastructure Files..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/docker-compose-production.yml" "Docker Compose main configuration"
echo ""

echo "🔍 Checking Documentation Files..."
echo "─────────────────────────────────────"
check_file "$BASE_DIR/README.md" "Main documentation"
check_file "$BASE_DIR/QUICK_START.md" "Quick start guide"
check_file "$BASE_DIR/ARCHITECTURE.md" "Architecture documentation"
check_file "$BASE_DIR/IMPLEMENTATION_SUMMARY.md" "Implementation summary"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                      VERIFICATION RESULTS                          ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Verified: $SUCCESS_COUNT files/directories"
echo "❌ Missing: $FAIL_COUNT files/directories"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 All components successfully implemented!"
    echo ""
    echo "📊 Implementation Statistics:"
    echo "   - Total lines of code: $(wc -l "$BASE_DIR"/{*.py,*.md,*.yml,**/*.py,**/*.sql,**/*.avsc} 2>/dev/null | tail -1 | awk '{print $1}')"
    echo "   - Python files: $(find "$BASE_DIR" -name "*.py" | wc -l)"
    echo "   - Documentation files: $(find "$BASE_DIR" -name "*.md" | wc -l)"
    echo "   - Configuration files: $(find "$BASE_DIR" -name "*.yml" -o -name "*.yaml" -o -name ".env" | wc -l)"
    echo "   - Schema files: $(find "$BASE_DIR" -name "*.avsc" | wc -l)"
    echo "   - SQL scripts: $(find "$BASE_DIR" -name "*.sql" | wc -l)"
    echo ""
    echo "🚀 Ready to start! Run:"
    echo "   cd $BASE_DIR"
    echo "   docker-compose -f docker-compose-production.yml up -d"
    echo ""
    echo "✨ Then monitor at:"
    echo "   - Kafka UI: http://localhost:8080"
    echo "   - Airflow: http://localhost:8888"
    echo "   - Spark: http://localhost:8181"
    echo "   - API Docs: http://localhost:8000/docs"
    exit 0
else
    echo "⚠️  Warning: Some components are missing. Please check the above output."
    exit 1
fi
