from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


ROOT = os.path.dirname(os.path.realpath(__file__))
LEGACY_STYLES_PATH = os.path.join(ROOT, "styles", "styles_v1.json")
STYLE_PACKS_DIR = os.path.join(ROOT, "styles", "packs")

LOAD_POLICY_LENIENT = "lenient"
LOAD_POLICY_STRICT = "strict"
DEFAULT_VARIANT = "default"
DEFAULT_PHRASE_SEPARATOR = ", "
NO_STYLES_CHOICE = "(no styles found) | (no styles) | __none__"
Z_SEP = ", "

# Shared prompt fragments reused by the generator and user-style tooling.
CATEGORY_BASE_PREFIX = {
    "Cinema": (
        "cinematic film still",
        "professional cinematography",
        "cinematic framing",
        "carefully composed shot",
        "atmospheric depth",
        "realistic lighting",
    ),
    "Photography": (
        "professional photography",
        "realistic lighting",
        "natural color rendition",
        "coherent shadows",
        "true-to-life textures",
    ),
    "Product": (
        "commercial product photography",
        "controlled studio lighting",
        "minimal background",
        "controlled reflections",
        "clean composition",
    ),
    "Fashion": (
        "fashion editorial photography",
        "magazine look",
        "high-end styling",
        "clean composition",
        "stylized studio lighting",
    ),
    "Architecture/Interior": (
        "architectural photography",
        "straight verticals",
        "clean geometry",
        "wide field of view",
        "realistic materials",
        "balanced natural light",
    ),
    "Nature": (
        "nature photography",
        "natural light",
        "atmospheric depth",
        "fine detail",
        "realistic textures",
        "environmental realism",
    ),
    "3D/CG": (
        "3d render",
        "high quality render",
        "clean geometry",
        "global illumination",
        "studio lighting",
        "soft shadows",
    ),
    "Graphic Design": (
        "graphic design",
        "poster-like composition",
        "clear hierarchy",
        "bold shapes",
        "limited palette",
        "print-ready layout",
    ),
    "Illustration": (
        "detailed illustration",
        "cohesive style",
        "readable shapes",
        "intentional composition",
        "handcrafted look",
    ),
    "Anime/Manga": (
        "anime/manga illustration",
        "clean linework",
        "cel shading",
        "expressive character design",
        "vibrant palette",
    ),
    "Pixel Art": ("pixel art", "16-bit", "limited palette", "pixel-perfect"),
    "Vector": ("vector illustration", "flat colors", "clean shapes", "crisp edges", "smooth curves"),
    "Technical": ("technical illustration", "clean lines", "diagrammatic layout", "precise geometry", "labels and callouts"),
    "Printmaking": ("printmaking", "ink on paper", "handcrafted texture", "carved lines", "high contrast"),
    "Experimental": ("experimental aesthetic", "bold composition", "graphic lighting", "textural detail"),
    "Color Grade": ("intentional color grade", "filmic tone mapping"),
    "Fine Art": ("fine art", "museum-quality", "traditional techniques", "gallery piece", "handcrafted"),
    "Mixed Media": ("mixed media artwork", "layered textures", "handcrafted marks", "tactile surface"),
    "Street Art": ("street art mural", "spray paint texture", "urban wall", "bold graphic shapes"),
}

