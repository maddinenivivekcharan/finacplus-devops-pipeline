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
    if len(sys.argv) not in (4, 5):
        print("usage: set_image.py <rendered-yaml> <container-name> <image> [build-sha]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    container_name = sys.argv[2]
    image = sys.argv[3]
    build_sha = sys.argv[4] if len(sys.argv) == 5 else None
    docs = list(yaml.safe_load_all(read_text(path)))
    updated = False
    for doc in docs:
        if not doc or doc.get("kind") != "Deployment":
            continue
        containers = doc["spec"]["template"]["spec"].get("containers", [])
        for container in containers:
            if container.get("name") == container_name:
                container["image"] = image
                if build_sha:
                    env = container.setdefault("env", [])
                    for item in env:
                        if item.get("name") == "BUILD_SHA":
                            item.clear()
                            item.update({"name": "BUILD_SHA", "value": build_sha})
                            break
                    else:
                        env.append({"name": "BUILD_SHA", "value": build_sha})
                updated = True
    if not updated:
        print(f"container not found in Deployment: {container_name}", file=sys.stderr)
        return 1
    yaml.safe_dump_all(docs, sys.stdout, sort_keys=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
