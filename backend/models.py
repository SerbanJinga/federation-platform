"""Pydantic models. The ServiceDescriptor is the unit of integration from the
report, a small document a twin publishes when it registers."""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field as PField


class ServiceField(BaseModel):
    name: str
    type: str = "unknown"          # declared semantic type (may be refined by the ontology)


class ServiceDescriptor(BaseModel):
    name: str
    domain: str
    process: bool = False           # True for an orchestrator or process twin
    protocols: List[str] = PField(default_factory=lambda: ["REST"])
    fields: List[ServiceField] = PField(default_factory=list)
    data_url: Optional[str] = None  # direct runtime endpoint exposed by the twin


class FederateRequest(BaseModel):
    topology: str                   # centralized | hierarchical | distributed
    twin_ids: List[str]


class MappingApply(BaseModel):
    a_id: str
    a_field: str
    b_id: str
    b_field: str
