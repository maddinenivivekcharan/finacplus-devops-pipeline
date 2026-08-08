import sys
from pathlib import Path

import yaml


CLUSTER_SCOPED_KINDS = {
    "ClusterRole",
    "ClusterRoleBinding",
    "CustomResourceDefinition",
    "Namespace",
    "Node",
    "PersistentVolume",
    "StorageClass",
}


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: set_namespace.py <rendered-yaml> <namespace>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    namespace = sys.argv[2]
    docs = list(yaml.safe_load_all(read_text(path)))
    for doc in docs:
        if not doc:
            continue
        metadata = doc.setdefault("metadata", {})
        if doc.get("kind") == "Namespace":
            metadata["name"] = namespace
        elif doc.get("kind") not in CLUSTER_SCOPED_KINDS:
            metadata["namespace"] = namespace
    yaml.safe_dump_all(docs, sys.stdout, sort_keys=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
