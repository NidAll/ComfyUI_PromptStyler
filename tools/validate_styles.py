import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from style_library import LOAD_POLICY_STRICT, StyleLibraryError, load_style_library


def main() -> int:
    try:
        library = load_style_library(load_policy=LOAD_POLICY_STRICT)
    except StyleLibraryError as exc:
        print(f"ERROR: {exc}")
        return 2

    ids = set()
    names = set()
    ok = True
    for style in library.styles:
        if style.id in ids:
            print(f"ERROR: duplicate id: {style.id}")
            ok = False
        if style.name in names:
            print(f"ERROR: duplicate name: {style.name}")
            ok = False
        ids.add(style.id)
        names.add(style.name)

    if not ok:
        return 2

    print(f"OK: {len(library.styles)} styles; {len(ids)} unique ids; {len(names)} unique names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
