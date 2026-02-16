"""
Lakehouse API Server
REST API for querying and managing lakehouse data
"""

import json
from datetime import datetime
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pyspark.sql import SparkSession

from configs.lakehouse_config import lakehouse_config
from configs.logging_config import setup_logging
from utils.delta_utils import DeltaLakeManager
from catalog.data_catalog import get_catalog


logger = setup_logging(__name__, lakehouse_config.log_level)


# FastAPI app
app = FastAPI(
    title='Lakehouse API',
    description='REST API for lakehouse queries and metadata operations',
    version='1.0.0',
)

# Global Spark session
spark = None
delta_manager = None
catalog = None


def init_spark():
    """Initialize Spark session"""
    global spark, delta_manager, catalog
    
    spark = SparkSession.builder \
        .appName('lakehouse-api') \
        .master(lakehouse_config.spark_master) \
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') \
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') \
        .getOrCreate()
    
    delta_manager = DeltaLakeManager(spark)
    catalog = get_catalog()
    
    logger.info("✅ Spark session initialized")


# Startup hook
@app.on_event('startup')
async def startup_event():
    """Initialize on startup"""
    init_spark()
    logger.info("✅ Lakehouse API started")


@app.on_event('shutdown')
async def shutdown_event():
    """Cleanup on shutdown"""
    if spark:
        spark.stop()
    logger.info("✅ Lakehouse API stopped")


# ============================================================================
# Models
# ============================================================================

class QueryRequest(BaseModel):
    """SQL query request"""
    sql: str
    limit: int = 1000


class TableInfo(BaseModel):
    """Table information"""
    name: str
    layer: str
    path: str
    records: int
    size_mb: float


# ============================================================================
# Endpoints
# ============================================================================

@app.get('/health')
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}


@app.post('/query')
async def execute_query(request: QueryRequest) -> Dict[str, Any]:
    """
    Execute SQL query against lakehouse tables
    
    Args:
        request: SQL query request
    
    Returns:
        Query results
    """
    try:
        logger.info(f"🔍 Executing query: {request.sql[:100]}")
        
        df = spark.sql(request.sql)
        
        # Limit results
        rows = df.limit(request.limit).collect()
        columns = df.columns
        
        results = [dict(row) for row in rows]
        
        return {
            'status': 'success',
            'record_count': len(results),
            'columns': columns,
            'data': results,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/tables')
async def list_tables(layer: str = Query(None, description='Filter by layer')) -> Dict[str, Any]:
    """
    List lakehouse tables
    
    Args:
        layer: Optional layer filter (bronze, silver, gold)
    
    Returns:
        List of tables
    """
    try:
        if layer:
            tables = catalog.get_layer_tables(layer)
        else:
            tables = list(catalog.tables.values())
        
        table_info = [
            {
                'name': t.table_name,
                'layer': t.layer,
                'path': t.path,
                'records': t.record_count,
                'size_mb': t.size_bytes / (1024**2),
                'owner': t.owner,
                'description': t.description,
                'updated': t.last_updated_timestamp,
            }
            for t in tables
        ]
        
        return {
            'status': 'success',
            'count': len(table_info),
            'tables': table_info,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/tables/{table_name}')
async def get_table_metadata(table_name: str) -> Dict[str, Any]:
    """Get metadata for a specific table"""
    try:
        metadata = catalog.get_table_metadata(table_name)
        
        if metadata is None:
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
        
        lineage = catalog.get_table_lineage(table_name)
        
        return {
            'status': 'success',
            'metadata': {
                'name': metadata.table_name,
                'layer': metadata.layer,
                'path': metadata.path,
                'records': metadata.record_count,
                'size_mb': metadata.size_bytes / (1024**2),
                'owner': metadata.owner,
                'description': metadata.description,
                'created': metadata.created_timestamp,
                'updated': metadata.last_updated_timestamp,
                'retention_days': metadata.retention_days,
                'tags': metadata.tags,
            },
            'lineage': lineage,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get table metadata: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/tables/{table_name}/preview')
async def preview_table(table_name: str, limit: int = Query(10, le=100)) -> Dict[str, Any]:
    """Get preview of table data"""
    try:
        # Read table
        df = spark.read.format('delta').option('path', f"/var/lib/lakehouse/*/{table_name}").load()
        
        rows = df.limit(limit).collect()
        columns = df.columns
        
        results = [dict(row) for row in rows]
        
        return {
            'status': 'success',
            'table': table_name,
            'columns': columns,
            'record_count': len(results),
            'data': results,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Failed to preview table: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/catalog')
async def get_catalog_info() -> Dict[str, Any]:
    """Get overall catalog information"""
    try:
        report = catalog.get_catalog_report()
        
        return {
            'status': 'success',
            'report': report,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Failed to get catalog info: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/catalog/lineage/{table_name}')
async def get_table_lineage(table_name: str) -> Dict[str, Any]:
    """Get data lineage for a table"""
    try:
        lineage = catalog.get_table_lineage(table_name)
        
        return {
            'status': 'success',
            'table': table_name,
            'lineage': lineage,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Failed to get lineage: {e}")
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8888,
        log_level='info',
    )
