from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
K8S_ROOT = ROOT / "k8s"


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return [doc for doc in yaml.safe_load_all(handle) if doc]


def assert_true(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def main() -> int:
    base_kustomization = load_yaml(K8S_ROOT / "base" / "kustomization.yaml")[0]
    assert_true(base_kustomization.get("namespace") == "finacplus-devops", "base kustomization namespace missing")

    docs = []
    for path in sorted(K8S_ROOT.rglob("*.yaml")):
        docs.extend((path, doc) for doc in load_yaml(path))

    kinds = {doc.get("kind") for _, doc in docs}
    required = {"Deployment", "Service", "HorizontalPodAutoscaler", "NetworkPolicy", "ServiceAccount"}
    assert_true(required.issubset(kinds), f"missing Kubernetes kinds: {sorted(required - kinds)}")

    deployments = [
        doc for _, doc in docs
        if doc.get("kind") == "Deployment" and "template" in doc.get("spec", {})
    ]
    assert_true(deployments, "missing Deployment")
    for deployment in deployments:
        pod_spec = deployment["spec"]["template"]["spec"]
        container = pod_spec["containers"][0]
        security = container.get("securityContext", {})
        assert_true(container.get("readinessProbe"), "Deployment missing readinessProbe")
        assert_true(container.get("livenessProbe"), "Deployment missing livenessProbe")
        assert_true(security.get("allowPrivilegeEscalation") is False, "container can escalate privileges")
        assert_true(security.get("runAsNonRoot") is True, "container must run as non-root")
        assert_true(security.get("runAsUser") == 10001, "container must use numeric non-root UID")
        assert_true(security.get("runAsGroup") == 10001, "container must use numeric non-root GID")
        assert_true("requests" in container.get("resources", {}), "resources.requests missing")
        assert_true("limits" in container.get("resources", {}), "resources.limits missing")

    print(f"Kubernetes manifest validation passed ({len(docs)} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
