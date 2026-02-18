"""
Report Generator - Automated Report Creation and Scheduling

Provides:
- Report template management
- Scheduled report execution
- Multiple export formats
- Email distribution
- Report versioning
- Historical tracking
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats"""
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"
    CSV = "csv"
    JSON = "json"


class ReportSchedule(Enum):
    """Report scheduling options"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ReportSection:
    """Represents a section in a report"""
    id: str
    title: str
    content_type: str  # table, chart, text, metric
    query: str  # SQL or data query
    format_config: Dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass
class Report:
    """Represents a report"""
    name: str
    title: str
    description: str = ""
    sections: List[ReportSection] = field(default_factory=list)
    format: ReportFormat = ReportFormat.PDF
    schedule: ReportSchedule = ReportSchedule.ONCE
    schedule_time: str = ""  # HH:MM
    recipients: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_generated: Optional[str] = None
    owner: str = ""
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class ReportExecution:
    """Record of a report execution"""
    report_name: str
    execution_id: str
    status: str  # success, failed, in_progress
    started_at: str
    completed_at: Optional[str] = None
    output_path: str = ""
    error_message: str = ""
    duration_seconds: float = 0.0


class ReportGenerator:
    """Manages report creation and generation"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Report Generator
        
        Args:
            config_path: Path to configuration file
        """
        from ..configs.bi_config import get_bi_config
        self.config = get_bi_config(config_path)
        self.storage_path = Path(self.config.get('reports.storage', 'analytics_data/reports'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.reports: Dict[str, Report] = {}
        self.executions: List[ReportExecution] = []
        self.templates: Dict[str, Report] = {}
        
        self._load_reports()
    
    def _load_reports(self) -> None:
        """Load existing reports from storage"""
        reports_file = self.storage_path / 'reports.json'
        if reports_file.exists():
            try:
                with open(reports_file, 'r') as f:
                    data = json.load(f)
                    for report_data in data.get('reports', []):
                        sections = [
                            ReportSection(**section_data)
                            for section_data in report_data.get('sections', [])
                        ]
                        report_data['sections'] = sections
                        report_data['format'] = ReportFormat(report_data.get('format', 'pdf'))
                        report_data['schedule'] = ReportSchedule(report_data.get('schedule', 'once'))
                        report = Report(**report_data)
                        self.reports[report.name] = report
                    
                    # Load executions
                    for exec_data in data.get('executions', []):
                        execution = ReportExecution(**exec_data)
                        self.executions.append(execution)
            except Exception as e:
                logger.warning(f"Failed to load reports: {e}")
    
    def _save_reports(self) -> None:
        """Save reports to storage"""
        reports_file = self.storage_path / 'reports.json'
        data = {
            'version': self.config.get('version'),
            'timestamp': datetime.now().isoformat(),
            'reports': [
                {**asdict(report), 'sections': [asdict(s) for s in report.sections]}
                for report in self.reports.values()
            ],
            'executions': [asdict(exec) for exec in self.executions[-100:]]  # Keep last 100
        }
        try:
            with open(reports_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save reports: {e}")
    
    def create_report(self, name: str, title: str, 
                     description: str = "", owner: str = "") -> Report:
        """Create a new report
        
        Args:
            name: Unique report name
            title: Display title
            description: Report description
            owner: Report owner
        
        Returns:
            Created Report object
        """
        if name in self.reports:
            raise ValueError(f"Report '{name}' already exists")
        
        report = Report(
            name=name,
            title=title,
            description=description,
            owner=owner
        )
        
        self.reports[name] = report
        logger.info(f"Created report: {name}")
        self._save_reports()
        
        return report
    
    def add_section(self, report_name: str, section: ReportSection) -> ReportSection:
        """Add a section to a report
        
        Args:
            report_name: Report name
            section: Section to add
        
        Returns:
            Added ReportSection
        """
        report = self.reports.get(report_name)
        if not report:
            raise ValueError(f"Report '{report_name}' not found")
        
        # Auto-order if not set
        if section.order == 0:
            section.order = len(report.sections) + 1
        
        report.sections.append(section)
        report.updated_at = datetime.now().isoformat()
        
        logger.info(f"Added section '{section.id}' to report '{report_name}'")
        self._save_reports()
        
        return section
    
    def remove_section(self, report_name: str, section_id: str) -> bool:
        """Remove a section from a report"""
        report = self.reports.get(report_name)
        if not report:
            raise ValueError(f"Report '{report_name}' not found")
        
        report.sections = [s for s in report.sections if s.id != section_id]
        report.updated_at = datetime.now().isoformat()
        
        self._save_reports()
        return True
    
    def configure_scheduling(self, report_name: str, 
                            schedule: ReportSchedule,
                            schedule_time: str,
                            recipients: List[str]) -> Report:
        """Configure report scheduling
        
        Args:
            report_name: Report name
            schedule: Scheduling frequency
            schedule_time: Time in HH:MM format
            recipients: Email recipients
        
        Returns:
            Updated Report
        """
        report = self.reports.get(report_name)
        if not report:
            raise ValueError(f"Report '{report_name}' not found")
        
        report.schedule = schedule
        report.schedule_time = schedule_time
        report.recipients = recipients
        report.updated_at = datetime.now().isoformat()
        
        self._save_reports()
        return report
    
    def generate_report(self, report_name: str, 
                       format: Optional[ReportFormat] = None) -> str:
        """Generate a report
        
        Args:
            report_name: Report name
            format: Output format (uses report config if not specified)
        
        Returns:
            Path to generated report
        """
        report = self.reports.get(report_name)
        if not report:
            raise ValueError(f"Report '{report_name}' not found")
        
        execution_id = f"{report_name}_{datetime.now().timestamp()}"
        execution = ReportExecution(
            report_name=report_name,
            execution_id=execution_id,
            status="in_progress",
            started_at=datetime.now().isoformat()
        )
        
        try:
            # Generate report content
            format = format or report.format
            
            # Create output directory
            report_dir = self.storage_path / report_name
            report_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = report_dir / f"{report_name}_{timestamp}.{format.value}"
            
            # Process sections and generate content
            content = self._build_report_content(report, format)
            
            # Save report
            with open(output_file, 'w') as f:
                f.write(content)
            
            execution.status = "success"
            execution.output_path = str(output_file)
            execution.completed_at = datetime.now().isoformat()
            
            report.last_generated = execution.completed_at
            
            logger.info(f"Generated report: {report_name} -> {output_file}")
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.now().isoformat()
            logger.error(f"Failed to generate report {report_name}: {e}")
        
        self.executions.append(execution)
        self._save_reports()
        
        return execution.output_path
    
    def _build_report_content(self, report: Report, format: ReportFormat) -> str:
        """Build report content based on sections"""
        if format == ReportFormat.JSON:
            content = {
                'name': report.name,
                'title': report.title,
                'generated_at': datetime.now().isoformat(),
                'sections': [asdict(s) for s in report.sections]
            }
            return json.dumps(content, indent=2)
        elif format == ReportFormat.HTML:
            html = f"""
            <html>
            <head>
                <title>{report.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .section {{ margin-top: 30px; border-bottom: 1px solid #ccc; padding-bottom: 10px; }}
                    .section h2 {{ color: #666; }}
                </style>
            </head>
            <body>
                <h1>{report.title}</h1>
                <p>{report.description}</p>
                <p>Generated: {datetime.now().isoformat()}</p>
            """
            for section in sorted(report.sections, key=lambda s: s.order):
                html += f"""
                <div class="section">
                    <h2>{section.title}</h2>
                    <p>Type: {section.content_type}</p>
                </div>
                """
            html += "</body></html>"
            return html
        else:
            return json.dumps([asdict(s) for s in report.sections])
    
    def get_report(self, name: str) -> Optional[Report]:
        """Get report by name"""
        return self.reports.get(name)
    
    def list_reports(self) -> List[str]:
        """List all report names"""
        return list(self.reports.keys())
    
    def get_execution_history(self, report_name: str, 
                             limit: int = 10) -> List[ReportExecution]:
        """Get execution history for a report"""
        history = [e for e in self.executions if e.report_name == report_name]
        return sorted(history, key=lambda e: e.started_at, reverse=True)[:limit]
    
    def create_template(self, name: str, report: Report) -> Report:
        """Create a report template"""
        self.templates[name] = report
        logger.info(f"Created report template: {name}")
        return report
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of report generator"""
        return {
            'status': 'healthy',
            'reports_count': len(self.reports),
            'templates_count': len(self.templates),
            'total_sections': sum(len(r.sections) for r in self.reports.values()),
            'executions_recorded': len(self.executions),
            'storage_path': str(self.storage_path),
            'timestamp': datetime.now().isoformat()
        }


def get_report_generator(config_path: Optional[str] = None) -> ReportGenerator:
    """Factory function to get ReportGenerator instance"""
    return ReportGenerator(config_path)
