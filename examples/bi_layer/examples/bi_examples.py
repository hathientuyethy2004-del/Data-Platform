"""
BI Layer Usage Examples

Demonstrates how to use each component of the BI layer.
"""

from bi_layer import get_bi_manager
from bi_layer.data_mart import Dimension, Fact
from bi_layer.dashboard import Widget
from bi_layer.reports import ReportSection, ReportFormat, ReportSchedule
from bi_layer.metadata import AssetType, DataClassification, DataQualityMetrics
from bi_layer.visualization import ChartType


def example_data_mart():
    """Example: Create a dimensional data mart"""
    print("\n=== Data Mart Example ===\n")
    
    manager = get_bi_manager()
    engine = manager.data_mart
    
    # Create dimensions
    print("Creating dimensions...")
    
    customer_dim = engine.create_dimension(
        name="customer",
        columns=[
            {"name": "customer_id", "type": "int"},
            {"name": "customer_name", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "segment", "type": "string"}
        ],
        table_name="dim_customer",
        description="Customer dimension",
        scd_type=2
    )
    
    product_dim = engine.create_dimension(
        name="product",
        columns=[
            {"name": "product_id", "type": "int"},
            {"name": "product_name", "type": "string"},
            {"name": "category", "type": "string"},
            {"name": "price", "type": "decimal"}
        ],
        table_name="dim_product",
        description="Product dimension"
    )
    
    time_dim = engine.create_dimension(
        name="time",
        columns=[
            {"name": "date_key", "type": "int"},
            {"name": "date", "type": "date"},
            {"name": "month", "type": "int"},
            {"name": "year", "type": "int"}
        ],
        table_name="dim_time",
        description="Time dimension"
    )
    
    print(f"✓ Created dimension: {customer_dim.name}")
    print(f"✓ Created dimension: {product_dim.name}")
    print(f"✓ Created dimension: {time_dim.name}")
    
    # Create fact table
    print("\nCreating fact table...")
    
    sales_fact = engine.create_fact(
        name="sales",
        columns=[
            {"name": "customer_id", "type": "int"},
            {"name": "product_id", "type": "int"},
            {"name": "date_key", "type": "int"},
            {"name": "quantity", "type": "int"},
            {"name": "amount", "type": "decimal"},
            {"name": "discount", "type": "decimal"}
        ],
        table_name="fact_sales",
        grain="transaction",
        description="Sales transactions"
    )
    
    print(f"✓ Created fact table: {sales_fact.name}")
    
    # Create data mart
    print("\nCreating data mart...")
    
    mart = engine.create_data_mart(
        mart_name="sales_mart",
        dimensions=["customer", "product", "time"],
        facts=["sales"],
        description="Sales analytics data mart"
    )
    
    print(f"✓ Created data mart: {mart['name']}")
    
    # Show schema
    print("\nData Mart Schema:")
    schema = engine.get_mart_schema("sales_mart")
    print(f"  Dimensions: {list(schema['dimensions'].keys())}")
    print(f"  Facts: {list(schema['facts'].keys())}")


def example_dashboard():
    """Example: Create an interactive dashboard"""
    print("\n=== Dashboard Example ===\n")
    
    manager = get_bi_manager()
    builder = manager.dashboard
    
    # Create dashboard
    print("Creating dashboard...")
    
    dashboard = builder.create_dashboard(
        name="sales_performance",
        title="Sales Performance Dashboard",
        description="Real-time sales metrics and trends",
        owner="analytics_team"
    )
    
    print(f"✓ Created dashboard: {dashboard.name}")
    
    # Add widgets
    print("\nAdding widgets...")
    
    # Metric widget
    metric_widget = Widget(
        id="total_revenue",
        type="metric",
        title="Total Revenue",
        query="SELECT SUM(amount) FROM fact_sales",
        position={"x": 0, "y": 0, "width": 3, "height": 2},
        refresh_interval=300
    )
    builder.add_widget("sales_performance", metric_widget)
    print("✓ Added metric widget: Total Revenue")
    
    # Sales by region chart
    region_chart = Widget(
        id="sales_by_region",
        type="chart",
        title="Sales by Region",
        query="SELECT region, SUM(amount) as sales FROM sales GROUP BY region",
        position={"x": 3, "y": 0, "width": 6, "height": 3},
        config={"chart_type": "bar"}
    )
    builder.add_widget("sales_performance", region_chart)
    print("✓ Added chart widget: Sales by Region")
    
    # Trend chart
    trend_chart = Widget(
        id="revenue_trend",
        type="chart",
        title="Revenue Trend",
        query="SELECT date, SUM(amount) as revenue FROM sales GROUP BY date ORDER BY date",
        position={"x": 0, "y": 3, "width": 9, "height": 3},
        config={"chart_type": "line"}
    )
    builder.add_widget("sales_performance", trend_chart)
    print("✓ Added chart widget: Revenue Trend")
    
    # Show dashboard summary
    print("\nDashboard Summary:")
    summary = builder.get_dashboard_summary("sales_performance")
    print(f"  Title: {summary['title']}")
    print(f"  Owner: {summary['owner']}")
    print(f"  Widgets: {summary['widgets_count']}")
    print(f"  Types: {summary['widget_types']}")


