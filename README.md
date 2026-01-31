# ComfyUI PromptStyler

PromptStyler is a **custom ComfyUI node** that helps you keep your prompts consistent by applying a selected “style template” to your **positive prompt**, then outputting **CONDITIONING** for KSampler.

If you are new to ComfyUI: you can think of CONDITIONING as the “encoded text prompt” that the sampler uses. PromptStyler builds a *styled prompt string*, encodes it with the model’s text encoder (CLIP), and passes the result to KSampler.

## What This Node Does (Exact Behavior)

Node name in ComfyUI:

- `PromptStyler: Prompt -> Conditioning (Style Picker)`

Step-by-step:

1. You type a normal prompt in `prompt` (your subject + what you want).
2. You pick one style from the dropdown (the node loads style templates from JSON packs).
3. If `apply_style` is enabled:
   - It builds a new prompt: `style.prefix + your prompt + style.suffix`
   - For `template_variant=default`, it merges comma-separated phrases and de-dupes duplicates.
   - For `template_variant=flux_2_klein`, it appends a short prose style guide after your prompt (when available).
4. It tokenizes and encodes the final prompt using the `text_encoder` (CLIP).
5. It outputs:
   - `positive` (CONDITIONING) for KSampler
   - `styled_prompt` (STRING) so you can see the exact final prompt

Important: styles are written to describe **style only** (medium/process/lighting/palette/texture/composition) and to avoid injecting unrelated objects that you didn’t ask for.

## Install (Beginner Friendly)

1. Copy or clone this repo into:

```text
ComfyUI/custom_nodes/ComfyUI_PromptStyler/
```

2. Restart ComfyUI (or use **Reload custom nodes**).
3. Confirm the node exists by searching for `PromptStyler` in the node menu.

## How To Use (Recommended Wiring)

Typical workflow:

1. Add `CheckpointLoaderSimple`
2. Add `PromptStyler: Prompt -> Conditioning (Style Picker)`
3. Add `KSampler`

Connect:

- `CheckpointLoaderSimple.CLIP` -> `PromptStyler.text_encoder`
- Your text -> `PromptStyler.prompt`
- `PromptStyler.positive` -> `KSampler.positive`

Optional (debugging):

- Use the `styled_prompt` output to verify that the style template is doing what you expect.

## Inputs / Outputs (Explained)

Inputs:

- `prompt` (STRING): your prompt text (subject/action/attributes). Works best with comma+space phrases.
- `apply_style` (BOOLEAN): when off, PromptStyler passes your prompt through unchanged (still outputs conditioning).
- `style` (dropdown): pick **one** style. Dropdown entries are `Category | Name | id`.
- `template_variant`:
  - `default`: uses comma+space “phrase tokens” (best for SD-like prompt token lists).
  - `flux_2_klein`: uses prose guidance when present (helpful for Flux-like models).
- `style_id_override` (STRING): advanced. If set, the node uses that style `id` directly (useful right after adding a new style).
- `text_encoder` (CLIP): wire this from your checkpoint/model loader.

Outputs:

- `positive` (CONDITIONING): connect to KSampler `positive`.
- `styled_prompt` (STRING): the final prompt string used for conditioning.

## Style Library (Where Styles Live)

Styles live in JSON packs:

- `styles/packs/*.json` (merged at runtime in filename order)
- Legacy fallback (only used if packs are missing): `styles/styles_v1.json`

Pack file naming:

- Numeric prefixes control merge order (example: `10_cinema.json` loads before `20_photography.json`).

Style entry schema:

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

## Adding Your Own Styles (No Coding Required)

This repo includes a helper tool that writes a custom pack file (gitignored by default):

- Default user pack: `styles/packs/99_user_custom.json`

Wizard (recommended):

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py wizard
```

After adding a style:

- Copy the printed `id`
- Paste it into `style_id_override` to use it immediately (no ComfyUI reload required)

List categories:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py categories
```

Add a style directly:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py add --name "Ink Noir (Modern)" --category "Fine Art" --core "ink wash, chiaroscuro, high contrast" --details "paper texture, soft bleed, dramatic mood" --tags "ink,noir"
```

## Prompting Tips (So Styles Stay Accurate)

- Put **subjects/objects** in your `prompt` (the user input), not in the style template.
- Write prompts as comma+space phrases: `", "` is the splitter used by the node’s default template mode.
- If a style is explicitly specific (its name is a scene/subject), it may include those nouns. Otherwise templates aim to stay subject-agnostic.

## Validate / Audit (Recommended Before Editing Packs)

Validate required fields and uniqueness:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\validate_styles.py
```

Optional consistency audit (also flags banned gear terms):

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\audit_styles.py
```

## Regenerate Curated Packs (For Maintainers)

Curated packs are generated by:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\generate_style_packs.py
```

After regenerating packs, restart ComfyUI (or reload custom nodes) to refresh the dropdown.

## Troubleshooting

- Node doesn’t show up:
  - Verify the folder path is exactly `ComfyUI/custom_nodes/ComfyUI_PromptStyler/`
  - Restart ComfyUI or use **Reload custom nodes**
- Styles missing or dropdown says “(no styles found)”:
  - Check that `styles/packs/*.json` exists and is valid JSON
  - Run `.\tools\validate_styles.py`
- A style feels like it “adds extra objects”:
  - Try `template_variant=default` first (token style)
  - Keep your subject strongly stated in the user `prompt`
  - If you find a template adding unwanted nouns, it should be fixed in the pack (PRs welcome)

## Versioning / GitHub Releases (Preparing v0.3.0)

Source of truth:

- Version: `VERSION` (mirrored in `__init__.py` as `__version__`)
- Changelog: `CHANGELOG.md` (Keep a Changelog)

Suggested release checklist:

1. Run `.\tools\validate_styles.py` and `.\tools\audit_styles.py` (include output in your PR).
2. Ensure `README.md` describes new behavior/inputs.
3. Ensure `CHANGELOG.md` has the release notes under the new version.
4. Push to GitHub and let Release Please create the release PR (see `RELEASING.md`).
