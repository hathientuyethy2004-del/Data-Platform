from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


@dataclass
class QueryRequest:
    sql: str
    params: Dict[str, Any]
    caller: str


@dataclass
class QueryResult:
    columns: List[str]
    rows: List[List[Any]]
    took_ms: float


@dataclass
class ValidationReport:
    is_valid: bool
    score: float
    errors: List[str]


class IngestionPort(Protocol):
    def ingest_events(self, events: List[Dict[str, Any]]) -> int:
        ...


class QualityPort(Protocol):
    def validate_events(self, events: List[Dict[str, Any]]) -> ValidationReport:
        ...


class ServingPort(Protocol):
    def execute_query(self, request: QueryRequest) -> QueryResult:
        ...
