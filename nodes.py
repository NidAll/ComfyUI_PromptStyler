from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


_HERE = os.path.dirname(os.path.realpath(__file__))
_STYLES_PATH = os.path.join(_HERE, "styles", "styles_v1.json")
_STYLE_PACKS_DIR = os.path.join(_HERE, "styles", "packs")


def _norm_space(s: str) -> str:
    return " ".join((s or "").replace("\r", " ").replace("\n", " ").split())


def _split_phrases(s: str, sep: str) -> List[str]:
    s = _norm_space(s)
    if not s:
        return []
    parts = [p.strip() for p in s.split(sep)]
    return [p for p in parts if p]


def _dedupe_phrases(phrases: List[str]) -> List[str]:
    # Stable de-dupe (case-insensitive) while preserving first occurrence.
    seen = set()
    out: List[str] = []
    for p in phrases:
        k = p.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


@dataclass(frozen=True)
class StyleTemplate:
    id: str
    name: str
    category: str
    prefix: str
    suffix: str
    flux_prefix: str = ""
    flux_suffix: str = ""
    tags: Tuple[str, ...] = ()


_STYLE_CACHE_SIG: Optional[Tuple[Tuple[str, float, int], ...]] = None
_STYLE_CACHE_STYLES: Tuple[StyleTemplate, ...] = ()
_STYLE_CACHE_BY_ID: Dict[str, StyleTemplate] = {}
_STYLE_CACHE_CHOICES: List[str] = []


def _file_sig(path: str) -> Tuple[str, float, int]:
    try:
        st = os.stat(path)
        return (path, float(st.st_mtime), int(st.st_size))
    except OSError:
        return (path, -1.0, -1)


def _iter_pack_paths() -> List[str]:
    if not os.path.isdir(_STYLE_PACKS_DIR):
        return []
    out: List[str] = []
    for name in sorted(os.listdir(_STYLE_PACKS_DIR)):
        if name.lower().endswith(".json"):
            out.append(os.path.join(_STYLE_PACKS_DIR, name))
    return out


def _style_sources_sig(path: str = _STYLES_PATH) -> Tuple[Tuple[str, float, int], ...]:
    pack_paths = _iter_pack_paths()
    # Include the legacy file in the signature even when packs exist, since we
    # may fall back to it if packs are empty/broken.
    sources = (pack_paths + [path]) if pack_paths else [path]
    return tuple(_file_sig(p) for p in sources)


def _load_styles_file(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f) or {}
    if not isinstance(data, dict):
        return []
    styles = data.get("styles", []) or []
    if not isinstance(styles, list):
        return []
    return [s for s in styles if isinstance(s, dict)]


def _load_style_sources(path: str = _STYLES_PATH) -> List[Dict[str, Any]]:
    # Supports either a single monolithic JSON (styles_v1.json) or multiple packs
    # in styles/packs/*.json. If packs exist, they are merged (in filename order).
    pack_paths = _iter_pack_paths()
    if not pack_paths:
        try:
            return _load_styles_file(path)
        except Exception as e:
            print(f"PromptStyler: ERROR: unable to read styles file: {path} ({e})")
            return []

    merged: List[Dict[str, Any]] = []
    for p in pack_paths:
        try:
            part = _load_styles_file(p)
        except Exception as e:
            print(f"PromptStyler: WARN: unable to read style pack: {p} ({e})")
            continue
        if not part:
            # Empty packs are allowed; keep going.
            continue
        merged.extend(part)

    # If packs exist but none were usable, fall back to the legacy file so the node still loads.
    if not merged:
        try:
            legacy = _load_styles_file(path)
        except Exception as e:
            print(
                f"PromptStyler: ERROR: no usable style packs found and unable to read legacy file: {path} ({e})"
            )
            return []
        if legacy:
            print(f"PromptStyler: WARN: no styles loaded from packs; falling back to legacy file: {path}")
            return legacy

    return merged


