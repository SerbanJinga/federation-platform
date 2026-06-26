"""
Connector SDK, the thin client a twin owner embeds.

It implements ASIF's Local Connector Service and the registration handshake. A
twin creates a Connector with the facilitator URL and its service descriptor and
then calls register, which does four things.

    1. register a new instance at the facilitator
    2. publish the service descriptor (data, services, protocols)
    3. open a logical connection to the facilitator
    4. wait for interoperability commands

After setup the twin serves its data directly at the descriptor data_url and the
facilitator stays out of the runtime path.
"""
from __future__ import annotations
import time
import requests


class Connector:
    def __init__(self, facilitator_url: str, descriptor: dict) -> None:
        self.facilitator_url = facilitator_url.rstrip("/")
        self.descriptor = descriptor
        self.twin_id: str | None = None

    def register(self, retries: int = 30, delay: float = 1.0) -> str:
        """Steps 1 to 3 of the handshake, with retry so a twin can start before
        the facilitator is up."""
        last_err = None
        for _ in range(retries):
            try:
                r = requests.post(f"{self.facilitator_url}/api/twins",
                                  json=self.descriptor, timeout=4)
                r.raise_for_status()
                self.twin_id = r.json()["id"]
                return self.twin_id
            except Exception as e:  # facilitator not ready yet
                last_err = e
                time.sleep(delay)
        raise RuntimeError(f"could not register with facilitator: {last_err}")
