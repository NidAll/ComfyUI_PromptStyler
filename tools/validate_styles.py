import json
import os
import sys


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    packs_dir = os.path.join(root, "styles", "packs")

    data = {"styles": []}
    if os.path.isdir(packs_dir):
        for name in sorted(os.listdir(packs_dir)):
            if not name.lower().endswith(".json"):
                continue
            path = os.path.join(packs_dir, name)
            with open(path, "r", encoding="utf-8") as f:
                part = json.load(f) or {}
            data["styles"].extend(part.get("styles", []) or [])
    else:
        path = os.path.join(root, "styles", "styles_v1.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    styles = data.get("styles", [])
    if not isinstance(styles, list):
        print("ERROR: styles must be a list")
        return 2

    ids = set()
    names = set()
    ok = True
    for i, s in enumerate(styles):
        sid = s.get("id")
        name = s.get("name")
        if not sid or not name:
            print(f"ERROR: styles[{i}] missing id or name")
            ok = False
            continue
        if sid in ids:
            print(f"ERROR: duplicate id: {sid}")
            ok = False
        if name in names:
            print(f"ERROR: duplicate name: {name}")
            ok = False
        ids.add(sid)
        names.add(name)

        default = s.get("default", {})
        if not isinstance(default, dict):
            print(f"ERROR: styles[{i}].default must be an object")
            ok = False
            continue
        for k in ("prefix", "suffix"):
            if k not in default:
                print(f"ERROR: styles[{i}].default missing {k}")
                ok = False

    if not ok:
        return 2

    print(f"OK: {len(styles)} styles; {len(ids)} unique ids; {len(names)} unique names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
