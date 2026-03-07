import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from style_library import LOAD_POLICY_STRICT, StyleLibraryError, write_legacy_snapshot


def main() -> int:
    try:
        total = write_legacy_snapshot(load_policy=LOAD_POLICY_STRICT)
    except StyleLibraryError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"Updated styles/styles_v1.json with {total} merged styles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
