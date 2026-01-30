# ComfyUI PromptStyler

Custom ComfyUI node that applies curated style **prefix/suffix** templates to your positive prompt and outputs **CONDITIONING** for KSampler.

## Versioning / Releases

- Version: `VERSION` (also mirrored as `__version__` in `__init__.py`).
- Changelog: `CHANGELOG.md`.
- Releases: automated via Release Please (`.github/workflows/release-please.yml`).

## Install

1. Copy this folder to: `ComfyUI/custom_nodes/ComfyUI_PromptStyler`
2. Restart ComfyUI.

## Nodes

- `PromptStyler: Prompt -> Conditioning (Style Picker)`
  - What it does: takes your `prompt`, applies exactly **one** style (prefix + suffix), and returns `positive` CONDITIONING.
  - Inputs:
    - `prompt` (STRING)
    - `apply_style` (BOOLEAN) - disable to pass your prompt through unchanged
    - `style` (single-select dropdown, sorted + categorized)
    - `text_encoder` (CLIP) (wire this from your model loader node)
  - Outputs:
    - `positive` (CONDITIONING) -> connect to KSampler `positive`
    - `styled_prompt` (STRING) -> useful for debugging/seeing the final prompt

### Typical Wiring

1. `CheckpointLoaderSimple` -> take its `CLIP` output into `PromptStyler` `text_encoder`
2. Your text prompt -> `PromptStyler` `prompt`
3. `PromptStyler` `positive` -> `KSampler` `positive`

## Style Data

- Styles live in JSON packs under `styles/packs/*.json` (merged in filename order).
- The dropdown is formatted as: `Category | Name | id`
  - Example: `Anime/Manga | Anime Style | anime_style`
- Each style entry contains:
  - `id`, `name`, `category`
  - `default`: `{ "prefix": "...", "suffix": "..." }`

## Validate

Run with your embedded python:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\validate_styles.py
```

## Regenerate Style Packs

The library is generated into `styles/packs/*.json`:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\generate_style_packs.py
```

After regenerating, restart ComfyUI (or "Reload custom nodes") to refresh the style dropdown.

## Add Your Own Styles

Two options:

1. Edit `tools/generate_style_packs.py` and regenerate packs (recommended if you want the same style structure everywhere).
2. Add a new JSON file under `styles/packs/` that follows the same schema (`{"version": 1, "styles": [...]}`).

### Add Styles (Automated)

Use `tools/add_styles.py` to append styles into a custom pack (default: `styles/packs/99_user_custom.json`).

List categories:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py categories
```

Add one style:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py add --name "Ink Noir (Modern)" --category "Fine Art" --core "ink wash, chiaroscuro, high contrast" --details "paper texture, soft bleed, dramatic mood" --tags "ink,noir"
```

Bulk add from CSV (columns: `name,category,core,details,tags`):

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py bulk --csv .\tools\new_styles.csv
```
