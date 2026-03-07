import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
VERSION_PATH = os.path.join(ROOT, "VERSION")
INIT_PATH = os.path.join(ROOT, "__init__.py")
MANIFEST_PATH = os.path.join(ROOT, ".release-please-manifest.json")


def _read_version() -> str:
    with open(VERSION_PATH, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def _read_manifest_version() -> str:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle) or {}
    return str(data.get(".", "")).strip()


def _write_manifest_version(version: str) -> None:
    with open(MANIFEST_PATH, "w", encoding="utf-8") as handle:
        json.dump({".": version}, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def _init_reads_version_file() -> bool:
    with open(INIT_PATH, "r", encoding="utf-8") as handle:
        text = handle.read()
    return "_read_version()" in text and 'os.path.join(here, "VERSION")' in text


def cmd_check(_args) -> int:
    version = _read_version()
    manifest_version = _read_manifest_version()
    ok = True

    if not _init_reads_version_file():
        print("ERROR: __init__.py is no longer reading VERSION directly")
        ok = False

    if manifest_version != version:
        print(f"ERROR: .release-please-manifest.json ({manifest_version}) does not match VERSION ({version})")
        ok = False

    if not ok:
        return 2

    print(f"OK: VERSION, __init__.py, and .release-please-manifest.json are aligned at {version}")
    return 0


def cmd_write(_args) -> int:
    version = _read_version()
    _write_manifest_version(version)
    print(f"Updated .release-please-manifest.json -> {version}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="version_sync.py", description="Check or sync version metadata")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="Validate VERSION, __init__.py, and release manifest alignment")
    p_check.set_defaults(func=cmd_check)

    p_write = sub.add_parser("write", help="Write manifest version from VERSION")
    p_write.set_defaults(func=cmd_write)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