CATEGORY_BASE_SUFFIX = {
    "Cinema": (
        "filmic color science",
        "smooth highlight rolloff",
        "deep blacks",
        "subtle film grain",
        "soft halation",
        "high dynamic range",
    ),
    "Photography": (
        "sharp focus",
        "high detail",
        "balanced exposure",
        "fine texture detail",
        "natural contrast",
        "clean highlights",
    ),
    "Product": (
        "crisp edges",
        "clean specular highlights",
        "premium look",
        "high detail",
        "minimal clutter",
    ),
    "Fashion": (
        "editorial color grade",
        "sharp focus",
        "skin texture",
        "catchlights",
        "high detail",
    ),
    "Architecture/Interior": (
        "crisp lines",
        "balanced exposure",
        "clean shadows",
        "high detail",
        "material realism",
    ),
    "Nature": (
        "natural color",
        "clean contrast",
        "high detail",
        "fine microtexture",
        "realistic atmosphere",
    ),
    "3D/CG": (
        "clean render",
        "high detail",
        "sharp edges",
        "high resolution",
        "clean shading",
    ),
    "Graphic Design": (
        "crisp edges",
        "high contrast",
        "clean alignment",
        "balanced negative space",
        "print texture",
    ),
    "Illustration": ("cohesive palette", "clean composition", "high detail", "believable texture"),
    "Anime/Manga": ("high clarity", "crisp edges", "clean gradients", "sharp eyes"),
    "Pixel Art": ("crisp pixels", "dithered shading", "readable silhouette", "sprite-like clarity"),
    "Vector": ("clean layout", "consistent stroke weight", "crisp edges", "smooth curves"),
    "Technical": ("high legibility", "crisp lines", "precise layout", "flat lighting"),
    "Printmaking": ("paper texture", "ink texture", "rough edges", "high contrast"),
    "Experimental": ("intentional design", "high contrast", "tactile texture", "coherent palette"),
    "Color Grade": ("smooth highlight rolloff", "clean shadows", "color separation", "balanced contrast"),
    "Fine Art": ("high detail", "handcrafted surface texture", "gallery lighting", "balanced composition"),
    "Mixed Media": ("high detail", "tactile texture", "paper grain", "layered depth", "cohesive composition"),
    "Street Art": ("bold color", "high contrast", "wall texture", "urban grit", "spray paint overspray"),
}


class StyleLibraryError(RuntimeError):
    pass


@dataclass(frozen=True)
class StyleTemplate:
    id: str
    name: str
    category: str
    prefix: str
    suffix: str
    tags: Tuple[str, ...]
    variants: Dict[str, Tuple[str, str]]

    def variant_prompt(self, variant: str) -> Tuple[str, str, str]:
        if variant == DEFAULT_VARIANT:
            return DEFAULT_VARIANT, self.prefix, self.suffix

        prefix, suffix = self.variants.get(variant, ("", ""))
        if prefix.strip() or suffix.strip():
            return variant, prefix, suffix

        return DEFAULT_VARIANT, self.prefix, self.suffix


@dataclass(frozen=True)
class StyleLibrary:
    styles: Tuple[StyleTemplate, ...]
    by_id: Dict[str, StyleTemplate]
    choices: List[str]
    variants: Tuple[str, ...]


@dataclass(frozen=True)
class SearchCandidate:
    style: StyleTemplate
    score: int
    matched_fields: Tuple[str, ...]


_CACHE_SIGS: Dict[str, Tuple[Tuple[str, float, int], ...]] = {}
_CACHE_LIBRARIES: Dict[str, StyleLibrary] = {}


def norm_space(value: str) -> str:
    return " ".join((value or "").replace("\r", " ").replace("\n", " ").split())


def split_phrases(value: str, sep: str = DEFAULT_PHRASE_SEPARATOR) -> List[str]:
    value = norm_space(value)
    if not value:
        return []
    return [part for part in (p.strip() for p in value.split(sep)) if part]


