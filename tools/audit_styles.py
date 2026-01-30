import json
import os
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple


ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PACKS_DIR = os.path.join(ROOT, "styles", "packs")


def _iter_pack_paths() -> Iterable[str]:
    if not os.path.isdir(PACKS_DIR):
        return []
    for name in sorted(os.listdir(PACKS_DIR)):
        if name.lower().endswith(".json"):
            yield os.path.join(PACKS_DIR, name)


def _load_all_styles() -> Tuple[List[Dict[str, Any]], List[str]]:
    styles: List[Dict[str, Any]] = []
    bad_packs: List[str] = []
    for path in _iter_pack_paths():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception:
            bad_packs.append(path)
            continue
        styles.extend(data.get("styles", []) or [])
    return styles, bad_packs


def main() -> int:
    styles, bad_packs = _load_all_styles()

    if bad_packs:
        print("WARN: unable to read some packs:")
        for p in bad_packs:
            print(f"  - {p}")

    ids = [str(s.get("id", "")) for s in styles]
    names = [str(s.get("name", "")) for s in styles]
    cats = [str(s.get("category", "Uncategorized")) for s in styles]

    print(f"styles: {len(styles)}")
    print(f"packs: {len(list(_iter_pack_paths()))}")
    print("categories:")
    for c, n in Counter(cats).most_common():
        print(f"  {n:4d}  {c}")

    warnings: List[str] = []

    id_re = re.compile(r"^[a-z0-9_]+$")
    bad_ids = [sid for sid in ids if sid and not id_re.match(sid)]
    if bad_ids:
        warnings.append(f"bad_ids: {len(bad_ids)} (expected snake_case [a-z0-9_])")

    empty_prefix = 0
    empty_suffix = 0
    missing_default = 0
    missing_tags = 0
    missing_flux_2_klein = 0
    comma_without_space: List[Tuple[str, str]] = []
    comma_re = re.compile(r",(?!\s)")

    for s in styles:
        sid = str(s.get("id", ""))
        default = s.get("default", None)
        if not isinstance(default, dict):
            missing_default += 1
            continue

        prefix = str(default.get("prefix", "") or "")
        suffix = str(default.get("suffix", "") or "")
        if not prefix.strip():
            empty_prefix += 1
        if not suffix.strip():
            empty_suffix += 1

        for field, text in (("prefix", prefix), ("suffix", suffix)):
            if comma_re.search(text):
                comma_without_space.append((sid, field))

        tags = s.get("tags", None)
        if not isinstance(tags, list) or not any(str(t).strip() for t in tags):
            missing_tags += 1

        models = s.get("models", {})
        if not (isinstance(models, dict) and "flux_2_klein" in models):
            missing_flux_2_klein += 1

    if missing_default:
        warnings.append(f"missing_or_bad_default: {missing_default}")
    if empty_prefix:
        warnings.append(f"empty_prefix: {empty_prefix}")
    if empty_suffix:
        warnings.append(f"empty_suffix: {empty_suffix}")
    if comma_without_space:
        warnings.append(f"comma_without_space: {len(comma_without_space)} (node splits on ', ')")
    if missing_tags:
        warnings.append(f"missing_tags: {missing_tags}")
    if missing_flux_2_klein:
        warnings.append(f"missing_models.flux_2_klein: {missing_flux_2_klein}")

    # Quick uniqueness sanity (validate_styles.py is the source of truth).
    if len(set(ids)) != len(ids):
        warnings.append("duplicate_ids: detected")
    if len(set(names)) != len(names):
        warnings.append("duplicate_names: detected")

    if warnings:
        print("warnings:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("warnings: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

