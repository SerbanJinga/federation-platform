"""
Launcher for the whole system. Run it with python run.py.

It starts the Federation Facilitator and operator GUI on http://localhost:8000,
and the mock twin host on http://localhost:8101 whose twins register themselves.

Open http://localhost:8000 in a browser. Ctrl+C stops everything.
"""
import os
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
FAC_PORT = os.environ.get("FAC_PORT", "8000")
MOCK_PORT = os.environ.get("MOCK_PORT", "8101")
FAC_URL = f"http://localhost:{FAC_PORT}"
MOCK_URL = f"http://localhost:{MOCK_PORT}"

env = dict(os.environ)
env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
env["FACILITATOR_URL"] = FAC_URL
env["MOCK_HOST"] = MOCK_URL

procs = []


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", int(port))) == 0


def start(name, module, port):
    # start_new_session puts each child in its own process group so shutdown
    # can kill the whole tree (uvicorn workers included) and never orphan it.
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", module, "--host", "127.0.0.1",
         "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=env, start_new_session=True,
    )
    procs.append((name, p))
    return p


def shutdown(*_):
    print("\nShutting down...")
    for name, p in procs:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            p.terminate()
    for name, p in procs:
        try:
            p.wait(timeout=5)
        except Exception:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                p.kill()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    busy = [p for p in (FAC_PORT, MOCK_PORT) if port_in_use(p)]
    if busy:
        print(f"Ports already in use: {', '.join(busy)}.")
        print("Another run is probably still alive. Free them with:")
        print(f"    lsof -ti tcp:{FAC_PORT},tcp:{MOCK_PORT} | xargs kill")
        print("or set FAC_PORT / MOCK_PORT to different values, then retry.")
        sys.exit(1)

    print("Starting Federation Facilitator + operator GUI ...")
    start("facilitator", "backend.main:app", FAC_PORT)
    time.sleep(2.0)
    print("Starting mock twin host (twins register themselves) ...")
    start("mock twins", "mock_twins.twin_host:app", MOCK_PORT)
    time.sleep(2.0)

    print("\n" + "=" * 56)
    print(f"  Operator GUI:        {FAC_URL}")
    print(f"  Facilitator API:     {FAC_URL}/api/twins")
    print(f"  Knowledge graph:     {FAC_URL}/api/graph")
    print(f"  Mock twin host:      {MOCK_URL}")
    print("=" * 56)
    print("  Open the Operator GUI in your browser. Ctrl+C to stop.\n")

    # stay alive and report if either child crashes
    while True:
        for name, p in procs:
            if p.poll() is not None:
                print(f"[{name}] exited with code {p.returncode}")
                shutdown()
        time.sleep(1.0)
