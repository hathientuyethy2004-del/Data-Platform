"""
BI Layer REST API

Provides HTTP endpoints for all BI layer operations.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class BIRestAPI:
    """REST API wrapper for BI Layer operations"""
    
    def __init__(self):
        """Initialize REST API"""
        self.routes = {}
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes"""
        self.routes = {
            # Data Mart endpoints
            'POST /api/v1/marts': self.create_data_mart,
            'GET /api/v1/marts': self.list_data_marts,
            'GET /api/v1/marts/{mart_name}': self.get_data_mart,
            'POST /api/v1/dimensions': self.create_dimension,
            'GET /api/v1/dimensions': self.list_dimensions,
            'POST /api/v1/facts': self.create_fact,
            'GET /api/v1/facts': self.list_facts,
            
            # Dashboard endpoints
            'POST /api/v1/dashboards': self.create_dashboard,
            'GET /api/v1/dashboards': self.list_dashboards,
            'GET /api/v1/dashboards/{dashboard_name}': self.get_dashboard,
            'POST /api/v1/dashboards/{dashboard_name}/widgets': self.add_widget,
            
            # Report endpoints
            'POST /api/v1/reports': self.create_report,
            'GET /api/v1/reports': self.list_reports,
            'GET /api/v1/reports/{report_name}': self.get_report,
            'POST /api/v1/reports/{report_name}/generate': self.generate_report,
            
            # Query endpoints
            'POST /api/v1/queries': self.execute_query,
            'GET /api/v1/queries/optimize': self.optimize_query,
            'POST /api/v1/queries/cache/clear': self.clear_query_cache,
            
            # Metadata endpoints
            'POST /api/v1/metadata/assets': self.register_asset,
            'GET /api/v1/metadata/assets': self.search_assets,
            'GET /api/v1/metadata/assets/{asset_id}': self.get_asset,
            
            # Chart endpoints
            'POST /api/v1/charts': self.create_chart,
            'GET /api/v1/charts': self.list_charts,
            'GET /api/v1/charts/{chart_id}': self.get_chart,
            
            # Health check
            'GET /api/v1/health': self.health_check,
        }
    
    async def create_data_mart(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new data mart"""
        try:
            from ..data_mart import get_data_mart_engine
            engine = get_data_mart_engine()
            mart = engine.create_data_mart(
                request['mart_name'],
                request.get('dimensions', []),
                request.get('facts', []),
                request.get('description', '')
            )
            return {'status': 'success', 'data': {'name': mart['name']}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def list_data_marts(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all data marts"""
        try:
            from ..data_mart import get_data_mart_engine
            engine = get_data_mart_engine()
            marts = engine.list_data_marts()
            return {'status': 'success', 'data': {'marts': marts}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def get_data_mart(self, mart_name: str) -> Dict[str, Any]:
        """Get data mart details"""
        try:
            from ..data_mart import get_data_mart_engine
            engine = get_data_mart_engine()
            schema = engine.get_mart_schema(mart_name)
            return {'status': 'success', 'data': schema}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def create_dimension(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dimension"""
        try:
            from ..data_mart import get_data_mart_engine
            engine = get_data_mart_engine()
            dim = engine.create_dimension(
                request['name'],
                request['columns'],
                request['table_name'],
                request.get('description', ''),
                request.get('scd_type', 1)
            )
            return {'status': 'success', 'data': {'name': dim.name}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def list_dimensions(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all dimensions"""
        try:
            from ..data_mart import get_data_mart_engine
            engine = get_data_mart_engine()
            dims = engine.list_dimensions()
            return {'status': 'success', 'data': {'dimensions': dims}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def create_fact(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fact table"""
        try:
            from ..data_mart import get_data_mart_engine
            engine = get_data_mart_engine()
            fact = engine.create_fact(
                request['name'],
                request['columns'],
                request['table_name'],
                request['grain'],
                request.get('description', '')
            )
            return {'status': 'success', 'data': {'name': fact.name}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def list_facts(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all fact tables"""
        try:
            from ..data_mart import get_data_mart_engine
            engine = get_data_mart_engine()
            facts = engine.list_facts()
            return {'status': 'success', 'data': {'facts': facts}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def create_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dashboard"""
        try:
            from ..dashboard import get_dashboard_builder
            builder = get_dashboard_builder()
            dashboard = builder.create_dashboard(
                request['name'],
                request['title'],
                request.get('description', ''),
                request.get('owner', '')
            )
            return {'status': 'success', 'data': {'name': dashboard.name}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def list_dashboards(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all dashboards"""
        try:
            from ..dashboard import get_dashboard_builder
            builder = get_dashboard_builder()
            dashboards = builder.list_dashboards()
            return {'status': 'success', 'data': {'dashboards': dashboards}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def get_dashboard(self, dashboard_name: str) -> Dict[str, Any]:
        """Get dashboard details"""
        try:
            from ..dashboard import get_dashboard_builder
            builder = get_dashboard_builder()
            summary = builder.get_dashboard_summary(dashboard_name)
            return {'status': 'success', 'data': summary}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def add_widget(self, dashboard_name: str, 
                        request: Dict[str, Any]) -> Dict[str, Any]:
        """Add widget to dashboard"""
        try:
            from ..dashboard import get_dashboard_builder, Widget
            builder = get_dashboard_builder()
            widget = Widget(**request)
            builder.add_widget(dashboard_name, widget)
            return {'status': 'success', 'data': {'widget_id': widget.id}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def create_report(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a report"""
        try:
            from ..reports import get_report_generator
            generator = get_report_generator()
            report = generator.create_report(
                request['name'],
                request['title'],
                request.get('description', ''),
                request.get('owner', '')
            )
            return {'status': 'success', 'data': {'name': report.name}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def list_reports(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all reports"""
        try:
            from ..reports import get_report_generator
            generator = get_report_generator()
            reports = generator.list_reports()
            return {'status': 'success', 'data': {'reports': reports}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def get_report(self, report_name: str) -> Dict[str, Any]:
        """Get report details"""
        try:
            from ..reports import get_report_generator
            generator = get_report_generator()
            report = generator.get_report(report_name)
            if not report:
                return {'status': 'error', 'error': f'Report {report_name} not found'}
            return {'status': 'success', 'data': {'name': report.name, 'title': report.title}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def generate_report(self, report_name: str, 
                             request: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a report"""
        try:
            from ..reports import get_report_generator, ReportFormat
            generator = get_report_generator()
            format_str = request.get('format', 'pdf') if request else 'pdf'
            format_enum = ReportFormat[format_str.upper()]
            output_path = generator.generate_report(report_name, format_enum)
            return {'status': 'success', 'data': {'output_path': output_path}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def execute_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query"""
        try:
            from ..query_engine import get_query_optimizer
            optimizer = get_query_optimizer()
            result, execution = optimizer.execute_query(
                request['query'],
                request.get('use_cache', True)
            )
            return {
                'status': 'success',
                'data': {
                    'result': result,
                    'execution_time_ms': execution.execution_time_ms
                }
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def optimize_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a query"""
        try:
            from ..query_engine import get_query_optimizer
            optimizer = get_query_optimizer()
            plan = optimizer.optimize_query(request['query'])
            return {
                'status': 'success',
                'data': {
                    'estimated_cost': plan.estimated_cost,
                    'suggestions': plan.index_suggestions
                }
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def clear_query_cache(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """Clear query cache"""
        try:
            from ..query_engine import get_query_optimizer
            optimizer = get_query_optimizer()
            count = optimizer.clear_cache()
            return {'status': 'success', 'data': {'cleared': count}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def register_asset(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Register metadata asset"""
        try:
            from ..metadata import get_metadata_manager, AssetType
            manager = get_metadata_manager()
            asset = manager.register_asset(
                request['name'],
                AssetType(request['asset_type']),
                request.get('description', ''),
                request.get('owner', '')
            )
            return {'status': 'success', 'data': {'asset_id': asset.id}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def search_assets(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Search metadata assets"""
        try:
            from ..metadata import get_metadata_manager, AssetType, DataClassification
            manager = get_metadata_manager()
            assets = manager.search_assets(
                request.get('query', ''),
                AssetType(request['asset_type']) if 'asset_type' in request else None,
                DataClassification(request['classification']) if 'classification' in request else None,
                request.get('tags', [])
            )
            return {
                'status': 'success',
                'data': {'assets': [a.name for a in assets]}
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """Get asset details"""
        try:
            from ..metadata import get_metadata_manager
            manager = get_metadata_manager()
            asset = manager.get_asset(asset_id)
            if not asset:
                return {'status': 'error', 'error': f'Asset {asset_id} not found'}
            return {'status': 'success', 'data': {'name': asset.name}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def create_chart(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chart"""
        try:
            from ..visualization import get_chart_factory, ChartType
            factory = get_chart_factory()
            chart = factory.create_bar_chart(
                request['chart_id'],
                request['title'],
                request['category_key'],
                request['value_keys']
            )
            return {'status': 'success', 'data': {'chart_id': chart.id}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def list_charts(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all charts"""
        try:
            from ..visualization import get_chart_factory
            factory = get_chart_factory()
            charts = factory.list_charts()
            return {'status': 'success', 'data': {'charts': charts}}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def get_chart(self, chart_id: str) -> Dict[str, Any]:
        """Get chart details"""
        try:
            from ..visualization import get_chart_factory
            factory = get_chart_factory()
            summary = factory.get_chart_summary(chart_id)
            return {'status': 'success', 'data': summary}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def health_check(self, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """System health check"""
        try:
            from ..data_mart import get_data_mart_engine
            from ..dashboard import get_dashboard_builder
            from ..reports import get_report_generator
            from ..query_engine import get_query_optimizer
            from ..metadata import get_metadata_manager
            from ..visualization import get_chart_factory
            
            health = {
                'status': 'healthy',
                'components': {
                    'data_mart': get_data_mart_engine().health_check(),
                    'dashboard': get_dashboard_builder().health_check(),
                    'reports': get_report_generator().health_check(),
                    'query_engine': get_query_optimizer().health_check(),
                    'metadata': get_metadata_manager().health_check(),
                    'visualization': get_chart_factory().health_check(),
                }
            }
            return health
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


def get_bi_rest_api() -> BIRestAPI:
    """Factory function to get REST API instance"""
    return BIRestAPI()