def example_reports():
    """Example: Create scheduled reports"""
    print("\n=== Report Example ===\n")
    
    manager = get_bi_manager()
    generator = manager.reports
    
    # Create report
    print("Creating report...")
    
    report = generator.create_report(
        name="monthly_sales",
        title="Monthly Sales Report",
        description="Comprehensive monthly sales analysis",
        owner="sales_team"
    )
    
    print(f"✓ Created report: {report.name}")
    
    # Add sections
    print("\nAdding sections...")
    
    # Executive summary
    exec_section = ReportSection(
        id="executive_summary",
        title="Executive Summary",
        content_type="text",
        query="",
        order=1
    )
    generator.add_section("monthly_sales", exec_section)
    print("✓ Added section: Executive Summary")
    
    # Revenue analysis
    revenue_section = ReportSection(
        id="revenue_analysis",
        title="Revenue Analysis",
        content_type="table",
        query="SELECT month, COUNT(*) as transactions, SUM(amount) as revenue FROM sales GROUP BY month",
        order=2
    )
    generator.add_section("monthly_sales", revenue_section)
    print("✓ Added section: Revenue Analysis")
    
    # Regional performance
    region_section = ReportSection(
        id="regional_performance",
        title="Regional Performance",
        content_type="chart",
        query="SELECT region, SUM(amount) as sales FROM sales GROUP BY region",
        order=3
    )
    generator.add_section("monthly_sales", region_section)
    print("✓ Added section: Regional Performance")
    
    # Configure scheduling
    print("\nConfiguring scheduling...")
    
    generator.configure_scheduling(
        report_name="monthly_sales",
        schedule=ReportSchedule.MONTHLY,
        schedule_time="01:00",
        recipients=["sales-team@company.com", "executive@company.com"]
    )
    
    print("✓ Report scheduled for monthly generation at 01:00")
    
    # Generate report
    print("\nGenerating report...")
    output_path = generator.generate_report("monthly_sales", ReportFormat.HTML)
    print(f"✓ Report generated: {output_path}")


def example_queries():
    """Example: Query optimization and execution"""
    print("\n=== Query Optimization Example ===\n")
    
    manager = get_bi_manager()
    optimizer = manager.query_engine
    
    # Parse query
    print("Analyzing query...")
    
    query = "SELECT customer_id, SUM(amount) as total FROM fact_sales GROUP BY customer_id"
    analysis = optimizer.parse_query(query)
    
    print(f"✓ Query analyzed:")
    print(f"  - Is SELECT: {analysis['is_select']}")
    print(f"  - Has aggregation: {analysis['is_aggregate']}")
    print(f"  - Has GROUP BY: {analysis['has_group_by']}")
    print(f"  - Tables: {analysis['tables_referenced']}")
    
    # Optimize query
    print("\nOptimizing query...")
    
    plan = optimizer.optimize_query(query)
    print(f"✓ Optimization plan created:")
    print(f"  - Estimated cost: {plan.estimated_cost}")
    print(f"  - Suggestions: {plan.index_suggestions}")
    
    # Execute query
    print("\nExecuting query...")
    
    result, execution = optimizer.execute_query(query, use_cache=True)
    print(f"✓ Query executed:")
    print(f"  - Status: {execution.status}")
    print(f"  - Time: {execution.execution_time_ms:.2f}ms")
    print(f"  - Cache hit: {execution.cache_hit}")
    
    # Get statistics
    print("\nQuery statistics:")
    stats = optimizer.get_query_statistics()
    print(f"  - Total queries: {stats['total_queries']}")
    print(f"  - Successful: {stats['successful']}")
    print(f"  - Average time: {stats['average_execution_time_ms']:.2f}ms")
    print(f"  - Cache entries: {stats['cache_size']}")


