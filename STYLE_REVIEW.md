# Style Library Review & Expansion Notes

## Current Library Snapshot (as of 2026-01-31)

- Total styles: 500 (merged from `styles/packs/*.json` in filename order).
- Categories are consistent and already cover the big buckets: Photography, Cinema, Illustration, Fine Art, Graphic Design, 3D/CG, Architecture/Interior, Fashion/Product, Nature, Experimental, Color Grade, plus focused sub-buckets (e.g. `Photography/Alt Process`, `Decorative Arts/Textiles`, `Color Grade/Film Lab`).
- Style format is stable: each style has `id`, `name`, `category`, and `default.prefix`/`default.suffix` (comma+space separated phrases). The node de-dupes phrases case-insensitively.

Quick checks:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\validate_styles.py
C:\Comfyui\python_embeded\python.exe .\tools\audit_styles.py
```

## Deep Review: What’s Working Well

- **Atomic phrases:** Most templates are written as short, comma-delimited “phrase tokens”, which plays nicely with the node’s phrase splitting + de-dupe.
- **Consistent metadata:** Styles are uniquely named and tagged; packs are structured consistently.
- **Good usability:** Category-driven dropdown makes a large library navigable, and packs are additive (contributors can add a new pack without touching existing ones).

## Deep Review: Opportunities / Gaps

- **Underrepresented mediums:** Mixed Media (7) is still relatively small compared to Photography/Cinema. Printmaking has been expanded via `Printmaking/Expanded` (25), but additional tactile mediums are always valuable for variety and controllability.
- **Technique-level styles:** Many styles are movement-level (e.g., Impressionism, Cubism). Adding more “how it’s made” styles (materials, surface, process) tends to produce more controllable results across different subjects.
- **Prompt token consistency:** The node splits on `", "` (comma + space). Avoid using commas without a following space inside a single token, or the phrase won’t split as expected.

## New Additions: 500-style Expansion Packs

Added four focused packs (25 styles each) to reach 500 total styles:

- `styles/packs/21_photography_alt_process.json` (`Photography/Alt Process`) - alternative photo processes, printing looks, darkroom effects.
- `styles/packs/31_printmaking_expanded.json` (`Printmaking/Expanded`) - broader printmaking techniques beyond the core set.
- `styles/packs/41_decorative_arts_textiles.json` (`Decorative Arts/Textiles`) - fiber/textile techniques and tactile fabric aesthetics.
- `styles/packs/97_color_grade_film_lab.json` (`Color Grade/Film Lab`) - film lab looks (scan/process/stock-inspired grades and artifacts).

## New Additions: Decorative Arts Pack

Added `styles/packs/38_decorative_arts.json` with 12 “material/process-first” styles under the new **Decorative Arts** category. Each is designed to be subject-agnostic (it pushes materials, surface, and craft cues rather than forcing a specific object).

Highlights:

- **Kintsugi Ceramics:** glazed pottery textures + gold-filled crack seams; calm wabi-sabi mood; controlled reflections.
- **Cloisonné Enamelwork:** fine metal partitions, jewel-toned enamel cells; crisp boundaries; glossy speculars.
- **Urushi Lacquerware (Maki-e):** deep lacquer blacks/reds, subtle gold dust ornament; mirror-like finish; refined minimalism.
- **Marquetry Wood Inlay:** veneer grain + precise inlay boundaries; warm tones; polished sheen.
- **Batik Textile:** wax-resist crackle, dye diffusion, cloth weave; earthy palettes; handmade irregularities.
- **Sashiko Stitching:** indigo cloth + white running stitches; geometric patterns; visible thread relief.
- **Jacquard Tapestry Weave:** dense woven patterns; fiber fuzz and weave depth; warm ambient presentation.
- **Paper Quilling Filigree:** rolled paper coils + delicate curls; crisp cut edges; macro shadows between layers.
- **Suminagashi Marbling:** minimal ink rings and soft swirls; paper grain; calm negative space.
- **Ebru Marbling (Vibrant):** high-saturation swirling pigments; fluid motion; artisanal diffusion.
- **Alcohol Ink Blooms:** translucent gradients + sharp diffusion edges; pigment pooling; glossy highlights.
- **Millefiori Glasswork:** colorful internal cane motifs; translucent depth; caustic highlights.

## New Additions: Internet Aesthetics Pack

Added `styles/packs/39_internet_aesthetics.json` with 43 “mood-first” styles organized under **Aesthetics/** subcategories (Liminal, Horror, Retro Future, Tech, Neon, Maximal, Core). Each entry includes a detailed `models.flux_2_klein.suffix` description (lighting, mood, texture, palette) to make the intent explicit.

Highlights:

- **Dreamcore / Weirdcore / Liminal Spaces / Backrooms / Dead Mall / Poolrooms:** empty, nostalgic, uncanny spaces with soft haze and institutional lighting cues.
- **Analog Horror / Emergency Broadcast / Found Footage / Lost Media / Hauntology:** CRT/VHS artifacts, warning overlays, degraded archives, and “memory haze” nostalgia.
- **Retrofuturism / Cassette Futurism / Atompunk / Dieselpunk / Raygun Gothic / Googie / Steampunk / Clockpunk / Biopunk:** distinct eras of futurism and material language (chrome-plastic optimism → beige 80s utilitarianism → riveted soot-metal industry → ornate brass clockwork → wetware biotech).
- **Frutiger Aero / Dark Aero / Frutiger Metro / Webcore:** screen-era aesthetics (glossy aqua optimism, tech-noir glass, transit UI grids, early-web glitter clutter).
- **Synthwave / Darksynth / Dreamwave / Future Funk / Mallsoft / Hardvapour / Seapunk / Hyperpop / Glitchcore:** neon sub-aesthetics ranging from romantic haze to industrial aggression to candy-chrome maximalism.
- **Cottagecore / Fairycore / Goblincore / Angelcore / Dark Academia / Whimsigoth / Pastel Goth:** cozy-to-goth “core” aesthetics with clear palette and texture direction.

## Node UX Update: Disabling Styles

The node now includes `apply_style` (BOOLEAN). When disabled, the node passes the prompt through unchanged and only performs CLIP tokenization/encoding.

## Node UX Update: Flux Variant + Direct ID

- `template_variant`: choose `default` (comma-phrase templates) or `flux_2_klein` (use `models.flux_2_klein.suffix` prose guidance when available).
- `style_id_override`: apply a style directly by `id` (useful for freshly-added user styles without reloading nodes).

## User Style Wizard

Use the CLI wizard to add styles into `styles/packs/99_user_custom.json` (gitignored) under `User/<Subcategory>`:

```powershell
C:\Comfyui\python_embeded\python.exe .\tools\add_styles.py wizard
```

## Web Search Plan (for Future Style Expansion)

Goal: identify additional **medium/process** styles and capture them as prompt-friendly tokens (materials, texture, palette, lighting, composition).

Suggested sources to mine:

- Museum education glossaries (MoMA, Tate, Met) for technique vocabulary.
- Wikipedia “List of art techniques” and printmaking/book-arts pages for breadth.
- Conservation/craft references (ceramics glazing, metal patina, textile techniques) for surface descriptors.

Example query patterns:

- “{technique} texture terms” (e.g., “encaustic texture terms”, “mezzotint texture”)
- “{medium} lighting tips” (e.g., “glossy lacquer photography lighting”)
- “{craft} visual characteristics” (e.g., “sashiko stitching characteristics”)

Conversion checklist (from search notes → PromptStyler entry):

1. **Medium/material:** what it’s made of (glass, enamel, lacquer, fiber, paper).
2. **Surface cues:** gloss vs matte, grain, crackle, weave, tool marks.
3. **Color/palette:** typical pigments, saturation, tonal range.
4. **Pattern/composition:** repeating motifs, symmetry, negative space.
5. **Lighting:** studio/product lighting vs diffuse ambient to emphasize texture.
