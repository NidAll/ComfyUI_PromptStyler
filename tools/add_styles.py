"""
PromptStyler style pack tool.

This script helps you add more styles without editing python source by hand.
It writes (or updates) a JSON pack under styles/packs/, e.g.:
  styles/packs/99_user_custom.json

Usage examples:

  # List categories that exist (including ones supported by the generator)
  C:\\Comfyui\\python_embeded\\python.exe .\\tools\\add_styles.py categories

  # Add one style (core -> goes into prefix, details -> goes into suffix)
  C:\\Comfyui\\python_embeded\\python.exe .\\tools\\add_styles.py add ^
    --name "Anime Style (Soft Shading)" ^
    --category "Anime/Manga" ^
    --core "soft cel shading, warm palette, gentle gradients" ^
    --details "clean line weight, subtle texture, high clarity" ^
    --tags "anime, manga, illustration"

  # Bulk add from CSV (columns: name,category,core,details,tags)
  C:\\Comfyui\\python_embeded\\python.exe .\\tools\\add_styles.py bulk --csv .\\tools\\new_styles.csv
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PACKS_DIR = os.path.join(ROOT, "styles", "packs")
DEFAULT_PACK_PATH = os.path.join(PACKS_DIR, "99_user_custom.json")


def _load_generator_module():
    """
    Import tools/generate_style_packs.py as a module so we can reuse:
      - CATEGORY_BASE_PREFIX / CATEGORY_BASE_SUFFIX
      - z_join() (which de-dupes)
    """
    path = os.path.join(ROOT, "tools", "generate_style_packs.py")
    spec = importlib.util.spec_from_file_location("promptstyler_generate_style_packs", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import generator module: {path}")
    mod = importlib.util.module_from_spec(spec)
    # dataclasses (on some Python versions) expects the module to already exist in sys.modules
    # when evaluating annotations. Insert before exec_module to avoid NoneType errors.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _slugify(name: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in (name or "")).strip("_")
    while "__" in base:
        base = base.replace("__", "_")
    return base or "style"


def _split_csv_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f) or {}


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def _iter_pack_paths() -> Iterable[str]:
    if not os.path.isdir(PACKS_DIR):
        return []
    for name in sorted(os.listdir(PACKS_DIR)):
        if name.lower().endswith(".json"):
            yield os.path.join(PACKS_DIR, name)


def _load_all_styles() -> List[Dict[str, Any]]:
    styles: List[Dict[str, Any]] = []
    for path in _iter_pack_paths():
        try:
            data = _read_json(path)
        except Exception:
            # If a pack is broken, keep going; validate_styles.py will catch it.
            continue
        styles.extend(data.get("styles", []) or [])
    return styles


def _ensure_unique_id(style_id: str, existing_ids: set) -> str:
    if style_id not in existing_ids:
        return style_id
    i = 2
    while True:
        cand = f"{style_id}_{i}"
        if cand not in existing_ids:
            return cand
        i += 1


def _ensure_unique_name(name: str, existing_names: set) -> str:
    if name not in existing_names:
        return name
    i = 2
    while True:
        cand = f"{name} ({i})"
        if cand not in existing_names:
            return cand
        i += 1


def _available_categories(existing_styles: Sequence[Dict[str, Any]], gen_mod) -> List[str]:
    cats = set()
    for s in existing_styles:
        c = s.get("category")
        if isinstance(c, str) and c.strip():
            cats.add(c.strip())
    # Also include categories we have base templates for.
    cats.update((gen_mod.CATEGORY_BASE_PREFIX or {}).keys())
    cats.update((gen_mod.CATEGORY_BASE_SUFFIX or {}).keys())
    return sorted(cats, key=lambda x: x.casefold())


def _make_style_entry(
    gen_mod,
    *,
    name: str,
    category: str,
    core: Sequence[str],
    details: Sequence[str],
    tags: Sequence[str],
    style_id: Optional[str],
    id_prefix: str,
) -> Dict[str, Any]:
    all_styles = _load_all_styles()
    existing_ids = {str(s.get("id")) for s in all_styles if s.get("id") is not None}
    existing_names = {str(s.get("name")) for s in all_styles if s.get("name") is not None}

    base_id = style_id.strip() if style_id else f"{id_prefix}_{_slugify(name)}"
    final_id = _ensure_unique_id(base_id, existing_ids)
    final_name = _ensure_unique_name(name.strip(), existing_names)

    base_prefix = tuple((gen_mod.CATEGORY_BASE_PREFIX or {}).get(category, ()))
    base_suffix = tuple((gen_mod.CATEGORY_BASE_SUFFIX or {}).get(category, ()))

    prefix = gen_mod.z_join(tuple(base_prefix) + tuple(core))
    suffix = gen_mod.z_join(tuple(details) + tuple(base_suffix))

    entry: Dict[str, Any] = {
        "id": final_id,
        "name": final_name,
        "category": category,
        "default": {"prefix": prefix, "suffix": suffix},
    }
    if tags:
        entry["tags"] = list(tags)
    return entry


def _load_or_init_pack(path: str) -> Dict[str, Any]:
    if os.path.isfile(path):
        data = _read_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"Pack is not a JSON object: {path}")
        if "styles" not in data:
            data["styles"] = []
        if "version" not in data:
            data["version"] = 1
        return data
    return {"version": 1, "styles": []}


def cmd_categories(args) -> int:
    gen_mod = _load_generator_module()
    styles = _load_all_styles()
    cats = _available_categories(styles, gen_mod)
    counts = Counter(s.get("category", "Uncategorized") for s in styles)
    for c in cats:
        print(f"{c} ({counts.get(c, 0)})")
    return 0


def cmd_stats(args) -> int:
    styles = _load_all_styles()
    counts = Counter(s.get("category", "Uncategorized") for s in styles)
    total = sum(counts.values())
    print(f"styles {total}")
    for c, n in counts.most_common():
        print(f"{n:4d}  {c}")
    return 0


def cmd_add(args) -> int:
    gen_mod = _load_generator_module()
    pack_path = os.path.abspath(args.pack)
    pack = _load_or_init_pack(pack_path)

    core = _split_csv_list(args.core) + _split_csv_list(args.prefix_extra)
    details = _split_csv_list(args.details) + _split_csv_list(args.suffix_extra)
    tags = _split_csv_list(args.tags)

    entry = _make_style_entry(
        gen_mod,
        name=args.name,
        category=args.category,
        core=core,
        details=details,
        tags=tags,
        style_id=args.id,
        id_prefix=args.id_prefix,
    )

    pack["styles"].append(entry)
    pack["styles"] = sorted(
        pack["styles"],
        key=lambda s: (str(s.get("category", "")).casefold(), str(s.get("name", "")).casefold(), str(s.get("id", ""))),
    )
    _write_json(pack_path, pack)

    print(f"Added: {entry['category']} | {entry['name']} | {entry['id']}")
    print(f"Pack: {pack_path}")
    return 0


def _read_bulk_csv(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            rows.append({k.strip(): (v or "").strip() for k, v in row.items() if k})
    return rows


def _read_bulk_json(path: str) -> List[Dict[str, Any]]:
    data = _read_json(path)
    if isinstance(data, dict) and "styles" in data:
        data = data["styles"]
    if not isinstance(data, list):
        raise ValueError("JSON bulk file must be a list (or an object with a 'styles' list).")
    out: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        out.append(item)
    return out


def cmd_bulk(args) -> int:
    gen_mod = _load_generator_module()
    pack_path = os.path.abspath(args.pack)
    pack = _load_or_init_pack(pack_path)

    if args.csv:
        items = _read_bulk_csv(os.path.abspath(args.csv))
    elif args.json:
        items = _read_bulk_json(os.path.abspath(args.json))
    else:
        raise RuntimeError("bulk requires --csv or --json")

    added = 0
    for item in items:
        name = (item.get("name") or "").strip()
        category = (item.get("category") or "").strip()
        if not name or not category:
            continue

        core = _split_csv_list(item.get("core")) + _split_csv_list(item.get("prefix_extra"))
        details = _split_csv_list(item.get("details")) + _split_csv_list(item.get("suffix_extra"))
        tags = _split_csv_list(item.get("tags"))
        style_id = (item.get("id") or "").strip() or None

        entry = _make_style_entry(
            gen_mod,
            name=name,
            category=category,
            core=core,
            details=details,
            tags=tags,
            style_id=style_id,
            id_prefix=args.id_prefix,
        )
        pack["styles"].append(entry)
        added += 1

    pack["styles"] = sorted(
        pack["styles"],
        key=lambda s: (str(s.get("category", "")).casefold(), str(s.get("name", "")).casefold(), str(s.get("id", ""))),
    )
    _write_json(pack_path, pack)
    print(f"Added {added} styles to {pack_path}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="add_styles.py", description="PromptStyler style pack helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_categories = sub.add_parser("categories", help="List available categories")
    p_categories.set_defaults(func=cmd_categories)

    p_stats = sub.add_parser("stats", help="Show style counts per category")
    p_stats.set_defaults(func=cmd_stats)

    p_add = sub.add_parser("add", help="Add a single style to a pack")
    p_add.add_argument("--pack", default=DEFAULT_PACK_PATH, help="Output pack JSON path")
    p_add.add_argument("--id-prefix", default="user", help="Prefix for generated ids (default: user)")
    p_add.add_argument("--id", default=None, help="Optional explicit id (must be unique)")
    p_add.add_argument("--name", required=True, help="Style display name")
    p_add.add_argument("--category", required=True, help="Style category (as shown in the dropdown)")
    p_add.add_argument(
        "--core",
        default="",
        help="Comma-separated core descriptors (added to prefix after category base)",
    )
    p_add.add_argument(
        "--details",
        default="",
        help="Comma-separated detail descriptors (added to suffix before category base)",
    )
    p_add.add_argument("--prefix-extra", default="", help="Alias for --core")
    p_add.add_argument("--suffix-extra", default="", help="Alias for --details")
    p_add.add_argument("--tags", default="", help="Comma-separated tags")
    p_add.set_defaults(func=cmd_add)

    p_bulk = sub.add_parser("bulk", help="Bulk add styles from CSV or JSON")
    p_bulk.add_argument("--pack", default=DEFAULT_PACK_PATH, help="Output pack JSON path")
    p_bulk.add_argument("--id-prefix", default="user", help="Prefix for generated ids (default: user)")
    p_bulk.add_argument("--csv", default=None, help="CSV file path (columns: name,category,core,details,tags,id)")
    p_bulk.add_argument("--json", default=None, help="JSON file path (list of style objects)")
    p_bulk.set_defaults(func=cmd_bulk)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
