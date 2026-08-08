import sys
from pathlib import Path

import yaml


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: set_image.py <rendered-yaml> <container-name> <image>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    container_name = sys.argv[2]
    image = sys.argv[3]
    docs = list(yaml.safe_load_all(read_text(path)))
    updated = False
    for doc in docs:
        if not doc or doc.get("kind") != "Deployment":
            continue
        containers = doc["spec"]["template"]["spec"].get("containers", [])
        for container in containers:
            if container.get("name") == container_name:
                container["image"] = image
                updated = True
    if not updated:
        print(f"container not found in Deployment: {container_name}", file=sys.stderr)
        return 1
    yaml.safe_dump_all(docs, sys.stdout, sort_keys=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
