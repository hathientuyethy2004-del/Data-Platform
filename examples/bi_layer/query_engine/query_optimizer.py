"""
Query Optimizer - SQL Query Optimization and Execution Planning

Provides:
- Query parsing and analysis
- Execution plan optimization
- Query caching
- Performance metrics
- Cost-based optimization
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class QueryPlan:
    """Represents a query execution plan"""
    query_id: str
    original_query: str
    optimized_query: str
    estimated_cost: float
    estimated_rows: int
    steps: List[Dict[str, Any]] = field(default_factory=list)
    index_suggestions: List[str] = field(default_factory=list)


@dataclass
class QueryExecution:
    """Record of query execution"""
    query_id: str
    query: str
    execution_time_ms: float
    rows_returned: int
    status: str  # success, failed, cached
    executed_at: str
    error_message: str = ""
    cache_hit: bool = False


class QueryOptimizer:
    """Optimizes and executes analytical queries"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Query Optimizer
        
        Args:
            config_path: Path to configuration file
        """
        from ..configs.bi_config import get_bi_config
        self.config = get_bi_config(config_path)
        self.storage_path = Path(self.config.get('query.storage', 'analytics_data/queries'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.query_cache: Dict[str, Tuple[str, datetime]] = {}  # query_hash -> (result, timestamp)
        self.execution_history: List[QueryExecution] = []
        self.cache_ttl = self.config.get('query.cache_ttl', 3600)  # seconds
        
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load query cache from storage"""
        cache_file = self.storage_path / 'query_cache.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    for query_hash, (result, timestamp_str) in data.items():
                        timestamp = datetime.fromisoformat(timestamp_str)
                        self.query_cache[query_hash] = (result, timestamp)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self) -> None:
        """Save query cache to storage"""
        cache_file = self.storage_path / 'query_cache.json'
        # Convert datetime to string for JSON serialization
        cache_data = {
            k: (v[0], v[1].isoformat())
            for k, v in self.query_cache.items()
        }
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse and analyze a SQL query
        
        Args:
            query: SQL query string
        
        Returns:
            Query analysis dictionary
        """
        query_upper = query.upper().strip()
        
        analysis = {
            'query_length': len(query),
            'is_select': query_upper.startswith('SELECT'),
            'is_aggregate': any(agg in query_upper for agg in ['SUM(', 'AVG(', 'COUNT(', 'MAX(', 'MIN(']),
            'has_join': 'JOIN' in query_upper,
            'has_subquery': query_upper.count('SELECT') > 1,
            'has_group_by': 'GROUP BY' in query_upper,
            'has_order_by': 'ORDER BY' in query_upper,
            'tables_referenced': self._extract_tables(query),
            'columns_referenced': self._extract_columns(query)
        }
        
        return analysis
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query"""
        # Simple extraction - in production use SQL parser
        tables = []
        query_upper = query.upper()
        
        keywords = ['FROM', 'JOIN', 'INTO', 'UPDATE']
        for keyword in keywords:
            if keyword in query_upper:
                idx = query_upper.find(keyword)
                # Get next word(s) after keyword
                start = idx + len(keyword)
                remaining = query[start:].strip()
                # Take first word (table name)
                table = remaining.split()[0].rstrip('(').rstrip(',')
                if table and table not in ['WHERE', 'ON', 'AND', 'OR', 'ORDER', 'GROUP', 'HAVING']:
                    tables.append(table)
        
        return list(set(tables))
    
    def _extract_columns(self, query: str) -> List[str]:
        """Extract column names from query"""
        # Simple extraction - in production use SQL parser
        columns = []
        
        # Find SELECT clause
        select_idx = query.upper().find('SELECT')
        if select_idx >= 0:
            from_idx = query.upper().find('FROM', select_idx)
            if from_idx < 0:
                from_idx = len(query)
            
            select_clause = query[select_idx + 6:from_idx]
            
            # Split by comma but respect parentheses
            cols = select_clause.split(',')
            for col in cols:
                col = col.strip()
                if col != '*':
                    columns.append(col)
        
        return columns
    
    def optimize_query(self, query: str) -> QueryPlan:
        """Optimize a SQL query
        
        Args:
            query: SQL query string
        
        Returns:
            QueryPlan with optimization suggestions
        """
        analysis = self.parse_query(query)
        
        query_id = hashlib.md5(query.encode()).hexdigest()
        optimized_query = query  # In production, apply optimizations
        
        suggestions = []
        estimated_cost = 1.0
        
        # Generate optimization suggestions
        if analysis['has_join'] and not analysis['has_group_by']:
            suggestions.append("Consider adding GROUP BY for aggregation")
        
        if analysis['has_subquery'] and analysis['is_aggregate']:
            suggestions.append("Consider using window functions instead of subqueries")
            estimated_cost *= 1.5
        
        if not analysis['has_group_by'] and analysis['is_aggregate']:
            estimated_cost *= 0.8
        
        if analysis['has_order_by']:
            suggestions.append("LIMIT clause may improve performance")
        
        plan = QueryPlan(
            query_id=query_id,
            original_query=query,
            optimized_query=optimized_query,
            estimated_cost=estimated_cost,
            estimated_rows=1000,  # Placeholder
            steps=[
                {"step": 1, "description": "Parse query", "estimated_time_ms": 10},
                {"step": 2, "description": "Optimize plan", "estimated_time_ms": 50},
                {"step": 3, "description": "Execute query", "estimated_time_ms": 100}
            ],
            index_suggestions=suggestions
        )
        
        return plan
    
    def execute_query(self, query: str, use_cache: bool = True) -> Tuple[str, QueryExecution]:
        """Execute a query with optional caching
        
        Args:
            query: SQL query string
            use_cache: Whether to use cached results
        
        Returns:
            Tuple of (result, execution_record)
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()
        execution_id = f"query_{datetime.now().timestamp()}"
        
        # Check cache
        if use_cache and query_hash in self.query_cache:
            cached_result, timestamp = self.query_cache[query_hash]
            age = (datetime.now() - timestamp).total_seconds()
            
            if age < self.cache_ttl:
                execution = QueryExecution(
                    query_id=execution_id,
                    query=query,
                    execution_time_ms=0.1,
                    rows_returned=0,
                    status="cached",
                    executed_at=datetime.now().isoformat(),
                    cache_hit=True
                )
                self.execution_history.append(execution)
                logger.info(f"Query cache hit: {query_hash}")
                return cached_result, execution
        
        # Execute query (simulated)
        start = datetime.now()
        
        try:
            # Placeholder execution - in production this connects to actual DB
            result = self._simulate_query_execution(query)
            
            execution_time = (datetime.now() - start).total_seconds() * 1000
            
            execution = QueryExecution(
                query_id=execution_id,
                query=query,
                execution_time_ms=execution_time,
                rows_returned=100,
                status="success",
                executed_at=datetime.now().isoformat()
            )
            
            # Cache result
            self.query_cache[query_hash] = (result, datetime.now())
            
            logger.info(f"Query executed in {execution_time:.2f}ms")
            
        except Exception as e:
            execution_time = (datetime.now() - start).total_seconds() * 1000
            execution = QueryExecution(
                query_id=execution_id,
                query=query,
                execution_time_ms=execution_time,
                rows_returned=0,
                status="failed",
                executed_at=datetime.now().isoformat(),
                error_message=str(e)
            )
            result = ""
            logger.error(f"Query execution failed: {e}")
        
        self.execution_history.append(execution)
        self._save_cache()
        
        return result, execution
    
    def _simulate_query_execution(self, query: str) -> str:
        """Simulate query execution (placeholder)"""
        return json.dumps({
            "query": query,
            "rows": 100,
            "columns": ["col1", "col2"],
            "data": []
        })
    
    def clear_cache(self) -> int:
        """Clear query cache and return number of cleared entries"""
        count = len(self.query_cache)
        self.query_cache.clear()
        self._save_cache()
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query execution statistics"""
        if not self.execution_history:
            return {"status": "no_queries"}
        
        successful = [e for e in self.execution_history if e.status == "success"]
        failed = [e for e in self.execution_history if e.status == "failed"]
        cached = [e for e in self.execution_history if e.cache_hit]
        
        if successful:
            avg_time = sum(e.execution_time_ms for e in successful) / len(successful)
        else:
            avg_time = 0
        
        return {
            'total_queries': len(self.execution_history),
            'successful': len(successful),
            'failed': len(failed),
            'cached_hits': len(cached),
            'average_execution_time_ms': avg_time,
            'cache_size': len(self.query_cache),
            'cache_ttl_seconds': self.cache_ttl
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of query optimizer"""
        stats = self.get_query_statistics()
        return {
            'status': 'healthy',
            'cache_entries': len(self.query_cache),
            'total_executions': len(self.execution_history),
            'storage_path': str(self.storage_path),
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        }


def get_query_optimizer(config_path: Optional[str] = None) -> QueryOptimizer:
    """Factory function to get QueryOptimizer instance"""
    return QueryOptimizer(config_path)
