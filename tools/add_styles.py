"""
PromptStyler style pack tool.

This script helps you add more styles without editing JSON by hand.
It writes (or updates) a JSON pack under styles/packs/, e.g.:
  styles/packs/99_user_custom.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence


ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from style_library import (
    CATEGORY_BASE_PREFIX,
    CATEGORY_BASE_SUFFIX,
    LOAD_POLICY_STRICT,
    StyleLibraryError,
    available_categories,
    flux_join_sentences,
    load_style_library,
    z_join,
)


PACKS_DIR = os.path.join(ROOT, "styles", "packs")
DEFAULT_PACK_PATH = os.path.join(PACKS_DIR, "99_user_custom.json")


def _slugify(name: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in (name or "")).strip("_")
    while "__" in base:
        base = base.replace("__", "_")
    return base or "style"


def _normalize_user_subcategory(value: str) -> str:
    cleaned = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in (value or ""))
    cleaned = " ".join(cleaned.split()).strip()
    return cleaned or "Custom"


def _split_csv_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle) or {}


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def _load_library():
    return load_style_library(load_policy=LOAD_POLICY_STRICT)


def _existing_identity_sets() -> tuple[set[str], set[str]]:
    library = _load_library()
    return ({style.id for style in library.styles}, {style.name for style in library.styles})


def _ensure_unique_id(style_id: str, existing_ids: set[str]) -> str:
    if style_id not in existing_ids:
        return style_id
    i = 2
    while True:
        candidate = f"{style_id}_{i}"
        if candidate not in existing_ids:
            return candidate
        i += 1


def _ensure_unique_name(name: str, existing_names: set[str]) -> str:
    if name not in existing_names:
        return name
    i = 2
    while True:
        candidate = f"{name} ({i})"
        if candidate not in existing_names:
            return candidate
        i += 1


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


def _make_style_entry(
    *,
    name: str,
    category: str,
    core: Sequence[str],
    details: Sequence[str],
    tags: Sequence[str],
    style_id: Optional[str],
    id_prefix: str,
    flux_suffix: Optional[str] = None,
    existing_ids: Optional[set[str]] = None,
    existing_names: Optional[set[str]] = None,
) -> Dict[str, Any]:
    if existing_ids is None or existing_names is None:
        existing_ids, existing_names = _existing_identity_sets()

    base_id = style_id.strip() if style_id else f"{id_prefix}_{_slugify(name)}"
    final_id = _ensure_unique_id(base_id, existing_ids)
    final_name = _ensure_unique_name(name.strip(), existing_names)
    existing_ids.add(final_id)
    existing_names.add(final_name)

    prefix = z_join(tuple(CATEGORY_BASE_PREFIX.get(category, ())) + tuple(core))
    suffix = z_join(tuple(details) + tuple(CATEGORY_BASE_SUFFIX.get(category, ())))

    tags2 = [tag.strip() for tag in tags if (tag or "").strip()]
    if not tags2:
        tags2 = ["user"]

    if flux_suffix is None:
        parts = [f"Style: {final_name}"]
        core_hint = z_join(core[:12]) if core else ""
        detail_hint = z_join(details[:12]) if details else ""
        if core_hint:
            parts.append(f"Core cues: {core_hint}")
        if detail_hint:
            parts.append(f"Details: {detail_hint}")
        parts.append("Lighting: coherent and intentional")
        parts.append("Mood: consistent with the user prompt")
        flux_suffix2 = flux_join_sentences(parts)
    else:
        flux_suffix2 = str(flux_suffix or "").strip()
        if flux_suffix2 and not re.search(r"[.!?]$", flux_suffix2):
            flux_suffix2 += "."

    return {
        "id": final_id,
        "name": final_name,
        "category": category,
        "default": {"prefix": prefix, "suffix": suffix},
        "models": {"flux_2_klein": {"prefix": "", "suffix": flux_suffix2}},
        "tags": tags2,
    }


def _read_bulk_csv(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row:
                continue
            rows.append({key.strip(): (value or "").strip() for key, value in row.items() if key})
    return rows


def _read_bulk_json(path: str) -> List[Dict[str, Any]]:
    data = _read_json(path)
    if isinstance(data, dict) and "styles" in data:
        data = data["styles"]
    if not isinstance(data, list):
        raise ValueError("JSON bulk file must be a list (or an object with a 'styles' list).")
    return [item for item in data if isinstance(item, dict)]


def cmd_categories(_args) -> int:
    library = _load_library()
    counts = Counter(style.category or "Uncategorized" for style in library.styles)
    for category in available_categories(library.styles):
        print(f"{category} ({counts.get(category, 0)})")
    return 0


def cmd_stats(_args) -> int:
    library = _load_library()
    counts = Counter(style.category or "Uncategorized" for style in library.styles)
    total = sum(counts.values())
    print(f"styles {total}")
    for category, count in counts.most_common():
        print(f"{count:4d}  {category}")
    return 0


def cmd_add(args) -> int:
    pack_path = os.path.abspath(args.pack)
    pack = _load_or_init_pack(pack_path)
    existing_ids, existing_names = _existing_identity_sets()

    core = _split_csv_list(args.core) + _split_csv_list(args.prefix_extra)
    details = _split_csv_list(args.details) + _split_csv_list(args.suffix_extra)
    tags = _split_csv_list(args.tags)

    entry = _make_style_entry(
        name=args.name,
        category=args.category,
        core=core,
        details=details,
        tags=tags,
        style_id=args.id,
        id_prefix=args.id_prefix,
        existing_ids=existing_ids,
        existing_names=existing_names,
    )

    pack["styles"].append(entry)
    pack["styles"] = sorted(
        pack["styles"],
        key=lambda style: (
            str(style.get("category", "")).casefold(),
            str(style.get("name", "")).casefold(),
            str(style.get("id", "")),
        ),
    )
    _write_json(pack_path, pack)

    print(f"Added: {entry['category']} | {entry['name']} | {entry['id']}")
    print(f"Pack: {pack_path}")
    return 0


def cmd_bulk(args) -> int:
    pack_path = os.path.abspath(args.pack)
    pack = _load_or_init_pack(pack_path)
    existing_ids, existing_names = _existing_identity_sets()

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

        entry = _make_style_entry(
            name=name,
            category=category,
            core=_split_csv_list(item.get("core")) + _split_csv_list(item.get("prefix_extra")),
            details=_split_csv_list(item.get("details")) + _split_csv_list(item.get("suffix_extra")),
            tags=_split_csv_list(item.get("tags")),
            style_id=(item.get("id") or "").strip() or None,
            id_prefix=args.id_prefix,
            flux_suffix=(item.get("flux") or item.get("flux_suffix") or "").strip() or None,
            existing_ids=existing_ids,
            existing_names=existing_names,
        )
        pack["styles"].append(entry)
        added += 1

    pack["styles"] = sorted(
        pack["styles"],
        key=lambda style: (
            str(style.get("category", "")).casefold(),
            str(style.get("name", "")).casefold(),
            str(style.get("id", "")),
        ),
    )
    _write_json(pack_path, pack)
    print(f"Added {added} styles to {pack_path}")
    return 0


def _prompt_line(label: str, *, default: Optional[str] = None) -> str:
    if default is None:
        return input(f"{label}: ").strip()
    value = input(f"{label} [{default}]: ").strip()
    return value if value else default


def cmd_wizard(args) -> int:
    pack_path = os.path.abspath(args.pack)
    pack = _load_or_init_pack(pack_path)
    existing_ids, existing_names = _existing_identity_sets()

    print("PromptStyler: User Style Wizard")
    print("Tip: use comma-separated phrases (node splits default templates on ', ').")
    print("")

    subcat = _normalize_user_subcategory(
        _prompt_line("User subcategory (creates category User/<subcategory>)", default="Custom")
    )
    category = f"User/{subcat}"
    name = _prompt_line("Style name")
    if not name.strip():
        print("ERROR: style name is required")
        return 2

    core = _split_csv_list(_prompt_line("Core descriptors (comma-separated)", default=""))
    details = _split_csv_list(_prompt_line("Detail descriptors (comma-separated)", default=""))
    tags = _split_csv_list(_prompt_line("Tags (comma-separated, optional)", default=""))
    tags.extend(["user", _slugify(subcat)])
    flux_suffix = _prompt_line("Flux suffix (optional; blank to auto-generate)", default="").strip() or None

    entry = _make_style_entry(
        name=name,
        category=category,
        core=core,
        details=details,
        tags=tags,
        style_id=None,
        id_prefix=args.id_prefix,
        flux_suffix=flux_suffix,
        existing_ids=existing_ids,
        existing_names=existing_names,
    )

    print("")
    print("Preview")
    print(f"  Category: {entry['category']}")
    print(f"  Name:     {entry['name']}")
    print(f"  ID:       {entry['id']}")
    print(f"  Prefix:   {entry['default']['prefix']}")
    print(f"  Suffix:   {entry['default']['suffix']}")
    print(f"  Flux:     {entry['models']['flux_2_klein']['suffix']}")
    print(f"  Tags:     {', '.join(entry.get('tags', []))}")
    print(f"  Pack:     {pack_path}")

    confirm = _prompt_line("Write this style? (y/n)", default="y").strip().lower()
    if confirm not in ("y", "yes"):
        print("Canceled.")
        return 0

    pack["styles"].append(entry)
    pack["styles"] = sorted(
        pack["styles"],
        key=lambda style: (
            str(style.get("category", "")).casefold(),
            str(style.get("name", "")).casefold(),
            str(style.get("id", "")),
        ),
    )
    _write_json(pack_path, pack)

    print("")
    print(f"Added: {entry['category']} | {entry['name']} | {entry['id']}")
    print(f"Pack: {pack_path}")
    print("Tip: paste the id into the node's style_id_override to use it immediately.")
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
    p_add.add_argument("--core", default="", help="Comma-separated core descriptors")
    p_add.add_argument("--details", default="", help="Comma-separated detail descriptors")
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

    p_wizard = sub.add_parser("wizard", help="Interactive wizard to add a user style")
    p_wizard.add_argument("--pack", default=DEFAULT_PACK_PATH, help="Output pack JSON path")
    p_wizard.add_argument("--id-prefix", default="user", help="Prefix for generated ids (default: user)")
    p_wizard.set_defaults(func=cmd_wizard)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except StyleLibraryError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
