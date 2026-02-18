"""
Chart Factory - Chart and Visualization Component Creation

Provides:
- Chart type factory
- Visualization configuration
- Export capabilities
- Chart theming
- Interactive visualization support
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    SCATTER = "scatter"
    PIE = "pie"
    DONUT = "donut"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    BOX_PLOT = "boxplot"
    GAUGE = "gauge"
    SANKEY = "sankey"
    TREE_MAP = "treemap"
    BUBBLE = "bubble"
    WATERFALL = "waterfall"
    SUNBURST = "sunburst"


class ChartTheme(Enum):
    """Chart theme options"""
    LIGHT = "light"
    DARK = "dark"
    COLORBLIND = "colorblind"
    CUSTOM = "custom"


@dataclass
class ChartAxis:
    """Configuration for chart axis"""
    title: str
    data_key: str
    scale_type: str = "linear"  # linear, log, categorical, time
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class ChartSeries:
    """Represents a data series in chart"""
    name: str
    data_key: str
    color: Optional[str] = None
    line_width: float = 2.0
    chart_type: str = ""  # Override for mixed charts


@dataclass
class ChartConfig:
    """Complete chart configuration"""
    id: str
    title: str
    chart_type: ChartType
    x_axis: ChartAxis
    y_axis: Optional[ChartAxis] = None
    series: List[ChartSeries] = field(default_factory=list)
    width: int = 800
    height: int = 600
    theme: ChartTheme = ChartTheme.LIGHT
    legend_position: str = "right"  # top, bottom, left, right, none
    show_grid: bool = True
    show_legend: bool = True
    show_tooltip: bool = True
    enable_zoom: bool = False
    enable_pan: bool = False
    custom_colors: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ChartFactory:
    """Factory for creating and managing chart components"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Chart Factory
        
        Args:
            config_path: Path to configuration file
        """
        from ..configs.bi_config import get_bi_config
        self.config = get_bi_config(config_path)
        self.storage_path = Path(self.config.get('charts.storage', 'analytics_data/charts'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.charts: Dict[str, ChartConfig] = {}
        self.chart_templates: Dict[str, ChartConfig] = {}
        self.color_schemes: Dict[str, List[str]] = {}
        
        self._load_charts()
        self._initialize_color_schemes()
    
    def _initialize_color_schemes(self) -> None:
        """Initialize predefined color schemes"""
        self.color_schemes['default'] = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        self.color_schemes['pastel'] = [
            '#fbb4ae', '#b3cde3', '#ccebc5', '#decbe4', '#fed9a6',
            '#ffffcc', '#e5d8bd', '#fddaec', '#f2f2f2', '#d9d9d9'
        ]
        self.color_schemes['dark'] = [
            '#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51',
            '#1d3557', '#457b9d', '#a8dadc', '#f1faee', '#e63946'
        ]
        self.color_schemes['vibrant'] = [
            '#eb3b5a', '#fa8231', '#f9ca24', '#6c5ce7', '#0984e3',
            '#00b894', '#fdcb6e', '#74b9ff', '#a29bfe', '#fd79a8'
        ]
    
    def _load_charts(self) -> None:
        """Load existing chart configurations from storage"""
        charts_file = self.storage_path / 'charts.json'
        if charts_file.exists():
            try:
                with open(charts_file, 'r') as f:
                    data = json.load(f)
                    for chart_data in data.get('charts', []):
                        chart_data['chart_type'] = ChartType(chart_data.get('chart_type', 'bar'))
                        chart_data['theme'] = ChartTheme(chart_data.get('theme', 'light'))
                        
                        if 'x_axis' in chart_data:
                            chart_data['x_axis'] = ChartAxis(**chart_data['x_axis'])
                        if 'y_axis' in chart_data and chart_data['y_axis']:
                            chart_data['y_axis'] = ChartAxis(**chart_data['y_axis'])
                        
                        series_list = []
                        for s in chart_data.get('series', []):
                            series_list.append(ChartSeries(**s))
                        chart_data['series'] = series_list
                        
                        chart = ChartConfig(**chart_data)
                        self.charts[chart.id] = chart
            except Exception as e:
                logger.warning(f"Failed to load charts: {e}")
    
    def _save_charts(self) -> None:
        """Save chart configurations to storage"""
        charts_file = self.storage_path / 'charts.json'
        data = {
            'version': self.config.get('version'),
            'timestamp': datetime.now().isoformat(),
            'charts': [
                {
                    **asdict(chart),
                    'chart_type': chart.chart_type.value,
                    'theme': chart.theme.value,
                    'x_axis': asdict(chart.x_axis),
                    'y_axis': asdict(chart.y_axis) if chart.y_axis else None,
                    'series': [asdict(s) for s in chart.series]
                }
                for chart in self.charts.values()
            ]
        }
        try:
            with open(charts_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save charts: {e}")
    
    def create_chart(self, chart_id: str, title: str, chart_type: ChartType,
                    x_axis: ChartAxis, y_axis: Optional[ChartAxis] = None,
                    **kwargs) -> ChartConfig:
        """Create a new chart configuration
        
        Args:
            chart_id: Unique chart ID
            title: Chart title
            chart_type: Type of chart
            x_axis: X-axis configuration
            y_axis: Y-axis configuration
            **kwargs: Additional chart options
        
        Returns:
            Created ChartConfig
        """
        if chart_id in self.charts:
            raise ValueError(f"Chart '{chart_id}' already exists")
        
        chart = ChartConfig(
            id=chart_id,
            title=title,
            chart_type=chart_type,
            x_axis=x_axis,
            y_axis=y_axis,
            **kwargs
        )
        
        self.charts[chart_id] = chart
        logger.info(f"Created chart: {chart_id} ({chart_type.value})")
        self._save_charts()
        
        return chart
    
    def add_series(self, chart_id: str, series: ChartSeries) -> ChartSeries:
        """Add a data series to a chart"""
        chart = self.charts.get(chart_id)
        if not chart:
            raise ValueError(f"Chart '{chart_id}' not found")
        
        chart.series.append(series)
        self._save_charts()
        
        return series
    
    def remove_series(self, chart_id: str, series_name: str) -> bool:
        """Remove a data series from a chart"""
        chart = self.charts.get(chart_id)
        if not chart:
            raise ValueError(f"Chart '{chart_id}' not found")
        
        chart.series = [s for s in chart.series if s.name != series_name]
        self._save_charts()
        
        return True
    
    def apply_color_scheme(self, chart_id: str, scheme_name: str) -> ChartConfig:
        """Apply a predefined color scheme to a chart
        
        Args:
            chart_id: Chart ID
            scheme_name: Name of color scheme
        
        Returns:
            Updated ChartConfig
        """
        chart = self.charts.get(chart_id)
        if not chart:
            raise ValueError(f"Chart '{chart_id}' not found")
        
        colors = self.color_schemes.get(scheme_name, self.color_schemes['default'])
        
        for i, series in enumerate(chart.series):
            if i < len(colors):
                series.color = colors[i]
        
        self._save_charts()
        return chart
    
    def create_bar_chart(self, chart_id: str, title: str, 
                        category_key: str, value_keys: List[str],
                        **kwargs) -> ChartConfig:
        """Create a bar chart with simplified parameters"""
        x_axis = ChartAxis(title="Categories", data_key=category_key, 
                          scale_type="categorical")
        y_axis = ChartAxis(title="Values", data_key="", scale_type="linear")
        
        chart = self.create_chart(
            chart_id=chart_id,
            title=title,
            chart_type=ChartType.BAR,
            x_axis=x_axis,
            y_axis=y_axis,
            **kwargs
        )
        
        for key in value_keys:
            series = ChartSeries(name=key, data_key=key)
            self.add_series(chart_id, series)
        
        return chart
    
    def create_line_chart(self, chart_id: str, title: str,
                         time_key: str, value_keys: List[str],
                         **kwargs) -> ChartConfig:
        """Create a line chart with simplified parameters"""
        x_axis = ChartAxis(title="Time", data_key=time_key, scale_type="time")
        y_axis = ChartAxis(title="Values", data_key="", scale_type="linear")
        
        chart = self.create_chart(
            chart_id=chart_id,
            title=title,
            chart_type=ChartType.LINE,
            x_axis=x_axis,
            y_axis=y_axis,
            **kwargs
        )
        
        for key in value_keys:
            series = ChartSeries(name=key, data_key=key)
            self.add_series(chart_id, series)
        
        return chart
    
    def create_pie_chart(self, chart_id: str, title: str,
                        label_key: str, value_key: str,
                        **kwargs) -> ChartConfig:
        """Create a pie chart"""
        x_axis = ChartAxis(title="", data_key=label_key)
        
        chart = self.create_chart(
            chart_id=chart_id,
            title=title,
            chart_type=ChartType.PIE,
            x_axis=x_axis,
            **kwargs
        )
        
        series = ChartSeries(name="Value", data_key=value_key)
        self.add_series(chart_id, series)
        
        return chart
    
    def export_chart_config(self, chart_id: str, format: str = "json") -> str:
        """Export chart configuration"""
        chart = self.charts.get(chart_id)
        if not chart:
            raise ValueError(f"Chart '{chart_id}' not found")
        
        if format == "json":
            config_dict = {
                **asdict(chart),
                'chart_type': chart.chart_type.value,
                'theme': chart.theme.value,
                'x_axis': asdict(chart.x_axis),
                'y_axis': asdict(chart.y_axis) if chart.y_axis else None,
                'series': [asdict(s) for s in chart.series]
            }
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_chart(self, chart_id: str) -> Optional[ChartConfig]:
        """Get chart configuration by ID"""
        return self.charts.get(chart_id)
    
    def list_charts(self) -> List[str]:
        """List all chart IDs"""
        return list(self.charts.keys())
    
    def list_color_schemes(self) -> List[str]:
        """List available color schemes"""
        return list(self.color_schemes.keys())
    
    def get_chart_summary(self, chart_id: str) -> Dict[str, Any]:
        """Get summary information about a chart"""
        chart = self.charts.get(chart_id)
        if not chart:
            raise ValueError(f"Chart '{chart_id}' not found")
        
        return {
            'id': chart.id,
            'title': chart.title,
            'chart_type': chart.chart_type.value,
            'series_count': len(chart.series),
            'width': chart.width,
            'height': chart.height,
            'theme': chart.theme.value,
            'created_at': chart.created_at,
            'series_names': [s.name for s in chart.series]
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of chart factory"""
        return {
            'status': 'healthy',
            'charts_count': len(self.charts),
            'templates_count': len(self.chart_templates),
            'color_schemes': len(self.color_schemes),
            'storage_path': str(self.storage_path),
            'timestamp': datetime.now().isoformat()
        }


def get_chart_factory(config_path: Optional[str] = None) -> ChartFactory:
    """Factory function to get ChartFactory instance"""
    return ChartFactory(config_path)
