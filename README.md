# ComfyUI PromptStyler

PromptStyler is a custom ComfyUI node pack for applying curated style templates to a positive prompt and returning `CONDITIONING` for KSampler.

This release intentionally splits the runtime surface into a stable default node and an opt-in advanced node.

## Nodes

Stable node:

- `PromptStyler: Prompt -> Conditioning (Style Picker)`
- outputs: `positive`, `styled_prompt`
- behavior: legacy-compatible prompt composition and direct conditioning output

Advanced node:

- `PromptStyler: Advanced Prompt -> Conditioning`
- outputs: `positive`, `styled_prompt`, `resolved_style_id`, `resolved_style_meta`
- behavior: search, overlays, stronger filtering controls, and JSON debug metadata

Use the stable node unless you specifically need the advanced controls.

## Recommended Wiring

1. Add `CheckpointLoaderSimple`
2. Add `PromptStyler: Prompt -> Conditioning (Style Picker)`
3. Add `KSampler`

Connect:

- `CheckpointLoaderSimple.CLIP` -> `PromptStyler.text_encoder`
- your text source -> `PromptStyler.prompt`
- `PromptStyler.positive` -> `KSampler.positive`

`styled_prompt` is the exact text that was encoded.

## Stable Node Inputs

- `prompt`: your positive prompt
- `apply_style`: bypass styling while still encoding the prompt
- `style`: dropdown entry in `Category | Name | id` format
- `template_variant`: `default` or any model-specific variant present in the packs
- `style_id_override`: direct id selection for newly-added or scripted styles
- `text_encoder`: connect from your checkpoint/model loader

Stable node rules:

- `style_id_override` takes precedence over the dropdown when set
- `default` uses legacy comma-phrase composition and de-dupe behavior
- model-specific variants use their explicit variant text and otherwise fall back to `default`
- malformed conditioning now raises an explicit node error instead of silently returning a broken output

## Advanced Node Inputs

Core inputs are the same as the stable node, plus:

- `selection_mode`: `dropdown`, `search`, or `id`
- `style_search`: free-text search used by `selection_mode=search`
- `category_hint`: optional substring filter applied before search scoring
- `tag_hint`: optional comma-separated tag filter applied before search scoring
- `style_strength`: `subtle`, `normal`, or `strong`
- `dedupe_mode`: `smart` or `off`
- `overlay_style_id`: optional secondary style id, restricted to categories starting with `Color Grade`
- `on_missing_style`: `error` or `passthrough`

Advanced node outputs:

- `resolved_style_id`: the final base style id that was resolved
- `resolved_style_meta`: JSON payload describing resolution inputs and composition details

## Style Library

Primary runtime source:

- `styles/packs/*.json`

Compatibility snapshot:

- `styles/styles_v1.json`

Pack filenames use numeric prefixes for merge order, for example:

- `10_cinema.json`
- `96_color_grades.json`
- `99_user_custom.json`

Schema:

```json
{
  "id": "unique_snake_case",
  "name": "Human Name",
  "category": "Category/Subcategory",
  "default": { "prefix": "...", "suffix": "..." },
  "models": { "flux_2_klein": { "prefix": "", "suffix": "..." } },
  "tags": ["tag1", "tag2"]
}
```

## Adding Your Own Styles

Default user-local pack:

- `styles/packs/99_user_custom.json`

List categories:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py categories
```

Launch the wizard:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py wizard
```

Add one style directly:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py add --name "Ink Noir (Modern)" --category "Fine Art" --core "ink wash, chiaroscuro, high contrast" --details "paper texture, soft bleed, dramatic mood" --tags "ink,noir"
```

After adding a style, paste the generated id into `style_id_override` to use it immediately.

## Maintainer Commands

Validate packs:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\validate_styles.py
```

Audit pack consistency:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\audit_styles.py
```

Sync the legacy compatibility snapshot:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\sync_legacy_styles.py
```

Regenerate curated packs and refresh the legacy snapshot:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\generate_style_packs.py
```

Check release/version metadata consistency:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\version_sync.py check
```

Run runtime regression tests:

```powershell
python -m unittest discover -s tests
```

## Troubleshooting

- Stable node returns an error instead of an image:
  - inspect `styled_prompt`
  - confirm the connected `text_encoder` matches the active model family
  - if the error mentions invalid conditioning, compare the same `styled_prompt` through stock `CLIPTextEncode`
- Advanced search fails unexpectedly:
  - relax `category_hint` and `tag_hint`
  - inspect `resolved_style_meta`
- Styles look stale:
  - rerun `tools/sync_legacy_styles.py` or `tools/generate_style_packs.py`
  - reload custom nodes in ComfyUI

## Release Notes

Version metadata is managed from `VERSION`.

- `__init__.py` reads `VERSION` at runtime
- `.release-please-manifest.json` should be synced from `VERSION` with `tools/version_sync.py write`
- `CHANGELOG.md` follows Keep a Changelog

See `RELEASING.md` for the maintainer flow.