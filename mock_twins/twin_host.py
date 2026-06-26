"""
Mock twin host.

It hosts the three twins from the ASIF proof of concept (Farm, Machine, and
Process), each with its own service descriptor and its own direct data endpoint.
On startup each twin registers with the facilitator through the connector SDK and
then emits synthetic data over a REST endpoint that the monitoring view polls
directly. That is the direct runtime link.

The facilitator URL and this host's public URL come from the environment
(FACILITATOR_URL and MOCK_HOST) so run.py can wire everything together.
"""
from __future__ import annotations
import os
import random
import threading
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from connector_sdk import Connector

FACILITATOR_URL = os.environ.get("FACILITATOR_URL", "http://localhost:8000")
MOCK_HOST = os.environ.get("MOCK_HOST", "http://localhost:8101")

# Each twin has a path, a descriptor, and seeded field values. The Farm twin's
# temp_C against the Machine twin's temperature is the deliberate mismatch that
# exercises the semantic mapping step.
TWINS = {
    "farm": {
        "descriptor": {
            "name": "Farm DT", "domain": "Agriculture", "process": False,
            "protocols": ["REST", "MQTT"],
            "fields": [{"name": "temp_C", "type": "temperature"},
                       {"name": "soil", "type": "soil_moisture"},
                       {"name": "inventory", "type": "inventory"}],
            "data_url": f"{MOCK_HOST}/farm/data",
        },
        "values": {"temp_C": 21.0, "soil": 42.0, "inventory": 320.0},
    },
    "machine": {
        "descriptor": {
            "name": "Machine DT", "domain": "Manufacturing", "process": False,
            "protocols": ["OPC UA", "MQTT"],
            "fields": [{"name": "temperature", "type": "temperature"},
                       {"name": "vol_flow", "type": "flow"},
                       {"name": "quality", "type": "quality"}],
            "data_url": f"{MOCK_HOST}/machine/data",
        },
        "values": {"temperature": 19.5, "vol_flow": 12.0, "quality": 97.0},
    },
    "process": {
        "descriptor": {
            "name": "Process DT", "domain": "Process", "process": True,
            "protocols": ["REST"],
            "fields": [{"name": "capacity", "type": "yield"},
                       {"name": "schedule_ok", "type": "quality"}],
            "data_url": f"{MOCK_HOST}/process/data",
        },
        "values": {"capacity": 48.0, "schedule_ok": 99.0},
    },
}

app = FastAPI(title="Mock Twin Host")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


def _stream():
    """Random walk the synthetic values once per second."""
    while True:
        for cfg in TWINS.values():
            for k, v in cfg["values"].items():
                drift = (random.random() - 0.5) * (abs(v) * 0.04 + 0.6)
                cfg["values"][k] = max(0.0, round(v + drift, 2))
        time.sleep(1.0)


@app.on_event("startup")
def startup():
    # register each twin with the facilitator in the background
    def _register():
        for path, cfg in TWINS.items():
            try:
                tid = Connector(FACILITATOR_URL, cfg["descriptor"]).register()
                print(f"[mock] registered {cfg['descriptor']['name']} as {tid}")
            except Exception as e:
                print(f"[mock] registration failed for {path}: {e}")
    threading.Thread(target=_register, daemon=True).start()
    threading.Thread(target=_stream, daemon=True).start()


@app.get("/{path}/data")
def data(path: str):
    cfg = TWINS.get(path)
    return cfg["values"] if cfg else {}


@app.get("/{path}/descriptor")
def descriptor(path: str):
    cfg = TWINS.get(path)
    return cfg["descriptor"] if cfg else {}
