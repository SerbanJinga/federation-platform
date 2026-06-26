"""
Ontology and semantic toolbox for the Federation Facilitator.

A small ontology of semantic types, each with a canonical unit and a list of
name aliases. The facilitator uses it to reconcile field level differences
between heterogeneous twins (ASIF R6, report FR4).
"""

ONTOLOGY = {
    "temperature":   {"unit": "\u00b0C",  "aliases": ["temp", "temp_c", "temperature_celsius", "t"]},
    "humidity":      {"unit": "%",        "aliases": ["humid", "rh", "moisture"]},
    "soil_moisture": {"unit": "%",        "aliases": ["soil", "soilmoisture"]},
    "flow":          {"unit": "L/min",    "aliases": ["volumetric_flow", "flowrate", "vol_flow"]},
    "pressure":      {"unit": "bar",      "aliases": ["press", "p"]},
    "inventory":     {"unit": "units",    "aliases": ["stock", "count"]},
    "quality":       {"unit": "%",        "aliases": ["q", "grade"]},
    "yield":         {"unit": "kg",       "aliases": ["production", "output", "capacity"]},
}


def canonical_type(field_name: str, declared: str | None = None) -> str:
    """Resolve a field to a canonical semantic type, using the declared type
    first and falling back to alias matching on the field name."""
    if declared and declared in ONTOLOGY:
        return declared
    low = (field_name or "").lower()
    for ty, meta in ONTOLOGY.items():
        if ty in low or any(a in low for a in meta["aliases"]):
            return ty
    return declared or "unknown"


def unit_of(semantic_type: str) -> str:
    return ONTOLOGY.get(semantic_type, {}).get("unit", "")
