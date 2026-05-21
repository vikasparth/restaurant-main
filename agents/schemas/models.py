from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel

class TimeWindow(BaseModel):
    from_: str
    to: str

AgentName = Literal["frontend-sentry", "backend-sentry", "render-logs", "github", "diagnostic", "coding"]
AgentStatus = Literal["completed", "partial", "failed", "injection_detected"]
ConfidenceLevel = Literal["high", "medium", "low"]

class Metadata(BaseModel):
    schema_version: Literal["1.0"]
    agent: AgentName
    status: AgentStatus
    source: str
    time_window: TimeWindow
    confidence: ConfidenceLevel
    pii_flag: bool
    injection_flag: bool
    findings_count: int
    runbook_match: Optional[str] = None
    release_id: Optional[str] = None
    release_id_unresolvable: bool = False

AffectedLayer = Literal["frontend", "backend", "gateway", "infrastructure", "unknown"]

class Interpretation(BaseModel):
    root_cause: str
    affected_layer: AffectedLayer
    regression: bool

class BaseFinding(BaseModel):
    metadata: Metadata
    interpretation: Interpretation

class FrontendSentryData(BaseModel):
    error_type: str
    error_message: str
    affected_file: str
    line_number: Optional[int] = None
    affected_field: Optional[str] = None
    graphql_mutation: Optional[str] = None
    affected_user_count: Optional[int] = None
    first_seen: str
    last_seen: str

class FrontendSentryFinding(BaseFinding):
    findings: FrontendSentryData 