def dedupe_phrases(phrases: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for phrase in phrases:
        key = phrase.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(phrase)
    return out


def z_join(parts: Sequence[str]) -> str:
    return Z_SEP.join(dedupe_phrases([p.strip() for p in parts if (p or "").strip()]))


def flux_join_sentences(parts: Sequence[str]) -> str:
    parts2 = [p.strip().rstrip(".") for p in parts if (p or "").strip()]
    return ". ".join(parts2).strip() + ("." if parts2 else "")


def style_to_dict(style: StyleTemplate) -> Dict[str, Any]:
    models = {
        name: {"prefix": prefix, "suffix": suffix}
        for name, (prefix, suffix) in sorted(style.variants.items())
        if prefix or suffix
    }
    return {
        "id": style.id,
        "name": style.name,
        "category": style.category,
        "default": {"prefix": style.prefix, "suffix": style.suffix},
        "models": models,
        "tags": list(style.tags),
    }


def _pack_sort_key(name: str) -> Tuple[int, str]:
    match = re.match(r"^(\d+)", name)
    if not match:
        return (9999, name.casefold())
    return (int(match.group(1)), name.casefold())


def iter_pack_paths() -> List[str]:
    if not os.path.isdir(STYLE_PACKS_DIR):
        return []
    out: List[str] = []
    for name in sorted(os.listdir(STYLE_PACKS_DIR), key=_pack_sort_key):
        if name.lower().endswith(".json"):
            out.append(os.path.join(STYLE_PACKS_DIR, name))
    return out


def _file_sig(path: str) -> Tuple[str, float, int]:
    try:
        st = os.stat(path)
        return (path, float(st.st_mtime), int(st.st_size))
    except OSError:
        return (path, -1.0, -1)


def style_sources_sig(legacy_path: str = LEGACY_STYLES_PATH) -> Tuple[Tuple[str, float, int], ...]:
    pack_paths = iter_pack_paths()
    sources = (pack_paths + [legacy_path]) if pack_paths else [legacy_path]
    return tuple(_file_sig(path) for path in sources)


def _emit_problem(load_policy: str, message: str) -> None:
    if load_policy == LOAD_POLICY_STRICT:
        raise StyleLibraryError(message)
    print(f"PromptStyler: WARN: {message}")


def _read_json(path: str, load_policy: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle) or {}
    except Exception as exc:
        _emit_problem(load_policy, f"unable to read style pack: {path} ({exc})")
        return None

    if not isinstance(data, dict):
        _emit_problem(load_policy, f"style file must be a JSON object: {path}")
        return None
    return data


def _iter_raw_style_entries(path: str, load_policy: str) -> List[Dict[str, Any]]:
    data = _read_json(path, load_policy)
    if data is None:
        return []
    styles = data.get("styles", [])
    if not isinstance(styles, list):
        _emit_problem(load_policy, f"'styles' must be a list in: {path}")
        return []
    return [item for item in styles if isinstance(item, dict)]


def _normalize_variants(raw_models: Any, *, path: str, index: int, load_policy: str) -> Dict[str, Tuple[str, str]]:
    if raw_models is None:
        return {}
    if not isinstance(raw_models, dict):
        _emit_problem(load_policy, f"styles[{index}] models must be an object in: {path}")
        return {}

    out: Dict[str, Tuple[str, str]] = {}
    for key, raw_value in raw_models.items():
        if not isinstance(key, str) or not key.strip():
            _emit_problem(load_policy, f"styles[{index}] has a blank model key in: {path}")
            continue
        if not isinstance(raw_value, dict):
            _emit_problem(load_policy, f"styles[{index}] model '{key}' must be an object in: {path}")
            continue
        prefix = str(raw_value.get("prefix", "") or "")
        suffix = str(raw_value.get("suffix", "") or "")
        out[key] = (prefix, suffix)
    return out


def _normalize_style(raw: Dict[str, Any], *, path: str, index: int, load_policy: str) -> Optional[StyleTemplate]:
    sid = raw.get("id")
    name = raw.get("name")
    if sid is None or name is None:
        _emit_problem(load_policy, f"styles[{index}] missing id or name in: {path}")
        return None

    default = raw.get("default", {})
    if not isinstance(default, dict):
        _emit_problem(load_policy, f"styles[{index}] default must be an object in: {path}")
        return None
    if "prefix" not in default or "suffix" not in default:
        _emit_problem(load_policy, f"styles[{index}] default must include prefix and suffix in: {path}")
        return None

    tags_raw = raw.get("tags", []) or []
    if not isinstance(tags_raw, list):
        _emit_problem(load_policy, f"styles[{index}] tags must be a list in: {path}")
        tags_raw = []

    variants = _normalize_variants(raw.get("models", {}), path=path, index=index, load_policy=load_policy)
    return StyleTemplate(
        id=str(sid),
        name=str(name),
        category=str(raw.get("category", "Uncategorized")),
        prefix=str(default.get("prefix", "") or ""),
        suffix=str(default.get("suffix", "") or ""),
        tags=tuple(str(tag).strip() for tag in tags_raw if str(tag).strip()),
        variants=variants,
    )


def _normalize_styles(raw_styles: Sequence[Dict[str, Any]], *, path: str, load_policy: str) -> List[StyleTemplate]:
    out: List[StyleTemplate] = []
    seen_ids = set()
    seen_names = set()
    for index, raw in enumerate(raw_styles):
        style = _normalize_style(raw, path=path, index=index, load_policy=load_policy)
        if style is None:
            continue
        if style.id in seen_ids:
            _emit_problem(load_policy, f"duplicate id '{style.id}' in: {path}")
            continue
        if style.name in seen_names:
            _emit_problem(load_policy, f"duplicate name '{style.name}' in: {path}")
            continue
        seen_ids.add(style.id)
        seen_names.add(style.name)
        out.append(style)
    return out


def load_style_library(load_policy: str = LOAD_POLICY_LENIENT, legacy_path: str = LEGACY_STYLES_PATH) -> StyleLibrary:
    if load_policy not in (LOAD_POLICY_LENIENT, LOAD_POLICY_STRICT):
        raise ValueError(f"Unsupported load_policy: {load_policy}")

    pack_paths = iter_pack_paths()
    styles: List[StyleTemplate] = []
    by_id: Dict[str, StyleTemplate] = {}
    variants = {DEFAULT_VARIANT}

    if not pack_paths:
        raw_styles = _iter_raw_style_entries(legacy_path, load_policy)
        styles = _normalize_styles(raw_styles, path=legacy_path, load_policy=load_policy)
    else:
        for path in pack_paths:
            raw_styles = _iter_raw_style_entries(path, load_policy)
            normalized = _normalize_styles(raw_styles, path=path, load_policy=load_policy)
            for style in normalized:
                if style.id in by_id:
                    _emit_problem(load_policy, f"duplicate id '{style.id}' across packs")
                    continue
                styles.append(style)
                by_id[style.id] = style
                variants.update(style.variants.keys())

        if not styles:
            if load_policy == LOAD_POLICY_STRICT:
                raise StyleLibraryError("no usable style packs found")
            raw_styles = _iter_raw_style_entries(legacy_path, load_policy)
            styles = _normalize_styles(raw_styles, path=legacy_path, load_policy=load_policy)

    if not by_id:
        for style in styles:
            if style.id not in by_id:
                by_id[style.id] = style
            variants.update(style.variants.keys())

    choices = choices_for_styles(styles) if styles else [NO_STYLES_CHOICE]
    return StyleLibrary(
        styles=tuple(styles),
        by_id=by_id,
        choices=choices,
        variants=tuple([DEFAULT_VARIANT] + sorted(v for v in variants if v != DEFAULT_VARIANT)),
    )


def get_cached_style_library(load_policy: str = LOAD_POLICY_LENIENT, legacy_path: str = LEGACY_STYLES_PATH) -> StyleLibrary:
    sig = style_sources_sig(legacy_path)
    if _CACHE_SIGS.get(load_policy) == sig:
        return _CACHE_LIBRARIES[load_policy]
    library = load_style_library(load_policy=load_policy, legacy_path=legacy_path)
    _CACHE_SIGS[load_policy] = sig
    _CACHE_LIBRARIES[load_policy] = library
    return library


def choices_for_styles(styles: Sequence[StyleTemplate]) -> List[str]:
    styles_sorted = sorted(styles, key=lambda style: (style.category.casefold(), style.name.casefold(), style.id))
    return [f"{style.category} | {style.name} | {style.id}" for style in styles_sorted]


def style_by_choice(styles: Sequence[StyleTemplate], choice: str) -> Optional[StyleTemplate]:
    if not choice:
        return None
    sid = choice.rsplit("|", 1)[-1].strip()
    for style in styles:
        if style.id == sid:
            return style
    return None


def resolve_style_legacy(
    library: StyleLibrary,
    *,
    choice: str,
    style_id_override: str,
) -> StyleTemplate:
    style_id_override = (style_id_override or "").strip()
    if style_id_override:
        chosen = library.by_id.get(style_id_override)
        if chosen is None:
            raise StyleLibraryError(f"Unknown style_id_override: {style_id_override}")
        return chosen

    chosen = style_by_choice(library.styles, choice)
    if chosen is None:
        raise StyleLibraryError("No style selected.")
    return chosen


def parse_tag_hint(value: str) -> Tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip().casefold() for part in value.split(",") if part.strip())


