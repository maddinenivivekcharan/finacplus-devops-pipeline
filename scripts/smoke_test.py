import json
import os
import subprocess
import sys
import time
import urllib.request


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env.setdefault("APP_ENV", "smoke")
    proc = subprocess.Popen(
        [sys.executable, "-m", "flask", "--app", "finacplus_pipeline.app:app", "run", "--host", "127.0.0.1", "--port", "8081"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                with urllib.request.urlopen("http://127.0.0.1:8081/healthz", timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if payload == {"status": "ok"}:
                    print("Smoke test passed")
                    return 0
            except Exception:
                time.sleep(0.5)
        print("Smoke test failed: /healthz did not become healthy")
        return 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
