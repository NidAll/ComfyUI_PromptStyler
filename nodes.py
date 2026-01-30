from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


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
    tags: Tuple[str, ...] = ()


def load_styles(path: str = _STYLES_PATH) -> List[StyleTemplate]:
    # Supports either a single monolithic JSON (styles_v1.json) or multiple packs
    # in styles/packs/*.json. If packs exist, they are merged (in filename order).
    data: Dict[str, Any] = {"styles": []}
    if os.path.isdir(_STYLE_PACKS_DIR):
        for name in sorted(os.listdir(_STYLE_PACKS_DIR)):
            if not name.lower().endswith(".json"):
                continue
            p = os.path.join(_STYLE_PACKS_DIR, name)
            with open(p, "r", encoding="utf-8") as f:
                part = json.load(f) or {}
            data["styles"].extend(part.get("styles", []) or [])
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    styles: List[StyleTemplate] = []
    for raw in data.get("styles", []):
        default = raw.get("default", {}) or {}

        tmpl = StyleTemplate(
            id=str(raw["id"]),
            name=str(raw["name"]),
            category=str(raw.get("category", "Uncategorized")),
            prefix=str(default.get("prefix", "")),
            suffix=str(default.get("suffix", "")),
            tags=tuple(raw.get("tags", []) or []),
        )
        styles.append(tmpl)

    return styles


def _choices_for_styles(styles: List[StyleTemplate]) -> List[str]:
    # One big dropdown, but sorted + categorized to make it browsable.
    # Format is stable and easy to parse: "Category | Name | id"
    styles_sorted = sorted(styles, key=lambda s: (s.category.casefold(), s.name.casefold(), s.id))
    return [f"{s.category} | {s.name} | {s.id}" for s in styles_sorted]


def _style_by_choice(styles: List[StyleTemplate], choice: str) -> Optional[StyleTemplate]:
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
        styles = load_styles()
        return {
            "required": {
                # Prompt is the main input; CLIP is just a wire from your model loader.
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "style": (_choices_for_styles(styles),),
                "text_encoder": ("CLIP",),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "STRING")
    RETURN_NAMES = ("positive", "styled_prompt")
    FUNCTION = "encode"
    CATEGORY = "PromptStyler"

    def encode(self, prompt: str, style: str, text_encoder):
        styles = load_styles()
        chosen = _style_by_choice(styles, style)
        if chosen is None:
            raise ValueError("No style selected.")

        sep = ", "
        prefix_phrases = _split_phrases(chosen.prefix, sep=sep)
        prompt_phrases = _split_phrases(prompt, sep=sep)
        suffix_phrases = _split_phrases(chosen.suffix, sep=sep)

        phrases = _dedupe_phrases(prefix_phrases + prompt_phrases + suffix_phrases)
        styled_prompt = sep.join([p for p in phrases if p])

        if text_encoder is None:
            raise RuntimeError("ERROR: text_encoder input is invalid: None")

        tokens = text_encoder.tokenize(styled_prompt)
        conditioning = text_encoder.encode_from_tokens_scheduled(tokens)
        return (conditioning, styled_prompt)


NODE_CLASS_MAPPINGS = {
    "PromptStylerConditioning": PromptStylerConditioning,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptStylerConditioning": "PromptStyler: Prompt -> Conditioning (Style Picker)",
}
