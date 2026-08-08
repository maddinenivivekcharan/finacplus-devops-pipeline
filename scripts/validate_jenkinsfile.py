import re
import sys
from pathlib import Path


REQUIRED_STAGES = [
    "Validate Parameters",
    "Checkout",
    "Install and Test",
    "Validate Configuration",
    "Build Image",
    "Push Image",
    "Deploy to Kubernetes",
]


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "Jenkinsfile")
    text = path.read_text(encoding="utf-8")
    missing = [stage for stage in REQUIRED_STAGES if f"stage('{stage}')" not in text]
    checks = {
        "uses credentials binding": "withCredentials" in text,
        "has Kubernetes rollout verification": "rollout status" in text,
        "has parameterized overlay": "KUSTOMIZE_OVERLAY" in text,
        "has guarded deploy": "DEPLOY_TO_K8S" in text,
        "has guarded image push": "PUSH_IMAGE" in text,
        "prevents deploy without push": "DEPLOY_TO_K8S requires PUSH_IMAGE=true" in text,
        "has post failure feedback": "post {" in text and "failure {" in text,
    }
    failed = missing + [name for name, ok in checks.items() if not ok]
    if failed:
        for item in failed:
            print(f"FAILED: {item}")
        return 1
    if not re.search(r"timeout\(time:\s*\d+", text):
        print("FAILED: missing pipeline timeout")
        return 1
    print("Jenkinsfile static validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
