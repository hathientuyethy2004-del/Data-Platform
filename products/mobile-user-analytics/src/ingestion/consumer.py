from __future__ import annotations

from typing import Any, Dict, List

from src.ingestion.schema import MobileEvent


class MobileEventsConsumer:
    def __init__(self):
        self.processed_events: List[MobileEvent] = []

    def validate_event(self, payload: Dict[str, Any]) -> MobileEvent:
        return MobileEvent(**payload)

    def process_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = self.validate_event(payload)
        self.processed_events.append(event)
        return {
            "event_id": event.event_id,
            "status": "accepted",
            "event_type": event.event_type.value,
        }
