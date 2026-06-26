"""
Federation Facilitator REST API and the connection interface. It also serves the
operator GUI from the frontend folder.
"""
from __future__ import annotations
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import ServiceDescriptor, FederateRequest, MappingApply
from .facilitator import Facilitator
from .ontology import ONTOLOGY

app = FastAPI(title="DT Federation Facilitator", version="1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

fac = Facilitator()
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

# Demo twins behind the "Load ASIF PoC scenario" button. They mirror the twins
# the mock host registers on startup, so the button stays idempotent.
MOCK_HOST = os.environ.get("MOCK_HOST", "http://localhost:8101")
DEMO_TWINS = [
    {"name": "Farm DT", "domain": "Agriculture", "process": False,
     "protocols": ["REST", "MQTT"],
     "fields": [{"name": "temp_C", "type": "temperature"},
                {"name": "soil", "type": "soil_moisture"},
                {"name": "inventory", "type": "inventory"}],
     "data_url": f"{MOCK_HOST}/farm/data"},
    {"name": "Machine DT", "domain": "Manufacturing", "process": False,
     "protocols": ["OPC UA", "MQTT"],
     "fields": [{"name": "temperature", "type": "temperature"},
                {"name": "vol_flow", "type": "flow"},
                {"name": "quality", "type": "quality"}],
     "data_url": f"{MOCK_HOST}/machine/data"},
    {"name": "Process DT", "domain": "Process", "process": True,
     "protocols": ["REST"],
     "fields": [{"name": "capacity", "type": "yield"},
                {"name": "schedule_ok", "type": "quality"}],
     "data_url": f"{MOCK_HOST}/process/data"},
]


@app.get("/api/ontology")
def get_ontology():
    return {"types": ONTOLOGY}


@app.get("/api/twins")
def list_twins():
    return fac.twins()


@app.post("/api/twins")
def register_twin(desc: ServiceDescriptor):
    return fac.register(desc.model_dump())


@app.delete("/api/twins/{tid}")
def delete_twin(tid: str):
    fac.deregister(tid)
    return {"ok": True, "id": tid}


@app.post("/api/demo/seed")
def seed_demo():
    """Idempotently (re)register the ASIF proof of concept twins."""
    for d in DEMO_TWINS:
        fac.register(d)
    return fac.twins()


@app.post("/api/federate")
def federate(req: FederateRequest):
    if len(req.twin_ids) < 2:
        raise HTTPException(400, "need at least two twins to federate")
    return fac.federate(req.topology, req.twin_ids)


@app.get("/api/mapping")
def mapping(a: str, b: str):
    return fac.alignment(a, b)


@app.post("/api/mapping/apply")
def mapping_apply(m: MappingApply):
    fac.apply_mapping(m)
    return {"ok": True}


@app.get("/api/graph")
def graph_dump():
    triples = fac.kg.triples_dump()
    return {"count": len(triples), "triples": triples}


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


if (FRONTEND).exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")
