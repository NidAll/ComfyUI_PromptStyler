import os
import re
import sys
from collections import Counter
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from style_library import LOAD_POLICY_STRICT, StyleLibraryError, iter_pack_paths, load_style_library


ID_RE = re.compile(r"^[a-z0-9_]+$")
COMMA_RE = re.compile(r",(?!\s)")
BANNED_GEAR_TERMS = (
    "softbox",
    "soft box",
    "strobe",
    "speedlight",
    "beauty dish",
    "octabox",
    "umbrella",
    "ring light",
    "ringlight",
    "on-camera",
    "on camera",
    "tripod shot",
)
BANNED_GEAR_RES = [(term, re.compile(re.escape(term), re.IGNORECASE)) for term in BANNED_GEAR_TERMS]


def main() -> int:
    try:
        library = load_style_library(load_policy=LOAD_POLICY_STRICT)
    except StyleLibraryError as exc:
        print(f"ERROR: {exc}")
        return 2

    styles = list(library.styles)
    ids = [style.id for style in styles]
    names = [style.name for style in styles]
    categories = [style.category or "Uncategorized" for style in styles]

    print(f"styles: {len(styles)}")
    print(f"packs: {len(iter_pack_paths())}")
    print("categories:")
    for category, count in Counter(categories).most_common():
        print(f"  {count:4d}  {category}")

    warnings: List[str] = []
    bad_ids = [style_id for style_id in ids if style_id and not ID_RE.match(style_id)]
    if bad_ids:
        warnings.append(f"bad_ids: {len(bad_ids)} (expected snake_case [a-z0-9_])")

    empty_prefix = 0
    empty_suffix = 0
    missing_tags = 0
    missing_variant = 0
    comma_without_space: List[Tuple[str, str]] = []
    banned_gear_hits: List[Tuple[str, str, str]] = []

    for style in styles:
        prefix = style.prefix or ""
        suffix = style.suffix or ""
        if not prefix.strip():
            empty_prefix += 1
        if not suffix.strip():
            empty_suffix += 1

        for field, text in (("prefix", prefix), ("suffix", suffix)):
            if COMMA_RE.search(text):
                comma_without_space.append((style.id, field))

        variant_prefix, variant_suffix = style.variants.get("flux_2_klein", ("", ""))
        if "flux_2_klein" not in style.variants:
            missing_variant += 1

        for field, text in (("prefix", prefix), ("suffix", suffix), ("flux_2_klein.prefix", variant_prefix), ("flux_2_klein.suffix", variant_suffix)):
            if not text:
                continue
            for term, pattern in BANNED_GEAR_RES:
                if pattern.search(text):
                    banned_gear_hits.append((style.id, field, term))

        if not style.tags:
            missing_tags += 1

    if empty_prefix:
        warnings.append(f"empty_prefix: {empty_prefix}")
    if empty_suffix:
        warnings.append(f"empty_suffix: {empty_suffix}")
    if comma_without_space:
        warnings.append(f"comma_without_space: {len(comma_without_space)} (node splits on ', ')")
    if missing_tags:
        warnings.append(f"missing_tags: {missing_tags}")
    if missing_variant:
        warnings.append(f"missing_models.flux_2_klein: {missing_variant}")
    if len(set(ids)) != len(ids):
        warnings.append("duplicate_ids: detected")
    if len(set(names)) != len(names):
        warnings.append("duplicate_names: detected")
    if banned_gear_hits:
        warnings.append(f"banned_gear_terms: {len({style_id for style_id, _field, _term in banned_gear_hits})} styles")

    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        if banned_gear_hits:
            print("banned gear term examples:")
            for style_id, field, term in banned_gear_hits[:20]:
                print(f"  - {style_id} ({field}): {term}")
    else:
        print("warnings: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
