# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

## [0.3.2] - 2026-03-07

### Added

- CI checks for version sync, style validation, style audit, and runtime regression tests.
- `tools/sync_legacy_styles.py` and `tools/version_sync.py` for compatibility snapshot and release metadata maintenance.
- New medium-first style packs: `styles/packs/32_print_reprographic.json`, `styles/packs/42_decorative_arts_material_processes.json`, and `styles/packs/43_digital_craft.json`.
- Expanded `styles/packs/36_mixed_media.json` to deepen the mixed-media family with 18 new tactile/process-driven styles.
- `STYLE_TAXONOMY.md` documenting pack purpose, target size, and routing rules for future additions.
- Runtime regression coverage for legacy prompt composition and conditioning validation.

### Changed

- `PromptStyler: Prompt -> Conditioning (Style Picker)` now uses the narrow legacy-compatible prompt-to-conditioning contract again for stability.
- Broken or non-finite conditioning now raises an explicit node error instead of silently returning a malformed output.
- `styles/styles_v1.json` is now treated as a generated compatibility snapshot of merged packs.
- README and maintainer documentation now describe the restored stable-node runtime surface and release workflow.

## [0.3.1] - 2026-01-31

### Added

- New Fine Art artist-reference pack: `styles/packs/34_fine_art_artists.json` (25 styles under `Fine Art/Artists`).

## [0.3.0] - 2026-01-31

### Added

- More explicit Flux guidance for curated styles (adds key/finish cues and a “preserve the user subject” instruction).
- New audit check to flag banned photography/cinema gear terms in style text.

### Changed

- Curated style text is more “style-only” and avoids photo gear wording (replaced with effect-language like diffused key light, wide field of view, compressed perspective).
- README rewritten with a beginner-friendly walkthrough and v0.3.0 release checklist.

## [0.2.0] - 2026-01-31

### Added

- 4 new style packs (100 styles) to reach 500 total styles:
  - `styles/packs/21_photography_alt_process.json`
  - `styles/packs/31_printmaking_expanded.json`
  - `styles/packs/41_decorative_arts_textiles.json`
  - `styles/packs/97_color_grade_film_lab.json`
- Node inputs:
  - `template_variant` (`default` or `flux_2_klein`)
  - `style_id_override` (apply a style directly by `id`)
- `tools/add_styles.py wizard` interactive flow for adding user styles into `styles/packs/99_user_custom.json` under `User/<Subcategory>`.

### Changed

- Style loading is cached and more resilient (skips broken packs; falls back to `styles/styles_v1.json` if packs are missing/empty).

## [0.1.0] - 2026-01-30

### Added

- `apply_style` toggle to disable styling in the node.
- New style packs: Decorative Arts and Internet Aesthetics (library now at 400 unique styles).
- `tools/audit_styles.py` for consistency auditing.

### Changed

- README updates for new node input.
