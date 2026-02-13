"""
Audit Logger for AUTOFORGE

Captures per-phase execution details and emits audit_report.json.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


@dataclass
class PhaseRecord:
    phase_id: int
    phase_name: str
    status: str
    timestamp_start: str
    timestamp_end: Optional[str] = None
    duration_ms: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """Structured audit logger for pipeline runs."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.trace_id = f"TRACE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.timestamp_start = datetime.now(timezone.utc).isoformat()
        self.timestamp_end = None
        self.phases: List[PhaseRecord] = []
        self.final_status = "UNKNOWN"
        self.total_attempts = 0
        self.compliance_summary: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        self.requirement_traceability: Dict[str, Any] = {}

    def start_phase(self, phase_id: int, phase_name: str) -> PhaseRecord:
        record = PhaseRecord(
            phase_id=phase_id,
            phase_name=phase_name,
            status="RUNNING",
            timestamp_start=datetime.now(timezone.utc).isoformat(),
        )
        self.phases.append(record)
        return record

    def end_phase(self, record: PhaseRecord, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        record.status = status
        record.timestamp_end = datetime.now(timezone.utc).isoformat()
        record.duration_ms = _duration_ms(record.timestamp_start, record.timestamp_end)
        if details:
            record.details.update(details)

    def finalize(
        self,
        final_status: str,
        total_attempts: int,
        compliance_summary: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        requirement_traceability: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.final_status = final_status
        self.total_attempts = total_attempts
        self.timestamp_end = datetime.now(timezone.utc).isoformat()
        if compliance_summary:
            self.compliance_summary = compliance_summary
        if outputs:
            self.outputs = outputs
        if requirement_traceability:
            self.requirement_traceability = requirement_traceability

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_report": {
                "trace_id": self.trace_id,
                "service_name": self.service_name,
                "timestamp_start": self.timestamp_start,
                "timestamp_end": self.timestamp_end,
                "final_status": self.final_status,
                "total_attempts": self.total_attempts,
                "phases": [
                    {
                        "phase_id": p.phase_id,
                        "phase_name": p.phase_name,
                        "status": p.status,
                        "timestamp_start": p.timestamp_start,
                        "timestamp_end": p.timestamp_end,
                        "duration_ms": p.duration_ms,
                        "details": p.details,
                    }
                    for p in self.phases
                ],
                "compliance_summary": self.compliance_summary,
                "outputs": self.outputs,
                "requirement_traceability": self.requirement_traceability,
            }
        }

    def save(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_dict(), indent=2))


def _duration_ms(start_iso: str, end_iso: str) -> int:
    start_ts = datetime.fromisoformat(start_iso).timestamp()
    end_ts = datetime.fromisoformat(end_iso).timestamp()
    return int((end_ts - start_ts) * 1000)
