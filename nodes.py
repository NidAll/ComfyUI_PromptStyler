from __future__ import annotations

from typing import Any, Dict, Tuple

try:
    from .style_library import (
        DEFAULT_VARIANT,
        LOAD_POLICY_LENIENT,
        StyleLibraryError,
        StyleTemplate,
        compose_prompt,
        get_cached_style_library,
        make_style_meta,
        resolve_overlay_style,
        resolve_style,
    )
except ImportError:
    from style_library import (
        DEFAULT_VARIANT,
        LOAD_POLICY_LENIENT,
        StyleLibraryError,
        StyleTemplate,
        compose_prompt,
        get_cached_style_library,
        make_style_meta,
        resolve_overlay_style,
        resolve_style,
    )


def load_styles() -> Tuple[StyleTemplate, ...]:
    return get_cached_style_library(load_policy=LOAD_POLICY_LENIENT).styles


class PromptStylerConditioning:
    """
    One-node UX: pick one style, optionally refine the selection/search behavior,
    then output CONDITIONING for KSampler "positive".
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        library = get_cached_style_library(load_policy=LOAD_POLICY_LENIENT)
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "apply_style": ("BOOLEAN", {"default": True}),
                "style": (library.choices,),
                "template_variant": (list(library.variants),),
                "style_id_override": ("STRING", {"multiline": False, "default": ""}),
                "text_encoder": ("CLIP",),
                "selection_mode": (["dropdown", "search", "id"], {"default": "dropdown"}),
                "style_search": ("STRING", {"multiline": False, "default": ""}),
                "category_hint": ("STRING", {"multiline": False, "default": ""}),
                "tag_hint": ("STRING", {"multiline": False, "default": ""}),
                "style_strength": (["subtle", "normal", "strong"], {"default": "strong"}),
                "dedupe_mode": (["smart", "off"], {"default": "smart"}),
                "overlay_style_id": ("STRING", {"multiline": False, "default": ""}),
                "on_missing_style": (["error", "passthrough"], {"default": "error"}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "styled_prompt", "resolved_style_id", "resolved_style_meta")
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
        selection_mode: str,
        style_search: str,
        category_hint: str,
        tag_hint: str,
        style_strength: str,
        dedupe_mode: str,
        overlay_style_id: str,
        on_missing_style: str,
    ):
        if text_encoder is None:
            raise RuntimeError("ERROR: text_encoder input is invalid: None")

        prompt = prompt or ""
        chosen_style = None
        overlay_style = None
        resolved_style_id = ""
        applied_variant = DEFAULT_VARIANT
        error = ""
        prompt_details: Dict[str, Any] = {}

        if not apply_style:
            styled_prompt = prompt
        else:
            library = get_cached_style_library(load_policy=LOAD_POLICY_LENIENT)
            try:
                chosen_style = resolve_style(
                    library,
                    selection_mode=selection_mode,
                    choice=style,
                    style_id_override=style_id_override,
                    style_search=style_search,
                    category_hint=category_hint,
                    tag_hint=tag_hint,
                )
                resolved_style_id = chosen_style.id
            except StyleLibraryError as exc:
                if on_missing_style != "passthrough":
                    raise ValueError(str(exc))
                error = str(exc)
                styled_prompt = prompt
                chosen_style = None
            else:
                try:
                    overlay_style = resolve_overlay_style(library, overlay_style_id)
                except StyleLibraryError as exc:
                    if on_missing_style != "passthrough":
                        raise ValueError(str(exc))
                    error = str(exc)
                    overlay_style = None

                styled_prompt, prompt_details = compose_prompt(
                    prompt,
                    chosen_style,
                    template_variant=template_variant,
                    style_strength=style_strength,
                    dedupe_mode=dedupe_mode,
                    overlay_style=overlay_style,
                )
                applied_variant = str(prompt_details.get("variant", DEFAULT_VARIANT))

        resolved_style_meta = make_style_meta(
            chosen_style=chosen_style,
            overlay_style=overlay_style,
            requested_variant=template_variant,
            applied_variant=applied_variant,
            selection_mode=selection_mode,
            style_search=style_search,
            category_hint=category_hint,
            tag_hint=tag_hint,
            style_strength=style_strength,
            dedupe_mode=dedupe_mode,
            on_missing_style=on_missing_style,
            prompt_details=prompt_details,
            error=error,
        )

        tokens = text_encoder.tokenize(styled_prompt)
        conditioning = text_encoder.encode_from_tokens_scheduled(tokens)
        return (conditioning, styled_prompt, resolved_style_id, resolved_style_meta)


NODE_CLASS_MAPPINGS = {
    "PromptStylerConditioning": PromptStylerConditioning,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptStylerConditioning": "PromptStyler: Prompt -> Conditioning (Style Picker)",
}