def _style_matches_filters(style: StyleTemplate, *, category_hint: str, tags: Sequence[str]) -> bool:
    if category_hint and category_hint.casefold() not in style.category.casefold():
        return False
    if tags:
        style_tags = {tag.casefold() for tag in style.tags}
        if any(tag not in style_tags for tag in tags):
            return False
    return True


def filter_styles(
    styles: Sequence[StyleTemplate],
    *,
    category_hint: str = "",
    tag_hint: str = "",
) -> List[StyleTemplate]:
    category_hint = category_hint.strip()
    tags = parse_tag_hint(tag_hint)
    return [style for style in styles if _style_matches_filters(style, category_hint=category_hint, tags=tags)]


def _search_tokens(query: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9_]+", query.casefold()) if token]


def _search_candidate(style: StyleTemplate, query: str, tokens: Sequence[str]) -> Optional[SearchCandidate]:
    query_cf = query.casefold()
    if query_cf == style.id.casefold():
        return SearchCandidate(style=style, score=10000, matched_fields=("id_exact",))
    if query_cf == style.name.casefold():
        return SearchCandidate(style=style, score=9000, matched_fields=("name_exact",))

    matched_fields: List[str] = []
    score = 0
    id_cf = style.id.casefold()
    name_cf = style.name.casefold()
    category_cf = style.category.casefold()
    tags_cf = [tag.casefold() for tag in style.tags]

    for token in tokens:
        token_score = 0
        if token in id_cf:
            token_score += 60
            matched_fields.append("id")
        if token in name_cf:
            token_score += 40
            matched_fields.append("name")
        if token in category_cf:
            token_score += 25
            matched_fields.append("category")
        if any(token == tag for tag in tags_cf):
            token_score += 35
            matched_fields.append("tag_exact")
        elif any(token in tag for tag in tags_cf):
            token_score += 15
            matched_fields.append("tag")
        score += token_score

    if score <= 0:
        return None

    score += min(len(tokens), 5)
    return SearchCandidate(style=style, score=score, matched_fields=tuple(matched_fields))


