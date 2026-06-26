"""
RDFLib backed knowledge graph for the Federation Facilitator (report FR2).

Stores every registered twin, its services, and the relationships and mappings
created during federation as RDF triples. Each twin also keeps its descriptor as
a JSON literal so the registry can be rebuilt exactly, while the structured
triples stay queryable through the /api/graph endpoint.
"""
from __future__ import annotations
import json
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS

DT = Namespace("http://tue.nl/asif#")


class KnowledgeGraph:
    def __init__(self) -> None:
        self.g = Graph()
        self.g.bind("dt", DT)
        self.g.bind("rdfs", RDFS)

    def twin_uri(self, tid: str) -> URIRef:
        return URIRef(DT[f"twin/{tid}"])

    def svc_uri(self, tid: str, field: str) -> URIRef:
        return URIRef(DT[f"twin/{tid}/svc/{field}"])

    def add_twin(self, tid: str, descriptor: dict) -> None:
        self.remove_twin(tid)  # idempotent reregistration
        t = self.twin_uri(tid)
        self.g.add((t, RDF.type, DT.DigitalTwin))
        self.g.add((t, DT.id, Literal(tid)))
        self.g.add((t, RDFS.label, Literal(descriptor["name"])))
        self.g.add((t, DT.domain, Literal(descriptor["domain"])))
        self.g.add((t, DT.isProcess, Literal(bool(descriptor.get("process", False)))))
        if descriptor.get("data_url"):
            self.g.add((t, DT.dataUrl, Literal(descriptor["data_url"])))
        for p in descriptor.get("protocols", []):
            self.g.add((t, DT.protocol, Literal(p)))
        for f in descriptor.get("fields", []):
            s = self.svc_uri(tid, f["name"])
            self.g.add((t, DT.hasService, s))
            self.g.add((s, RDF.type, DT.Service))
            self.g.add((s, DT.fieldName, Literal(f["name"])))
            self.g.add((s, DT.semanticType, Literal(f.get("type", "unknown"))))
        # keep the raw descriptor so the registry rebuilds in order
        self.g.add((t, DT.descriptorJSON, Literal(json.dumps(descriptor))))

    def remove_twin(self, tid: str) -> None:
        t = self.twin_uri(tid)
        # drop the twin's service nodes first
        for s in list(self.g.objects(t, DT.hasService)):
            for trip in list(self.g.triples((s, None, None))):
                self.g.remove(trip)
        # then every triple where the twin is subject or object
        for trip in list(self.g.triples((t, None, None))):
            self.g.remove(trip)
        for trip in list(self.g.triples((None, None, t))):
            self.g.remove(trip)

    def get_twin(self, tid: str) -> dict | None:
        t = self.twin_uri(tid)
        raw = self.g.value(t, DT.descriptorJSON)
        if raw is None:
            return None
        d = json.loads(str(raw))
        d["id"] = tid
        return d

    def list_twins(self) -> list[dict]:
        out = []
        for t in self.g.subjects(RDF.type, DT.DigitalTwin):
            tid = str(self.g.value(t, DT.id))
            d = self.get_twin(tid)
            if d:
                out.append(d)
        # stable order by numeric id suffix
        out.sort(key=lambda d: int("".join(ch for ch in d["id"] if ch.isdigit()) or 0))
        return out

    def set_federation(self, topology: str, ids: list[str]) -> None:
        # clear any previous federation triples
        for trip in list(self.g.triples((None, DT.federatedWith, None))):
            self.g.remove(trip)
        for trip in list(self.g.triples((None, DT.topology, None))):
            self.g.remove(trip)
        fed = URIRef(DT["federation/current"])
        for trip in list(self.g.triples((fed, None, None))):
            self.g.remove(trip)
        self.g.add((fed, RDF.type, DT.Federation))
        self.g.add((fed, DT.topology, Literal(topology)))
        for tid in ids:
            self.g.add((fed, DT.member, self.twin_uri(tid)))
        # pairwise relationship for queryability
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                self.g.add((self.twin_uri(ids[i]), DT.federatedWith, self.twin_uri(ids[j])))

    def add_mapping(self, a_id: str, a_field: str, b_id: str, b_field: str) -> None:
        self.g.add((self.svc_uri(a_id, a_field), DT.mapsTo, self.svc_uri(b_id, b_field)))

    def has_mapping(self, a_id: str, a_field: str, b_id: str, b_field: str) -> bool:
        return (self.svc_uri(a_id, a_field), DT.mapsTo, self.svc_uri(b_id, b_field)) in self.g

    def triples_dump(self) -> list[list[str]]:
        def short(term):
            s = str(term)
            return s.replace(str(DT), "dt:").replace(str(RDF), "rdf:").replace(str(RDFS), "rdfs:")
        return [[short(s), short(p), short(o)] for s, p, o in self.g
                if p != DT.descriptorJSON]  # hide the bulky JSON literal
