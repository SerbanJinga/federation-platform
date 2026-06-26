# DT Federation Platform

A small web app that shows service level Digital Twin federation in action,
following the Abstract Service Level Interoperability Framework (ASIF). It is the
system described in the seminar report. You get a Federation Facilitator, a
knowledge graph, a connector SDK, a handful of mock twins, and an operator GUI.

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

Open http://localhost:8000 in your browser. Ctrl+C stops everything.

`run.py` starts two processes.

* The Federation Facilitator together with the operator GUI on http://localhost:8000
* The mock twin host on http://localhost:8101. Its three twins (Farm, Machine,
  and Process) register themselves with the facilitator on startup through the
  connector SDK.

## What you can do in the GUI

1. Registry. See the twins that registered through their connectors, then add or
   remove your own.
2. Federation. Pick a coordination topology (centralized, hierarchical, or
   distributed) and establish the federation. The facilitator records the
   relationships and hands back the direct runtime peer map, and the graph
   animates the direct links.
3. Semantic Mapping. The facilitator notices that the Farm twin's temp_C and the
   Machine twin's temperature mean the same ontology concept, flags the name
   mismatch, and lets you apply the suggested mapping. The mapping is recorded in
   the knowledge graph.
4. Dashboard. An external monitoring view that streams each twin's data straight
   from its endpoint, once per second.

## How it maps to the report

* Operator GUI (frontend) lives in frontend/index.html
* Federation Facilitator (backend) lives in backend/main.py and backend/facilitator.py
* The connection interface is the REST API in backend/main.py
* Knowledge graph (RDF) lives in backend/knowledge_graph.py, built on RDFLib
* Toolbox and ontology live in backend/ontology.py
* Local Connector Service and SDK live in connector_sdk/connector.py
* Mock twin services live in mock_twins/twin_host.py
* Service descriptor lives in backend/models.py as ServiceDescriptor

## API (Federation Facilitator)

* GET /api/twins lists the registered twins
* POST /api/twins registers a twin from a descriptor (FR1)
* DELETE /api/twins/{id} deregisters a twin
* POST /api/demo/seed registers the ASIF PoC twins again
* POST /api/federate establishes a federation and returns the peer map (FR3, FR5)
* GET /api/mapping?a=&b= returns the semantic alignment between two twins (FR4)
* POST /api/mapping/apply records a mapping in the knowledge graph
* GET /api/graph dumps the knowledge graph triples (FR2)
* GET /api/ontology returns the semantic type toolbox

## Project layout

```
federation-platform/
  run.py                 one command launcher
  requirements.txt
  backend/
    main.py              REST API and connection interface, serves the GUI
    facilitator.py       federation and mapping logic
    knowledge_graph.py   RDFLib triple store
    ontology.py          semantic types and toolbox
    models.py            service descriptor and request models
  connector_sdk/
    connector.py         thin client a twin embeds (registration handshake)
  mock_twins/
    twin_host.py         Farm, Machine, Process mock twins and synthetic streams
  frontend/
    index.html           operator GUI (single page app)
```

## Notes and next steps

* The mock twins stand in for real ones. The connector SDK is the same handshake
  a real twin would use, so you can swap the mock host for real connectors and
  nothing else changes.
* Security (FR7, authentication and access control) is designed but not wired in
  yet.
* The knowledge graph lives in memory. Point RDFLib at a persistent store or
  Neo4j if you need it to survive restarts.
* The dashboard polls twin endpoints over REST. You can add MQTT streaming behind
  the same descriptor data_url mechanism.
</content>
</invoke>
