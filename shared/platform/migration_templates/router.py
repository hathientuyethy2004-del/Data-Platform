from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Dict, List

from .adapters import (
    LegacyIngestionAdapter,
    LegacyQualityAdapter,
    LegacyServingAdapter,
    OSSIngestionAdapter,
    OSSQualityAdapter,
    OSSServingAdapter,
)
from .feature_flags import MigrationFlags
from .ports import IngestionPort, QualityPort, QueryRequest, QueryResult, ServingPort, ValidationReport

logger = logging.getLogger(__name__)


@dataclass
class MigrationRouter:
    flags: MigrationFlags
    ingestion: IngestionPort
    quality: QualityPort
    serving: ServingPort

    @classmethod
    def build(cls, flags: MigrationFlags) -> "MigrationRouter":
        ingestion = OSSIngestionAdapter() if flags.use_oss_ingestion else LegacyIngestionAdapter()
        quality = OSSQualityAdapter() if flags.use_oss_quality else LegacyQualityAdapter()
        serving = OSSServingAdapter() if (flags.use_oss_serving or flags.read_from_oss_serving) else LegacyServingAdapter()
        return cls(flags=flags, ingestion=ingestion, quality=quality, serving=serving)

    def process_events(self, events: List[Dict[str, Any]]) -> ValidationReport:
        if self.flags.dual_run_enabled:
            logger.info("migration.path=dual-run stage=ingestion count=%s", len(events))
            legacy_ingestion_count = LegacyIngestionAdapter().ingest_events(events)
            oss_ingestion_count = OSSIngestionAdapter().ingest_events(events)
            logger.info(
                "migration.path=dual-run stage=ingestion legacy_count=%s oss_count=%s",
                legacy_ingestion_count,
                oss_ingestion_count,
            )

            logger.info("migration.path=dual-run stage=quality count=%s", len(events))
            legacy_report = LegacyQualityAdapter().validate_events(events)
            oss_report = OSSQualityAdapter().validate_events(events)

            if self.flags.dual_run_compare_enabled:
                logger.info(
                    "migration.path=dual-run stage=quality compare is_valid_legacy=%s is_valid_oss=%s score_legacy=%.4f score_oss=%.4f",
                    legacy_report.is_valid,
                    oss_report.is_valid,
                    legacy_report.score,
                    oss_report.score,
                )

            return oss_report if self.flags.use_oss_quality else legacy_report

        _ = self.ingestion.ingest_events(events)
        return self.quality.validate_events(events)

    def run_query(self, sql: str, params: Dict[str, Any], caller: str) -> QueryResult:
        request = QueryRequest(sql=sql, params=params, caller=caller)

        if self.flags.dual_run_enabled:
            logger.info("migration.path=dual-run stage=serving caller=%s", caller)
            legacy_result = LegacyServingAdapter().execute_query(request)
            oss_result = OSSServingAdapter().execute_query(request)

            if self.flags.dual_run_compare_enabled:
                logger.info(
                    "migration.path=dual-run stage=serving compare rows_legacy=%s rows_oss=%s took_ms_legacy=%.4f took_ms_oss=%.4f",
                    len(legacy_result.rows),
                    len(oss_result.rows),
                    legacy_result.took_ms,
                    oss_result.took_ms,
                )

            return oss_result if self.flags.read_from_oss_serving else legacy_result

        return self.serving.execute_query(request)
