# PromptStyler Maintainer Notes

This document is for maintainers. It tracks architecture, pack behavior, and the rules that matter when changing runtime style resolution.

## Architecture

Runtime surface:

- `nodes.py`: ComfyUI node definition and input/output wiring
- `style_library.py`: shared style loading, indexing, search, filtering, prompt composition, and legacy snapshot generation

Maintainer tooling:

- `tools/validate_styles.py`: strict schema and uniqueness validation
- `tools/audit_styles.py`: consistency audit and quality checks
- `tools/add_styles.py`: user/custom pack helper
- `tools/generate_style_packs.py`: curated pack generation plus legacy snapshot refresh
- `tools/sync_legacy_styles.py`: regenerate `styles/styles_v1.json` from merged packs
- `tools/version_sync.py`: check or write release metadata derived from `VERSION`
- `STYLE_TAXONOMY.md`: pack purpose, target size, and routing rules for future style additions

Data sources:

- `styles/packs/*.json`: primary runtime source
- `styles/styles_v1.json`: generated compatibility snapshot

## Load Policies

`style_library.py` exposes two load modes:

- `strict`: fail on malformed files or required-field issues
- `lenient`: warn and skip unusable files so the runtime node can stay available

Use `strict` in maintainer tooling and CI.
Use `lenient` in the ComfyUI runtime node.

## Runtime Resolution Model

The node resolves one base style and optionally one overlay style.

Base style resolution modes:

- `dropdown`
- `id`
- `search`

Search ranking order:

1. exact id match
2. exact name match
3. token matches across id, name, category, and tags

Search filters are applied before scoring:

- `category_hint`
- `tag_hint`

If multiple candidates tie for the best score, resolution fails with the top candidates listed.

## Prompt Composition Rules

Recommended composition model:

- base style
- optional color-grade overlay
- optional search-driven style lookup

Default phrase-based variant:

- `style_strength=subtle`: first 3 prefix phrases and first 3 suffix phrases
- `style_strength=normal`: first 6 prefix phrases and first 6 suffix phrases
- `style_strength=strong`: all phrases
- `dedupe_mode=smart`: remove only style-added duplicates, never collapse the raw user prompt
- `dedupe_mode=off`: preserve all style phrases in original order

Overlay rule:

- `overlay_style_id` must resolve to a category starting with `Color Grade`
- the overlay contributes suffix-only styling

Variant rule:

- `template_variant=default` uses phrase-based composition
- model-specific variants use the style's model entry when available and fall back to `default` otherwise

## Pack Authoring Rules

Required fields per style:

- `id`
- `name`
- `default.prefix`
- `default.suffix`

Conventions:

- `id` must be unique and `snake_case`
- phrase-based text should use comma+space separators
- keep style text subject-agnostic unless the style itself is explicitly subject-specific
- avoid photo/cinema gear terms in curated styles

## Release Metadata

Version metadata flow:

- edit `VERSION`
- run `python tools/version_sync.py write`
- CI enforces that `VERSION`, `__init__.py`, and `.release-please-manifest.json` are aligned

## Maintenance Checklist

When changing curated style packs:

1. regenerate or update the packs
2. run `python tools/validate_styles.py`
3. run `python tools/audit_styles.py`
4. run `python tools/sync_legacy_styles.py` if needed
5. update `README.md` when user-visible behavior changed
6. update `CHANGELOG.md`
