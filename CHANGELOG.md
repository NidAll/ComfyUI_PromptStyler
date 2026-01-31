# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

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
