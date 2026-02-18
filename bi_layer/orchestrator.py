"""
BI Layer Orchestrator

Central orchestration point for managing all BI layer operations.
Coordinates between data mart, dashboards, reports, metadata, and visualizations.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path


logger = logging.getLogger(__name__)


class BIOrchestrator:
    """Orchestrates BI layer operations and workflows"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize BI Orchestrator
        
        Args:
            config_path: Path to configuration file
        """
        from bi_layer import get_bi_manager
        
        self.manager = get_bi_manager(config_path)
        self.workflows = {}
        self.execution_history = []
        
        logger.info("BI Orchestrator initialized")
    
    def execute_workflow(self, workflow_name: str, 
                        workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a multi-step BI workflow
        
        Args:
            workflow_name: Name of the workflow
            workflow_steps: List of steps to execute
        
        Returns:
            Workflow execution results
        """
        logger.info(f"Starting workflow: {workflow_name}")
        
        execution = {
            "workflow_name": workflow_name,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "steps": [],
            "results": {}
        }
        
        try:
            for step_index, step in enumerate(workflow_steps):
                step_result = self._execute_step(step)
                execution["steps"].append(step_result)
                
                if step_result["status"] != "success":
                    execution["status"] = "failed"
                    logger.error(f"Step {step_index} failed: {step_result['error']}")
                    break
            
            if execution["status"] != "failed":
                execution["status"] = "success"
                logger.info(f"Workflow '{workflow_name}' completed successfully")
            
        except Exception as e:
            execution["status"] = "error"
            execution["error"] = str(e)
            logger.error(f"Workflow execution error: {e}")
        
        execution["completed_at"] = datetime.now().isoformat()
        self.execution_history.append(execution)
        
        return execution
    
    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_name = step.get("name", "unknown")
        step_type = step.get("type", "")
        
        result = {
            "name": step_name,
            "type": step_type,
            "status": "pending",
            "started_at": datetime.now().isoformat()
        }
        
        try:
            if step_type == "create_dimension":
                result["data"] = self._create_dimension_step(step)
            
            elif step_type == "create_fact":
                result["data"] = self._create_fact_step(step)
            
            elif step_type == "create_data_mart":
                result["data"] = self._create_data_mart_step(step)
            
            elif step_type == "create_dashboard":
                result["data"] = self._create_dashboard_step(step)
            
            elif step_type == "add_widget":
                result["data"] = self._add_widget_step(step)
            
            elif step_type == "create_report":
                result["data"] = self._create_report_step(step)
            
            elif step_type == "register_asset":
                result["data"] = self._register_asset_step(step)
            
            elif step_type == "create_chart":
                result["data"] = self._create_chart_step(step)
            
            else:
                raise ValueError(f"Unknown step type: {step_type}")
            
            result["status"] = "success"
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Step '{step_name}' failed: {e}")
        
        result["completed_at"] = datetime.now().isoformat()
        return result
    
    def _create_dimension_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create dimension in workflow"""
        engine = self.manager.data_mart
        dimension = engine.create_dimension(
            name=step["name"],
            columns=step["columns"],
            table_name=step.get("table_name"),
            description=step.get("description", ""),
            scd_type=step.get("scd_type", 1)
        )
        return {"dimension_name": dimension.name}
    
    def _create_fact_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create fact table in workflow"""
        engine = self.manager.data_mart
        fact = engine.create_fact(
            name=step["name"],
            columns=step["columns"],
            table_name=step.get("table_name"),
            grain=step.get("grain"),
            description=step.get("description", "")
        )
        return {"fact_name": fact.name}
    
    def _create_data_mart_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create data mart in workflow"""
        engine = self.manager.data_mart
        mart = engine.create_data_mart(
            mart_name=step["name"],
            dimensions=step.get("dimensions", []),
            facts=step.get("facts", []),
            description=step.get("description", "")
        )
        return {"mart_name": mart["name"]}
    
    def _create_dashboard_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create dashboard in workflow"""
        builder = self.manager.dashboard
        dashboard = builder.create_dashboard(
            name=step["name"],
            title=step.get("title"),
            description=step.get("description", ""),
            owner=step.get("owner", "")
        )
        return {"dashboard_name": dashboard.name}
    
    def _add_widget_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Add widget to dashboard in workflow"""
        from bi_layer.dashboard import Widget
        
        builder = self.manager.dashboard
        widget = Widget(**step.get("widget", {}))
        builder.add_widget(step["dashboard_name"], widget)
        
        return {"widget_id": widget.id}
    
    def _create_report_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create report in workflow"""
        generator = self.manager.reports
        report = generator.create_report(
            name=step["name"],
            title=step.get("title"),
            description=step.get("description", ""),
            owner=step.get("owner", "")
        )
        return {"report_name": report.name}
    
    def _register_asset_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Register metadata asset in workflow"""
        from bi_layer.metadata import AssetType
        
        metadata = self.manager.metadata
        asset = metadata.register_asset(
            name=step["name"],
            asset_type=AssetType(step.get("asset_type", "dataset")),
            description=step.get("description", ""),
            owner=step.get("owner", "")
        )
        return {"asset_id": asset.id}
    
    def _create_chart_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Create chart in workflow"""
        factory = self.manager.visualization
        
        chart_type = step.get("chart_type", "bar")
        
        if chart_type == "bar":
            chart = factory.create_bar_chart(
                chart_id=step["name"],
                title=step.get("title"),
                category_key=step.get("category_key"),
                value_keys=step.get("value_keys", [])
            )
        elif chart_type == "line":
            chart = factory.create_line_chart(
                chart_id=step["name"],
                title=step.get("title"),
                time_key=step.get("time_key"),
                value_keys=step.get("value_keys", [])
            )
        elif chart_type == "pie":
            chart = factory.create_pie_chart(
                chart_id=step["name"],
                title=step.get("title"),
                label_key=step.get("label_key"),
                value_key=step.get("value_key")
            )
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        return {"chart_id": chart.id}
    
    def create_sales_analytics_workspace(self) -> Dict[str, Any]:
        """Create a complete sales analytics workspace (example workflow)"""
        logger.info("Creating sales analytics workspace...")
        
        workflow_steps = [
            # Create dimensions
            {
                "name": "create_customer_dim",
                "type": "create_dimension",
                "name": "customer",
                "table_name": "dim_customer",
                "columns": [
                    {"name": "customer_id", "type": "int"},
                    {"name": "customer_name", "type": "string"},
                    {"name": "segment", "type": "string"}
                ],
                "description": "Customer dimension"
            },
            {
                "name": "create_product_dim",
                "type": "create_dimension",
                "name": "product",
                "table_name": "dim_product",
                "columns": [
                    {"name": "product_id", "type": "int"},
                    {"name": "product_name", "type": "string"},
                    {"name": "category", "type": "string"}
                ],
                "description": "Product dimension"
            },
            {
                "name": "create_date_dim",
                "type": "create_dimension",
                "name": "date",
                "table_name": "dim_date",
                "columns": [
                    {"name": "date_key", "type": "int"},
                    {"name": "date", "type": "date"}
                ],
                "description": "Date dimension"
            },
            
            # Create fact table
            {
                "name": "create_sales_fact",
                "type": "create_fact",
                "name": "sales",
                "table_name": "fact_sales",
                "columns": [
                    {"name": "customer_id", "type": "int"},
                    {"name": "product_id", "type": "int"},
                    {"name": "date_key", "type": "int"},
                    {"name": "quantity", "type": "int"},
                    {"name": "amount", "type": "decimal"}
                ],
                "grain": "transaction",
                "description": "Sales fact table"
            },
            
            # Create data mart
            {
                "name": "create_sales_mart",
                "type": "create_data_mart",
                "name": "sales_mart",
                "dimensions": ["customer", "product", "date"],
                "facts": ["sales"],
                "description": "Sales analytics mart"
            },
            
            # Create dashboard
            {
                "name": "create_sales_dashboard",
                "type": "create_dashboard",
                "name": "sales_dashboard",
                "title": "Sales Analytics Dashboard",
                "owner": "analytics_team"
            },
            
            # Create charts
            {
                "name": "create_sales_by_category",
                "type": "create_chart",
                "chart_type": "bar",
                "name": "sales_by_category",
                "title": "Sales by Category",
                "category_key": "category",
                "value_keys": ["amount"]
            },
            
            {
                "name": "create_sales_trend",
                "type": "create_chart",
                "chart_type": "line",
                "name": "sales_trend",
                "title": "Sales Trend",
                "time_key": "date",
                "value_keys": ["amount"]
            },
            
            # Register metadata assets
            {
                "name": "register_sales_dataset",
                "type": "register_asset",
                "name": "sales_dataset",
                "asset_type": "dataset",
                "description": "Sales master dataset",
                "owner": "data_engineering"
            }
        ]
        
        return self.execute_workflow("create_sales_analytics", workflow_steps)
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow executions"""
        return self.execution_history[-limit:]
    
    def export_execution_report(self, output_path: str) -> str:
        """Export execution history as report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_executions": len(self.execution_history),
            "executions": self.execution_history
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Execution report saved to {output_path}")
        return output_path
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of entire BI workspace"""
        return {
            "orchestrator_status": "healthy",
            "components": self.manager.health_check(),
            "workflows_executed": len(self.execution_history),
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }


def get_bi_orchestrator(config_path: Optional[str] = None) -> BIOrchestrator:
    """Factory function to get BIOrchestrator instance"""
    return BIOrchestrator(config_path)
