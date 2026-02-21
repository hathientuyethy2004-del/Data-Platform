from __future__ import annotations

import logging
from typing import Any, Dict, List

from .ports import IngestionPort, QualityPort, QueryRequest, QueryResult, ServingPort, ValidationReport

logger = logging.getLogger(__name__)


class LegacyIngestionAdapter(IngestionPort):
    def ingest_events(self, events: List[Dict[str, Any]]) -> int:
        logger.info("migration.path=legacy component=ingestion count=%s", len(events))
        return len(events)


class OSSIngestionAdapter(IngestionPort):
    def ingest_events(self, events: List[Dict[str, Any]]) -> int:
        logger.info("migration.path=oss component=ingestion count=%s", len(events))
        return len(events)


class LegacyQualityAdapter(QualityPort):
    def validate_events(self, events: List[Dict[str, Any]]) -> ValidationReport:
        logger.info("migration.path=legacy component=quality count=%s", len(events))
        return ValidationReport(is_valid=True, score=99.0, errors=[])


class OSSQualityAdapter(QualityPort):
    def validate_events(self, events: List[Dict[str, Any]]) -> ValidationReport:
        logger.info("migration.path=oss component=quality count=%s", len(events))
        return ValidationReport(is_valid=True, score=99.5, errors=[])


class LegacyServingAdapter(ServingPort):
    def execute_query(self, request: QueryRequest) -> QueryResult:
        logger.info("migration.path=legacy component=serving caller=%s", request.caller)
        return QueryResult(columns=[], rows=[], took_ms=0.0)


class OSSServingAdapter(ServingPort):
    def execute_query(self, request: QueryRequest) -> QueryResult:
        logger.info("migration.path=oss component=serving caller=%s", request.caller)
        return QueryResult(columns=[], rows=[], took_ms=0.0)