def search_styles(
    styles: Sequence[StyleTemplate],
    query: str,
    *,
    category_hint: str = "",
    tag_hint: str = "",
) -> List[SearchCandidate]:
    query = query.strip()
    if not query:
        return []

    filtered = filter_styles(styles, category_hint=category_hint, tag_hint=tag_hint)
    tokens = _search_tokens(query)
    if not tokens:
        return []

    candidates: List[SearchCandidate] = []
    for style in filtered:
        candidate = _search_candidate(style, query, tokens)
        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            -item.score,
            item.style.category.casefold(),
            item.style.name.casefold(),
            item.style.id,
        )
    )
    return candidates


def resolve_style(
    library: StyleLibrary,
    *,
    selection_mode: str,
    choice: str,
    style_id_override: str,
    style_search: str,
    category_hint: str = "",
    tag_hint: str = "",
) -> StyleTemplate:
    style_id_override = (style_id_override or "").strip()
    category_hint = (category_hint or "").strip()
    tag_hint = (tag_hint or "").strip()

    # Preserve old graphs: if a saved workflow already uses style_id_override and
    # the new selection mode input is left at its default, still honor the id.
    if selection_mode == "id" or (selection_mode == "dropdown" and style_id_override):
        chosen = library.by_id.get(style_id_override)
        if chosen is None:
            raise StyleLibraryError(f"Unknown style_id_override: {style_id_override}")
        return chosen

    if selection_mode == "dropdown":
        chosen = style_by_choice(library.styles, choice)
        if chosen is None:
            raise StyleLibraryError("No style selected.")
        return chosen

    if selection_mode != "search":
        raise StyleLibraryError(f"Unsupported selection_mode: {selection_mode}")

    matches = search_styles(
        library.styles,
        style_search,
        category_hint=category_hint,
        tag_hint=tag_hint,
    )
    if not matches:
        raise StyleLibraryError(
            f"No styles matched search query: {style_search.strip() or '(empty query)'}"
        )

    top = matches[0]
    tied = [item for item in matches if item.score == top.score]
    if len(tied) > 1:
        preview = "; ".join(
            f"{item.style.category} | {item.style.name} | {item.style.id}"
            for item in matches[:5]
        )
        raise StyleLibraryError(f"Ambiguous style search '{style_search}': {preview}")
    return top.style