def example_metadata():
    """Example: Metadata catalog and lineage"""
    print("\n=== Metadata Example ===\n")
    
    manager = get_bi_manager()
    metadata = manager.metadata
    
    # Register assets
    print("Registering data assets...")
    
    raw_data = metadata.register_asset(
        name="raw_customer_data",
        asset_type=AssetType.DATASET,
        description="Raw customer data from CRM",
        owner="data_engineering",
        source_system="Salesforce",
        classification=DataClassification.INTERNAL
    )
    print(f"✓ Registered: {raw_data.name}")
    
    customer_table = metadata.register_asset(
        name="customer_table",
        asset_type=AssetType.TABLE,
        description="Cleaned customer master data",
        owner="data_engineering",
        classification=DataClassification.INTERNAL
    )
    print(f"✓ Registered: {customer_table.name}")
    
    customer_dashboard = metadata.register_asset(
        name="customer_performance_dashboard",
        asset_type=AssetType.DASHBOARD,
        description="Customer performance metrics dashboard",
        owner="analytics_team"
    )
    print(f"✓ Registered: {customer_dashboard.name}")
    
    # Add tags
    print("\nAdding tags...")
    
    metadata.add_tags(customer_table.id, ["customer", "production", "critical", "pii"])
    print("✓ Added tags to customer_table")
    
    metadata.add_tags(customer_dashboard.id, ["dashboard", "production", "executive"])
    print("✓ Added tags to customer_dashboard")
    
    # Update lineage
    print("\nUpdating lineage...")
    
    metadata.update_lineage(
        asset_id=customer_table.id,
        upstream=[raw_data.id],
        downstream=[customer_dashboard.id]
    )
    print("✓ Updated lineage for customer_table")
    
    # Update quality metrics
    print("\nUpdating quality metrics...")
    
    quality = DataQualityMetrics(
        completeness=99.8,
        accuracy=99.5,
        consistency=99.2,
        timeliness=99.0,
        validity=100.0,
        uniqueness=98.5
    )
    
    metadata.update_quality_metrics(customer_table.id, quality)
    print("✓ Updated quality metrics for customer_table")
    
    # Search assets
    print("\nSearching assets...")
    
    results = metadata.search_assets(
        query="customer",
        asset_type=AssetType.TABLE,
        tags=["production"]
    )
    
    print(f"✓ Found {len(results)} assets matching criteria")
    for asset in results:
        print(f"  - {asset.name} ({asset.asset_type.value})")
    
    # Get impact analysis
    print("\nImpact analysis...")
    
    impact = metadata.get_impact_analysis(customer_table.id)
    print(f"✓ Asset '{impact['asset']}' impacts:")
    print(f"  - Direct dependencies: {impact['direct_dependencies']}")
    print(f"  - Total affected: {impact['dependency_count']}")
    print(f"  - High risk: {impact['high_risk']}")
    
    # Catalog summary
    print("\nCatalog summary:")
    summary = metadata.get_catalog_summary()
    print(f"  - Total assets: {summary['total_assets']}")
    print(f"  - By type: {summary['by_type']}")
    print(f"  - By classification: {summary['by_classification']}")


def example_charts():
    """Example: Creating visualizations"""
    print("\n=== Chart Factory Example ===\n")
    
    manager = get_bi_manager()
    factory = manager.visualization
    
    # Create bar chart
    print("Creating bar chart...")
    
    bar_chart = factory.create_bar_chart(
        chart_id="sales_by_category",
        title="Sales by Product Category",
        category_key="category",
        value_keys=["revenue", "units"]
    )
    
    print(f"✓ Created bar chart: {bar_chart.title}")
    factory.apply_color_scheme("sales_by_category", "vibrant")
    print("✓ Applied 'vibrant' color scheme")
    
    # Create line chart
    print("\nCreating line chart...")
    
    line_chart = factory.create_line_chart(
        chart_id="revenue_trend",
        title="Revenue Trend - Last 12 Months",
        time_key="date",
        value_keys=["revenue", "forecast"]
    )
    
    print(f"✓ Created line chart: {line_chart.title}")
    factory.apply_color_scheme("revenue_trend", "dark")
    print("✓ Applied 'dark' color scheme")
    
    # Create pie chart
    print("\nCreating pie chart...")
    
    pie_chart = factory.create_pie_chart(
        chart_id="market_share",
        title="Market Share by Competitor",
        label_key="competitor",
        value_key="market_percentage"
    )
    
    print(f"✓ Created pie chart: {pie_chart.title}")
    
    # List charts
    print("\nAvailable charts:")
    charts = factory.list_charts()
    for chart_id in charts:
        summary = factory.get_chart_summary(chart_id)
        print(f"  - {summary['title']} ({summary['chart_type']})")
    
    # List color schemes
    print("\nAvailable color schemes:")
    schemes = factory.list_color_schemes()
    for scheme in schemes:
        print(f"  - {scheme}")


def example_health_check():
    """Example: System health check"""
    print("\n=== System Health Check ===\n")
    
    manager = get_bi_manager()
    health = manager.health_check()
    
    print("BI Layer Component Status:")
    for component_name, component_health in health.items():
        status = component_health['status']
        print(f"\n✓ {component_name.replace('_', ' ').title()}: {status}")
        
        if 'dimensions_count' in component_health:
            print(f"  - Dimensions: {component_health['dimensions_count']}")
        if 'facts_count' in component_health:
            print(f"  - Facts: {component_health['facts_count']}")
        if 'marts_count' in component_health:
            print(f"  - Data Marts: {component_health['marts_count']}")
        if 'dashboards_count' in component_health:
            print(f"  - Dashboards: {component_health['dashboards_count']}")
        if 'reports_count' in component_health:
            print(f"  - Reports: {component_health['reports_count']}")
        if 'assets_count' in component_health:
            print(f"  - Metadata Assets: {component_health['assets_count']}")
        if 'charts_count' in component_health:
            print(f"  - Charts: {component_health['charts_count']}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("BI LAYER - COMPREHENSIVE USAGE EXAMPLES")
    print("=" * 60)
    
    try:
        example_data_mart()
        example_dashboard()
        example_reports()
        example_queries()
        example_metadata()
        example_charts()
        example_health_check()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
