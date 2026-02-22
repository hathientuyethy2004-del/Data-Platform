from __future__ import annotations

from pydantic import BaseModel


class GovernanceIncident(BaseModel):
    id: str
    severity: str
    title: str
    status: str
    created_at: str
