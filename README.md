# ComfyUI PromptStyler

PromptStyler is a custom ComfyUI node that applies a curated style template to your positive prompt and outputs `CONDITIONING` for KSampler.

The node stays lightweight in graphs, but it now supports three ways to resolve a style:

- dropdown selection
- direct `id` lookup
- offline search across style id, name, category, and tags

It also supports an optional color-grade overlay, search hints, and debug metadata without changing the existing node name or the first two outputs.

## Node

ComfyUI display name:

- `PromptStyler: Prompt -> Conditioning (Style Picker)`

Outputs:

- `positive` (`CONDITIONING`)
- `styled_prompt` (`STRING`)
- `resolved_style_id` (`STRING`)
- `resolved_style_meta` (`STRING`, JSON)

## What It Does

1. You enter a subject prompt.
2. PromptStyler resolves a base style from the dropdown, a style id, or a search query.
3. It applies the style to your prompt.
4. Optionally, it appends one `Color Grade*` overlay style.
5. It tokenizes the final prompt with the connected text encoder and returns `CONDITIONING`.

The default behavior remains compatible with older graphs:

- the node name is unchanged
- `style_id_override` still works in saved workflows
- default strength is `strong`, which preserves the prior full-style application behavior

## Recommended Wiring

1. Add `CheckpointLoaderSimple`
2. Add `PromptStyler: Prompt -> Conditioning (Style Picker)`
3. Add `KSampler`

Connect:

- `CheckpointLoaderSimple.CLIP` -> `PromptStyler.text_encoder`
- your text source -> `PromptStyler.prompt`
- `PromptStyler.positive` -> `KSampler.positive`

Use `styled_prompt` and `resolved_style_meta` for debugging when a style is not resolving the way you expect.

## Inputs

Core inputs:

- `prompt`: your positive prompt
- `apply_style`: bypass styling while still encoding the prompt
- `style`: main dropdown entry in `Category | Name | id` format
- `template_variant`: `default` or any model-specific variant present in the style packs
- `style_id_override`: direct id selection, mainly useful with newly-added user styles
- `text_encoder`: connect from your checkpoint/model loader

Selection controls:

- `selection_mode`: `dropdown`, `search`, or `id`
- `style_search`: free-text style lookup used by `selection_mode=search`
- `category_hint`: optional substring filter applied before search scoring
- `tag_hint`: optional comma-separated tag filter applied before search scoring
- `on_missing_style`: `error` or `passthrough`

Composition controls:

- `style_strength`: `subtle`, `normal`, or `strong`
- `dedupe_mode`: `smart` or `off`
- `overlay_style_id`: optional secondary style id, restricted to categories starting with `Color Grade`

### Selection Behavior

- `dropdown`: uses the selected dropdown entry
- `id`: uses `style_id_override`
- `search`: scores exact id matches first, then exact name, then token matches across id, name, category, and tags
- `category_hint` and `tag_hint` narrow the candidate pool before scoring
- ambiguous searches fail with the top candidates listed in the error

### Composition Model

Recommended mental model:

- base style
- optional color-grade overlay
- optional search-based style resolution

`style_strength` only affects the default phrase-based variant:

- `subtle`: first 3 unique prefix phrases and first 3 unique suffix phrases
- `normal`: first 6 unique prefix phrases and first 6 unique suffix phrases
- `strong`: all phrases

`dedupe_mode=smart` only removes duplicate style-added phrases. It does not rewrite or collapse repeated phrases inside the user prompt.

## Style Library

Styles are loaded from JSON packs in filename order:

- `styles/packs/*.json`

Compatibility snapshot:

- `styles/styles_v1.json`

Pack file naming uses numeric prefixes for merge order. Example:

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

## Troubleshooting

- Node does not appear:
  - verify the folder is `ComfyUI/custom_nodes/ComfyUI_PromptStyler/`
  - restart ComfyUI or reload custom nodes
- Search fails unexpectedly:
  - relax `category_hint` and `tag_hint`
  - use the `resolved_style_meta` output to inspect the resolution inputs and applied variant
- A saved graph should keep running while you edit packs:
  - use `on_missing_style=passthrough` if you want the node to fall back to the raw prompt during live pack edits
- Styles look stale:
  - rerun `tools/sync_legacy_styles.py` or `tools/generate_style_packs.py`
  - reload custom nodes in ComfyUI

## Release Notes

Version metadata is managed from `VERSION`.

- `__init__.py` reads `VERSION` at runtime
- `.release-please-manifest.json` should be synced from `VERSION` with `tools/version_sync.py write`
- `CHANGELOG.md` follows Keep a Changelog

See `RELEASING.md` for the maintainer flow.
