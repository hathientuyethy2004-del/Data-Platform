"""
Dashboard Builder - Interactive Dashboard Creation and Management

Provides:
- Dashboard template management
- Widget configuration
- Layout management
- Real-time data binding
- Export capabilities
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field


logger = logging.getLogger(__name__)


@dataclass
class Widget:
    """Represents a dashboard widget"""
    id: str
    type: str  # chart, metric, table, gauge, etc.
    title: str
    query: str  # SQL or query definition
    position: Dict[str, int] = field(default_factory=dict)  # x, y, width, height
    config: Dict[str, Any] = field(default_factory=dict)  # Widget-specific config
    refresh_interval: int = 300  # seconds
    enabled: bool = True


@dataclass
class Dashboard:
    """Represents a dashboard"""
    name: str
    title: str
    description: str = ""
    widgets: List[Widget] = field(default_factory=list)
    width: int = 1200
    height: int = 800
    theme: str = "light"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    owner: str = ""
    tags: List[str] = field(default_factory=list)


class DashboardBuilder:
    """Manages dashboard creation and configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Dashboard Builder
        
        Args:
            config_path: Path to configuration file
        """
        from ..configs.bi_config import get_bi_config
        self.config = get_bi_config(config_path)
        self.storage_path = Path(self.config.get('dashboard.storage', 'analytics_data/dashboards'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.dashboards: Dict[str, Dashboard] = {}
        self.templates: Dict[str, Dashboard] = {}  # Dashboard templates
        
        self._load_dashboards()
    
    def _load_dashboards(self) -> None:
        """Load existing dashboards from storage"""
        dashboards_file = self.storage_path / 'dashboards.json'
        if dashboards_file.exists():
            try:
                with open(dashboards_file, 'r') as f:
                    data = json.load(f)
                    for dash_data in data.get('dashboards', []):
                        widgets = [
                            Widget(**widget_data) 
                            for widget_data in dash_data.get('widgets', [])
                        ]
                        dash_data['widgets'] = widgets
                        dashboard = Dashboard(**dash_data)
                        self.dashboards[dashboard.name] = dashboard
            except Exception as e:
                logger.warning(f"Failed to load dashboards: {e}")
    
    def _save_dashboards(self) -> None:
        """Save dashboards to storage"""
        dashboards_file = self.storage_path / 'dashboards.json'
        data = {
            'version': self.config.get('version'),
            'timestamp': datetime.now().isoformat(),
            'dashboards': [
                {**asdict(dash), 'widgets': [asdict(w) for w in dash.widgets]}
                for dash in self.dashboards.values()
            ]
        }
        try:
            with open(dashboards_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save dashboards: {e}")
    
    def create_dashboard(self, name: str, title: str, 
                        description: str = "", owner: str = "") -> Dashboard:
        """Create a new dashboard
        
        Args:
            name: Unique dashboard name
            title: Display title
            description: Dashboard description
            owner: Dashboard owner
        
        Returns:
            Created Dashboard object
        """
        if name in self.dashboards:
            raise ValueError(f"Dashboard '{name}' already exists")
        
        dashboard = Dashboard(
            name=name,
            title=title,
            description=description,
            owner=owner
        )
        
        self.dashboards[name] = dashboard
        logger.info(f"Created dashboard: {name}")
        self._save_dashboards()
        
        return dashboard
    
    def add_widget(self, dashboard_name: str, widget: Widget) -> Widget:
        """Add a widget to a dashboard
        
        Args:
            dashboard_name: Dashboard name
            widget: Widget to add
        
        Returns:
            Added Widget
        """
        dashboard = self.dashboards.get(dashboard_name)
        if not dashboard:
            raise ValueError(f"Dashboard '{dashboard_name}' not found")
        
        # Check if widget ID already exists
        if any(w.id == widget.id for w in dashboard.widgets):
            raise ValueError(f"Widget '{widget.id}' already exists in dashboard")
        
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now().isoformat()
        
        logger.info(f"Added widget '{widget.id}' to dashboard '{dashboard_name}'")
        self._save_dashboards()
        
        return widget
    
    def remove_widget(self, dashboard_name: str, widget_id: str) -> bool:
        """Remove a widget from a dashboard
        
        Args:
            dashboard_name: Dashboard name
            widget_id: Widget ID
        
        Returns:
            True if removed, False if not found
        """
        dashboard = self.dashboards.get(dashboard_name)
        if not dashboard:
            raise ValueError(f"Dashboard '{dashboard_name}' not found")
        
        dashboard.widgets = [w for w in dashboard.widgets if w.id != widget_id]
        dashboard.updated_at = datetime.now().isoformat()
        
        self._save_dashboards()
        return True
    
    def update_widget(self, dashboard_name: str, widget_id: str, 
                     updates: Dict[str, Any]) -> Widget:
        """Update a widget configuration
        
        Args:
            dashboard_name: Dashboard name
            widget_id: Widget ID
            updates: Dictionary of updates
        
        Returns:
            Updated Widget
        """
        dashboard = self.dashboards.get(dashboard_name)
        if not dashboard:
            raise ValueError(f"Dashboard '{dashboard_name}' not found")
        
        widget = None
        for w in dashboard.widgets:
            if w.id == widget_id:
                widget = w
                break
        
        if not widget:
            raise ValueError(f"Widget '{widget_id}' not found")
        
        # Update widget attributes
        for key, value in updates.items():
            if hasattr(widget, key):
                setattr(widget, key, value)
        
        dashboard.updated_at = datetime.now().isoformat()
        self._save_dashboards()
        
        return widget
    
    def get_dashboard(self, name: str) -> Optional[Dashboard]:
        """Get dashboard by name"""
        return self.dashboards.get(name)
    
    def list_dashboards(self) -> List[str]:
        """List all dashboard names"""
        return list(self.dashboards.keys())
    
    def create_template(self, name: str, dashboard_config: Dashboard) -> Dashboard:
        """Create a dashboard template
        
        Args:
            name: Template name
            dashboard_config: Template configuration
        
        Returns:
            Created template
        """
        self.templates[name] = dashboard_config
        logger.info(f"Created dashboard template: {name}")
        return dashboard_config
    
    def create_from_template(self, template_name: str, 
                            new_name: str, **kwargs) -> Dashboard:
        """Create a dashboard from a template
        
        Args:
            template_name: Template name to use
            new_name: Name for new dashboard
            **kwargs: Overrides for template values
        
        Returns:
            Created Dashboard
        """
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Clone template
        dashboard = Dashboard(
            name=new_name,
            title=kwargs.get('title', template.title),
            description=kwargs.get('description', template.description),
            widgets=[Widget(**asdict(w)) for w in template.widgets],
            owner=kwargs.get('owner', template.owner)
        )
        
        self.dashboards[new_name] = dashboard
        self._save_dashboards()
        
        return dashboard
    
    def export_dashboard(self, name: str, format: str = "json") -> str:
        """Export dashboard configuration
        
        Args:
            name: Dashboard name
            format: Export format (json, yaml, etc.)
        
        Returns:
            Dashboard configuration as string
        """
        dashboard = self.dashboards.get(name)
        if not dashboard:
            raise ValueError(f"Dashboard '{name}' not found")
        
        if format == "json":
            dashboard_dict = {
                **asdict(dashboard),
                'widgets': [asdict(w) for w in dashboard.widgets]
            }
            return json.dumps(dashboard_dict, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_dashboard(self, config_str: str, format: str = "json") -> Dashboard:
        """Import a dashboard from configuration
        
        Args:
            config_str: Configuration string
            format: Configuration format
        
        Returns:
            Imported Dashboard
        """
        if format == "json":
            data = json.loads(config_str)
            widgets = [Widget(**w) for w in data.pop('widgets', [])]
            dashboard = Dashboard(**data)
            dashboard.widgets = widgets
            self.dashboards[dashboard.name] = dashboard
            self._save_dashboards()
            return dashboard
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_dashboard_summary(self, name: str) -> Dict[str, Any]:
        """Get summary information about a dashboard"""
        dashboard = self.dashboards.get(name)
        if not dashboard:
            raise ValueError(f"Dashboard '{name}' not found")
        
        return {
            'name': dashboard.name,
            'title': dashboard.title,
            'description': dashboard.description,
            'owner': dashboard.owner,
            'widgets_count': len(dashboard.widgets),
            'widget_types': list(set(w.type for w in dashboard.widgets)),
            'created_at': dashboard.created_at,
            'updated_at': dashboard.updated_at,
            'tags': dashboard.tags
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of dashboard builder"""
        return {
            'status': 'healthy',
            'dashboards_count': len(self.dashboards),
            'templates_count': len(self.templates),
            'total_widgets': sum(len(d.widgets) for d in self.dashboards.values()),
            'storage_path': str(self.storage_path),
            'timestamp': datetime.now().isoformat()
        }


def get_dashboard_builder(config_path: Optional[str] = None) -> DashboardBuilder:
    """Factory function to get DashboardBuilder instance"""
    return DashboardBuilder(config_path)
