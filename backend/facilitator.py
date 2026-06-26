"""
Core logic for the Federation Facilitator.

It wraps the knowledge graph and the ontology and exposes what the REST API
needs. It registers twins, establishes a federation, computes the peer map, and
aligns two twins semantically. It only handles setup. Once a federation exists,
twins talk to each other directly and the facilitator stays out of the data path.
"""
from __future__ import annotations
import itertools
from .knowledge_graph import KnowledgeGraph
from .ontology import canonical_type, unit_of

from typing import Optional

class Facilitator:
    def __init__(self) -> None:
        self.kg = KnowledgeGraph()
        self._counter = 0
        self.topology: Optional[str] = None

    def register(self, descriptor: dict) -> dict:
        # deduplicate by name so reregistering a mock twin is idempotent
        for t in self.kg.list_twins():
            if t["name"] == descriptor["name"]:
                self.kg.add_twin(t["id"], descriptor)
                return self.kg.get_twin(t["id"])
        self._counter += 1
        tid = f"t{self._counter}"
        self.kg.add_twin(tid, descriptor)
        return self.kg.get_twin(tid)

    def deregister(self, tid: str) -> None:
        self.kg.remove_twin(tid)
        self.topology = None  # any standing federation is now stale

    def twins(self) -> list[dict]:
        return self.kg.list_twins()

    def federate(self, topology: str, ids: list[str]) -> dict:
        self.topology = topology
        self.kg.set_federation(topology, ids)
        twins = {t["id"]: t for t in self.kg.list_twins() if t["id"] in ids}
        peers = self._peer_map(topology, ids, twins)
        return {
            "topology": topology,
            "peers": peers,
            "twins": [twins[i] for i in ids if i in twins],
        }

    def _peer_map(self, topology, ids, twins):
        """Direct runtime links the facilitator hands back to participants."""
        peers: dict[str, list[str]] = {i: [] for i in ids}
        proc = next((i for i in ids if twins.get(i, {}).get("process")), None)
        if topology == "distributed":
            for a, b in itertools.combinations(ids, 2):
                peers[a].append(b); peers[b].append(a)
        else:  # centralized or hierarchical, route through the process twin when there is one
            if proc:
                for i in ids:
                    if i != proc:
                        peers[proc].append(i); peers[i].append(proc)
            else:
                for a, b in zip(ids, ids[1:]):
                    peers[a].append(b); peers[b].append(a)
        return peers

    def alignment(self, a_id: str, b_id: str) -> dict:
        a = self.kg.get_twin(a_id); b = self.kg.get_twin(b_id)
        rows = []
        if a and b:
            for fa in a["fields"]:
                ca = canonical_type(fa["name"], fa.get("type"))
                fb = next((x for x in b["fields"]
                           if canonical_type(x["name"], x.get("type")) == ca), None)
                if fb:
                    exact = fa["name"] == fb["name"]
                    mapped = self.kg.has_mapping(a_id, fa["name"], b_id, fb["name"])
                    rows.append({
                        "a_field": fa["name"], "b_field": fb["name"],
                        "canonical": ca, "unit": unit_of(ca),
                        "exact": exact, "mapped": mapped,
                    })
        return {"a": a_id, "b": b_id,
                "a_name": a["name"] if a else "?", "b_name": b["name"] if b else "?",
                "rows": rows}

    def apply_mapping(self, m) -> None:
        self.kg.add_mapping(m.a_id, m.a_field, m.b_id, m.b_field)