def _style_limit(style_strength: str) -> Optional[int]:
    return {
        "subtle": 3,
        "normal": 6,
        "strong": None,
    }.get(style_strength, None)


def _limit_phrases(phrases: Sequence[str], style_strength: str) -> List[str]:
    limit = _style_limit(style_strength)
    if limit is None:
        return list(phrases)
    return list(phrases[:limit])


def compose_default_prompt(
    prompt: str,
    style: StyleTemplate,
    *,
    style_strength: str = "strong",
    dedupe_mode: str = "smart",
    overlay_style: Optional[StyleTemplate] = None,
) -> Tuple[str, Dict[str, Any]]:
    base_prefix = _limit_phrases(split_phrases(style.prefix), style_strength)
    base_suffix = _limit_phrases(split_phrases(style.suffix), style_strength)
    overlay_suffix = _limit_phrases(split_phrases(overlay_style.suffix), style_strength) if overlay_style else []

    user_phrase_keys = {phrase.casefold() for phrase in split_phrases(prompt)}
    style_phrase_keys = set()

    def include_phrase(phrase: str) -> bool:
        key = phrase.casefold()
        if dedupe_mode == "off":
            return True
        if key in style_phrase_keys:
            return False
        if key in user_phrase_keys:
            return False
        style_phrase_keys.add(key)
        return True

    prefix_phrases = [phrase for phrase in base_prefix if include_phrase(phrase)]
    suffix_phrases = [phrase for phrase in base_suffix if include_phrase(phrase)]
    overlay_phrases = [phrase for phrase in overlay_suffix if include_phrase(phrase)]

    parts = [
        DEFAULT_PHRASE_SEPARATOR.join(prefix_phrases),
        prompt,
        DEFAULT_PHRASE_SEPARATOR.join(suffix_phrases + overlay_phrases),
    ]
    styled_prompt = DEFAULT_PHRASE_SEPARATOR.join([part for part in parts if part])
    return styled_prompt, {
        "base_prefix_phrases": prefix_phrases,
        "base_suffix_phrases": suffix_phrases,
        "overlay_suffix_phrases": overlay_phrases,
    }


def compose_prompt(
    prompt: str,
    style: StyleTemplate,
    *,
    template_variant: str,
    style_strength: str = "strong",
    dedupe_mode: str = "smart",
    overlay_style: Optional[StyleTemplate] = None,
) -> Tuple[str, Dict[str, Any]]:
    prompt = prompt or ""
    applied_variant, prefix, suffix = style.variant_prompt(template_variant)
    overlay_variant = DEFAULT_VARIANT
    overlay_suffix = ""

    if overlay_style is not None:
        overlay_variant, _overlay_prefix, overlay_suffix = overlay_style.variant_prompt(template_variant)

    if applied_variant == DEFAULT_VARIANT:
        styled_prompt, details = compose_default_prompt(
            prompt,
            style,
            style_strength=style_strength,
            dedupe_mode=dedupe_mode,
            overlay_style=overlay_style,
        )
        details["variant"] = applied_variant
        details["overlay_variant"] = overlay_variant if overlay_style else ""
        return styled_prompt, details

    parts = [prompt, prefix, suffix, overlay_suffix]
    styled_prompt = norm_space(" ".join(part for part in parts if part))
    return styled_prompt, {
        "variant": applied_variant,
        "overlay_variant": overlay_variant if overlay_style else "",
        "base_prefix_phrases": [],
        "base_suffix_phrases": [],
        "overlay_suffix_phrases": [],
    }


