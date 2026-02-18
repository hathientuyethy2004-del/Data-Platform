"""
BI Layer Integration Tests
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

# Import all BI components
from bi_layer import (
    get_bi_manager,
    BILayerManager,
    DataMartEngine,
    DashboardBuilder,
    ReportGenerator,
    MetadataManager,
    QueryOptimizer,
    ChartFactory
)

from bi_layer.data_mart import Dimension, Fact
from bi_layer.dashboard import Dashboard, Widget
from bi_layer.reports import Report, ReportSection, ReportFormat
from bi_layer.metadata import DataAsset, AssetType, DataClassification
from bi_layer.visualization import ChartType, ChartTheme


class TestDataMartEngine:
    """Test Data Mart Engine"""
    
    def test_create_dimension(self):
        """Test creating a dimension"""
        engine = DataMartEngine()
        
        dimension = engine.create_dimension(
            name="test_dim",
            columns=[{"name": "id", "type": "int"}, {"name": "name", "type": "string"}],
            table_name="test_dim_table",
            description="Test dimension"
        )
        
        assert dimension.name == "test_dim"
        assert dimension.table_name == "test_dim_table"
    
    def test_create_fact(self):
        """Test creating a fact table"""
        engine = DataMartEngine()
        
        # Create dimension first
        dim = engine.create_dimension(
            name="test_dim2",
            columns=[{"name": "id", "type": "int"}],
            table_name="test_dim2_table"
        )
        
        # Create fact
        fact = engine.create_fact(
            name="test_fact",
            columns=[{"name": "dim_id", "type": "int"}, {"name": "amount", "type": "decimal"}],
            table_name="test_fact_table",
            grain="transaction",
            description="Test fact"
        )
        
        assert fact.name == "test_fact"
        assert fact.grain == "transaction"
    
    def test_list_dimensions(self):
        """Test listing dimensions"""
        engine = DataMartEngine()
        dims = engine.list_dimensions()
        assert isinstance(dims, list)


class TestDashboardBuilder:
    """Test Dashboard Builder"""
    
    def test_create_dashboard(self):
        """Test creating a dashboard"""
        builder = DashboardBuilder()
        
        dashboard = builder.create_dashboard(
            name="test_dashboard",
            title="Test Dashboard",
            description="Test dashboard description",
            owner="test_user"
        )
        
        assert dashboard.name == "test_dashboard"
        assert dashboard.title == "Test Dashboard"
        assert dashboard.owner == "test_user"
    
    def test_add_widget(self):
        """Test adding widget to dashboard"""
        builder = DashboardBuilder()
        
        dashboard = builder.create_dashboard(
            name="dash_with_widget",
            title="Dashboard with Widget"
        )
        
        widget = Widget(
            id="widget_1",
            type="chart",
            title="Test Chart",
            query="SELECT * FROM data",
            position={"x": 0, "y": 0, "width": 6, "height": 4}
        )
        
        builder.add_widget("dash_with_widget", widget)
        
        dashboard = builder.get_dashboard("dash_with_widget")
        assert len(dashboard.widgets) == 1
        assert dashboard.widgets[0].id == "widget_1"
    
    def test_list_dashboards(self):
        """Test listing dashboards"""
        builder = DashboardBuilder()
        dashboards = builder.list_dashboards()
        assert isinstance(dashboards, list)


class TestReportGenerator:
    """Test Report Generator"""
    
    def test_create_report(self):
        """Test creating a report"""
        generator = ReportGenerator()
        
        report = generator.create_report(
            name="test_report",
            title="Test Report",
            description="Test report description",
            owner="test_user"
        )
        
        assert report.name == "test_report"
        assert report.title == "Test Report"
    
    def test_add_section(self):
        """Test adding section to report"""
        generator = ReportGenerator()
        
        report = generator.create_report(
            name="report_with_section",
            title="Report with Section"
        )
        
        section = ReportSection(
            id="section_1",
            title="Section 1",
            content_type="table",
            query="SELECT * FROM data"
        )
        
        generator.add_section("report_with_section", section)
        
        report = generator.get_report("report_with_section")
        assert len(report.sections) == 1
    
    def test_list_reports(self):
        """Test listing reports"""
        generator = ReportGenerator()
        reports = generator.list_reports()
        assert isinstance(reports, list)


class TestQueryOptimizer:
    """Test Query Optimizer"""
    
    def test_parse_query(self):
        """Test query parsing"""
        optimizer = QueryOptimizer()
        
        query = "SELECT col1, col2 FROM table1 WHERE col1 > 10"
        analysis = optimizer.parse_query(query)
        
        assert analysis['is_select'] == True
        assert 'table1' in analysis['tables_referenced']
    
    def test_optimize_query(self):
        """Test query optimization"""
        optimizer = QueryOptimizer()
        
        query = "SELECT * FROM table1 WHERE col1 > 10"
        plan = optimizer.optimize_query(query)
        
        assert plan.original_query == query
        assert plan.estimated_cost > 0
    
    def test_execute_query(self):
        """Test query execution"""
        optimizer = QueryOptimizer()
        
        query = "SELECT 1 as col1"
        result, execution = optimizer.execute_query(query)
        
        assert execution.status == "success"
        assert execution.execution_time_ms >= 0


class TestMetadataManager:
    """Test Metadata Manager"""
    
    def test_register_asset(self):
        """Test registering an asset"""
        manager = MetadataManager()
        
        asset = manager.register_asset(
            name="test_dataset",
            asset_type=AssetType.DATASET,
            description="Test dataset",
            owner="test_user"
        )
        
        assert asset.name == "test_dataset"
        assert asset.asset_type == AssetType.DATASET
    
    def test_add_tags(self):
        """Test adding tags to asset"""
        manager = MetadataManager()
        
        asset = manager.register_asset(
            name="tagged_asset",
            asset_type=AssetType.TABLE
        )
        
        manager.add_tags(asset.id, ["important", "production"])
        
        asset = manager.get_asset(asset.id)
        assert "important" in asset.tags
        assert "production" in asset.tags
    
    def test_search_assets(self):
        """Test searching assets"""
        manager = MetadataManager()
        
        asset1 = manager.register_asset(
            name="search_test_1",
            asset_type=AssetType.TABLE,
            description="This is a test"
        )
        
        manager.add_tags(asset1.id, ["test"])
        
        results = manager.search_assets(query="search_test")
        assert len(results) >= 1


class TestChartFactory:
    """Test Chart Factory"""
    
    def test_create_bar_chart(self):
        """Test creating a bar chart"""
        factory = ChartFactory()
        
        chart = factory.create_bar_chart(
            chart_id="test_bar",
            title="Test Bar Chart",
            category_key="category",
            value_keys=["value1", "value2"]
        )
        
        assert chart.id == "test_bar"
        assert chart.chart_type == ChartType.BAR
        assert len(chart.series) == 2
    
    def test_create_line_chart(self):
        """Test creating a line chart"""
        factory = ChartFactory()
        
        chart = factory.create_line_chart(
            chart_id="test_line",
            title="Test Line Chart",
            time_key="date",
            value_keys=["metric1", "metric2"]
        )
        
        assert chart.id == "test_line"
        assert chart.chart_type == ChartType.LINE
    
    def test_apply_color_scheme(self):
        """Test applying color scheme"""
        factory = ChartFactory()
        
        chart = factory.create_bar_chart(
            chart_id="colored_chart",
            title="Colored Chart",
            category_key="cat",
            value_keys=["val"]
        )
        
        factory.apply_color_scheme("colored_chart", "pastel")
        chart = factory.get_chart("colored_chart")
        
        assert chart.series[0].color is not None


class TestBILayerManager:
    """Test BILayerManager integration"""
    
    def test_get_bi_manager(self):
        """Test getting BILayerManager instance"""
        manager = get_bi_manager()
        assert isinstance(manager, BILayerManager)
    
    def test_health_check(self):
        """Test health check"""
        manager = get_bi_manager()
        health = manager.health_check()
        
        assert 'data_mart' in health
        assert 'dashboard' in health
        assert 'reports' in health
        assert 'metadata' in health
        assert 'query_engine' in health
        assert 'visualization' in health
    
    def test_get_component(self):
        """Test getting specific component"""
        manager = get_bi_manager()
        
        data_mart = manager.get_component('data_mart')
        assert isinstance(data_mart, DataMartEngine)
        
        dashboard = manager.get_component('dashboard')
        assert isinstance(dashboard, DashboardBuilder)


class TestBIRestAPI:
    """Test REST API"""
    
    def test_rest_api_import(self):
        """Test importing REST API"""
        from bi_layer.api import get_bi_rest_api
        api = get_bi_rest_api()
        assert api is not None
        assert len(api.routes) > 0


@pytest.fixture
def bi_manager():
    """Fixture for BILayerManager"""
    return get_bi_manager()


def test_full_workflow(bi_manager):
    """Test complete BI workflow"""
    # 1. Create data mart
    dim = bi_manager.data_mart.create_dimension(
        name="workflow_dim",
        columns=[{"name": "id", "type": "int"}, {"name": "name", "type": "string"}],
        table_name="workflow_dim_table"
    )
    
    # 2. Create dashboard
    dashboard = bi_manager.dashboard.create_dashboard(
        name="workflow_dashboard",
        title="Workflow Dashboard"
    )
    
    # 3. Create widget
    widget = Widget(
        id="workflow_widget",
        type="metric",
        title="Key Metric",
        query="SELECT COUNT(*) FROM data"
    )
    bi_manager.dashboard.add_widget("workflow_dashboard", widget)
    
    # 4. Register metadata
    asset = bi_manager.metadata.register_asset(
        name="workflow_dataset",
        asset_type=AssetType.DATASET
    )
    
    # 5. Create chart
    chart = bi_manager.visualization.create_bar_chart(
        chart_id="workflow_chart",
        title="Workflow Chart",
        category_key="category",
        value_keys=["value"]
    )
    
    # 6. Check health
    health = bi_manager.health_check()
    assert health is not None
    
    # Verify all components are healthy
    for component_name, component_health in health.items():
        assert component_health['status'] == 'healthy'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