def _get_style_library(path: str = _STYLES_PATH) -> Tuple[Tuple[StyleTemplate, ...], Dict[str, StyleTemplate], List[str]]:
    global _STYLE_CACHE_SIG, _STYLE_CACHE_STYLES, _STYLE_CACHE_BY_ID, _STYLE_CACHE_CHOICES

    sig = _style_sources_sig(path)
    if sig == _STYLE_CACHE_SIG:
        return _STYLE_CACHE_STYLES, _STYLE_CACHE_BY_ID, _STYLE_CACHE_CHOICES

    raw_styles = _load_style_sources(path)
    styles: List[StyleTemplate] = []
    for raw in raw_styles:
        sid = raw.get("id")
        name = raw.get("name")
        if sid is None or name is None:
            continue

        default = raw.get("default", {}) or {}
        if not isinstance(default, dict):
            default = {}

        models = raw.get("models", {}) or {}
        if not isinstance(models, dict):
            models = {}
        flux = models.get("flux_2_klein", {}) or {}
        if not isinstance(flux, dict):
            flux = {}

        tmpl = StyleTemplate(
            id=str(sid),
            name=str(name),
            category=str(raw.get("category", "Uncategorized")),
            prefix=str(default.get("prefix", "")),
            suffix=str(default.get("suffix", "")),
            flux_prefix=str(flux.get("prefix", "") or ""),
            flux_suffix=str(flux.get("suffix", "") or ""),
            tags=tuple(raw.get("tags", []) or []),
        )
        styles.append(tmpl)

    by_id = {s.id: s for s in styles}
    choices = _choices_for_styles(styles) if styles else ["(no styles found) | (no styles) | __none__"]

    _STYLE_CACHE_SIG = sig
    _STYLE_CACHE_STYLES = tuple(styles)
    _STYLE_CACHE_BY_ID = by_id
    _STYLE_CACHE_CHOICES = choices
    return _STYLE_CACHE_STYLES, _STYLE_CACHE_BY_ID, _STYLE_CACHE_CHOICES


def load_styles(path: str = _STYLES_PATH) -> Tuple[StyleTemplate, ...]:
    styles, _by_id, _choices = _get_style_library(path)
    return styles


def _choices_for_styles(styles: Sequence[StyleTemplate]) -> List[str]:
    # One big dropdown, but sorted + categorized to make it browsable.
    # Format is stable and easy to parse: "Category | Name | id"
    styles_sorted = sorted(styles, key=lambda s: (s.category.casefold(), s.name.casefold(), s.id))
    return [f"{s.category} | {s.name} | {s.id}" for s in styles_sorted]


def _style_by_choice(styles: Sequence[StyleTemplate], choice: str) -> Optional[StyleTemplate]:
    if not choice:
        return None
    # Choice format: "Category | Name | id"
    sid = choice.rsplit("|", 1)[-1].strip()
    for s in styles:
        if s.id == sid:
            return s
    return None


class PromptStylerConditioning:
    """
    One-node UX: pick ONE style (from a categorized dropdown), apply it to the
    user's prompt, and output CONDITIONING for KSampler "positive".
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        styles, _by_id, choices = _get_style_library()
        return {
            "required": {
                # Prompt is the main input; CLIP is just a wire from your model loader.
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "apply_style": ("BOOLEAN", {"default": True}),
                "style": (choices,),
                "template_variant": (["default", "flux_2_klein"],),
                "style_id_override": ("STRING", {"multiline": False, "default": ""}),
                "text_encoder": ("CLIP",),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "STRING")
    RETURN_NAMES = ("positive", "styled_prompt")
    FUNCTION = "encode"
    CATEGORY = "PromptStyler"

    def encode(
        self,
        prompt: str,
        apply_style: bool,
        style: str,
        template_variant: str,
        style_id_override: str,
        text_encoder,
    ):
        if text_encoder is None:
            raise RuntimeError("ERROR: text_encoder input is invalid: None")

        prompt = prompt or ""

        if not apply_style:
            styled_prompt = prompt
        else:
            styles, by_id, _choices = _get_style_library()

            style_id_override = (style_id_override or "").strip()
            if style_id_override:
                chosen = by_id.get(style_id_override)
                if chosen is None:
                    raise ValueError(f"Unknown style_id_override: {style_id_override}")
            else:
                chosen = _style_by_choice(styles, style)
            if chosen is None:
                raise ValueError("No style selected.")

            if template_variant == "flux_2_klein" and (chosen.flux_prefix.strip() or chosen.flux_suffix.strip()):
                styled_prompt = _norm_space(" ".join([prompt, chosen.flux_prefix, chosen.flux_suffix]))
            else:
                sep = ", "
                prefix_phrases = _split_phrases(chosen.prefix, sep=sep)
                prompt_phrases = _split_phrases(prompt, sep=sep)
                suffix_phrases = _split_phrases(chosen.suffix, sep=sep)

                phrases = _dedupe_phrases(prefix_phrases + prompt_phrases + suffix_phrases)
                styled_prompt = sep.join([p for p in phrases if p])

        tokens = text_encoder.tokenize(styled_prompt)
        conditioning = text_encoder.encode_from_tokens_scheduled(tokens)
        return (conditioning, styled_prompt)


NODE_CLASS_MAPPINGS = {
    "PromptStylerConditioning": PromptStylerConditioning,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptStylerConditioning": "PromptStyler: Prompt -> Conditioning (Style Picker)",
}