def compose_prompt_legacy(
    prompt: str,
    style: StyleTemplate,
    *,
    template_variant: str,
) -> Tuple[str, Dict[str, Any]]:
    prompt = prompt or ""
    applied_variant, prefix, suffix = style.variant_prompt(template_variant)

    if applied_variant != DEFAULT_VARIANT:
        styled_prompt = norm_space(" ".join(part for part in (prompt, prefix, suffix) if part))
        return styled_prompt, {
            "variant": applied_variant,
            "base_prefix_phrases": [],
            "base_suffix_phrases": [],
        }

    prefix_phrases = split_phrases(style.prefix)
    prompt_phrases = split_phrases(prompt)
    suffix_phrases = split_phrases(style.suffix)
    phrases = dedupe_phrases(prefix_phrases + prompt_phrases + suffix_phrases)
    styled_prompt = DEFAULT_PHRASE_SEPARATOR.join(phrase for phrase in phrases if phrase)
    return styled_prompt, {
        "variant": DEFAULT_VARIANT,
        "base_prefix_phrases": prefix_phrases,
        "base_suffix_phrases": suffix_phrases,
    }


def is_color_grade_style(style: StyleTemplate) -> bool:
    return style.category.startswith("Color Grade")


def resolve_overlay_style(library: StyleLibrary, overlay_style_id: str) -> Optional[StyleTemplate]:
    overlay_style_id = (overlay_style_id or "").strip()
    if not overlay_style_id:
        return None
    chosen = library.by_id.get(overlay_style_id)
    if chosen is None:
        raise StyleLibraryError(f"Unknown overlay_style_id: {overlay_style_id}")
    if not is_color_grade_style(chosen):
        raise StyleLibraryError(
            f"overlay_style_id must reference a Color Grade style: {overlay_style_id}"
        )
    return chosen


def make_style_meta(
    *,
    chosen_style: Optional[StyleTemplate],
    overlay_style: Optional[StyleTemplate],
    requested_variant: str,
    applied_variant: str,
    selection_mode: str,
    style_search: str,
    category_hint: str,
    tag_hint: str,
    style_strength: str,
    dedupe_mode: str,
    on_missing_style: str,
    prompt_details: Mapping[str, Any],
    error: str = "",
) -> str:
    payload = {
        "status": "error" if error else "ok",
        "error": error,
        "selection_mode": selection_mode,
        "style_search": style_search,
        "category_hint": category_hint,
        "tag_hint": tag_hint,
        "requested_variant": requested_variant,
        "applied_variant": applied_variant,
        "style_strength": style_strength,
        "dedupe_mode": dedupe_mode,
        "on_missing_style": on_missing_style,
        "style": {
            "id": chosen_style.id if chosen_style else "",
            "name": chosen_style.name if chosen_style else "",
            "category": chosen_style.category if chosen_style else "",
            "tags": list(chosen_style.tags) if chosen_style else [],
        },
        "overlay": {
            "id": overlay_style.id if overlay_style else "",
            "name": overlay_style.name if overlay_style else "",
            "category": overlay_style.category if overlay_style else "",
            "tags": list(overlay_style.tags) if overlay_style else [],
        },
        "prompt_details": dict(prompt_details),
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)


def available_categories(styles: Sequence[StyleTemplate]) -> List[str]:
    categories = {style.category for style in styles if style.category.strip()}
    categories.update(CATEGORY_BASE_PREFIX.keys())
    categories.update(CATEGORY_BASE_SUFFIX.keys())
    return sorted(categories, key=lambda value: value.casefold())


def write_legacy_snapshot(path: str = LEGACY_STYLES_PATH, load_policy: str = LOAD_POLICY_STRICT) -> int:
    library = load_style_library(load_policy=load_policy)
    payload = {"version": 1, "styles": [style_to_dict(style) for style in library.styles]}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
    return len(library.styles)
