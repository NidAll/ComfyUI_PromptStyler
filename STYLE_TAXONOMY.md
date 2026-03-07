# Style Taxonomy

This document defines how curated packs should be organized and expanded.

## Pack Policy

- Default organization is medium/process/material first.
- Target size per pack is 15-25 styles.
- Split a pack when it grows past about 30 styles or starts mixing unrelated subfamilies.
- Preserve existing style ids and visible category labels unless a migration is explicitly planned.
- Extend an existing pack when the new styles share the same medium or production logic.
- Create a new pack only when a coherent process family would otherwise become a grab bag inside an unrelated pack.

## Current Curated Packs

| Pack | Purpose | Categories Covered | Target Range |
| --- | --- | --- | --- |
| `10_cinema.json` | Film still, cinematography, and cinematic look packages | `Cinema` | 15-25 |
| `20_photography.json` | General photographic genres, techniques, and perspective looks | `Photography` | 25-35 |
| `21_photography_alt_process.json` | Darkroom and historical photographic chemistry/process looks | `Photography/Alt Process` | 15-25 |
| `30_illustration.json` | General hand-drawn, painted, manga, vector, pixel, and technical illustration styles | `Illustration`, `Anime/Manga`, `Pixel Art`, `Vector`, `Technical` | 25-35 |
| `31_printmaking_expanded.json` | Historical and fine-art printmaking processes | `Printmaking/Expanded` | 20-30 |
| `32_print_reprographic.json` | Mechanical duplication, proofing, repro, and press-surface looks | `Printmaking/Expanded`, `Photography/Alt Process`, `Graphic Design` | 14-22 |
| `34_fine_art_artists.json` | Artist-reference fine art styles | `Fine Art/Artists` | 20-30 |
| `35_fine_art.json` | Movement and material-led fine art styles | `Fine Art` | 25-35 |
| `36_mixed_media.json` | Layered, tactile, composite-media processes | `Mixed Media` | 20-30 |
| `37_street_art.json` | Street-applied paint, poster, and wall-surface styles | `Street Art` | 12-20 |
| `38_decorative_arts.json` | Core decorative crafts and surface-rich artisan media | `Decorative Arts` | 12-20 |
| `39_internet_aesthetics.json` | Mood-first internet aesthetic families | `Aesthetics/*` | 30-45 |
| `40_graphic_design.json` | Posters, layouts, branding, and print-graphic looks | `Graphic Design` | 25-35 |
| `41_decorative_arts_textiles.json` | Textile, fiber, and woven decorative processes | `Decorative Arts/Textiles` | 20-30 |
| `42_decorative_arts_material_processes.json` | Glass, ceramic, metal, cast, etched, and inlay process styles | `Decorative Arts` | 15-25 |
| `43_digital_craft.json` | Diagrammatic, vector, and constrained-color digital craft styles | `Technical`, `Vector`, `Pixel Art` | 12-20 |
| `50_3d_cg.json` | 3D, render, miniature-set, and CG material looks | `3D/CG` | 15-25 |
| `60_architecture_interior.json` | Architecture and interior presentation looks | `Architecture/Interior` | 15-25 |
| `70_fashion.json` | Fashion/editorial looks | `Fashion` | 12-20 |
| `80_product.json` | Product and commercial object presentation looks | `Product` | 10-18 |
| `90_nature.json` | Landscape and nature presentation looks | `Nature` | 12-20 |
| `95_experimental.json` | Abstract, prismatic, and process-bending visual styles | `Experimental` | 12-20 |
| `96_color_grades.json` | General color grade overlays | `Color Grade` | 15-25 |
| `97_color_grade_film_lab.json` | Film-lab process, scan, and stock-behavior overlays | `Color Grade/Film Lab` | 20-30 |

## Routing Rules For New Styles

- Add tactile layered work to `36_mixed_media.json` before considering any new mixed-media pack.
- Add glass, ceramic, metal, lacquer, and inlay surfaces to the decorative arts family before using `Fine Art` as a fallback.
- Add repro, proofing, duplication, and press artifacts to `32_print_reprographic.json` instead of scattering them across `Graphic Design` or `Experimental`.
- Add `Technical`, `Vector`, and `Pixel Art` growth to `43_digital_craft.json` so those categories stop living as incidental outliers inside the broad illustration pack.
- Use `39_internet_aesthetics.json` only when a style is fundamentally mood/subculture driven rather than process driven.
- Prefer extending an existing process family over creating a new pack with fewer than about 12 coherent styles.
