"""
Generate PromptStyler style packs.

This creates JSON files under styles/packs/*.json. We keep packs split by category
so the library can scale without a single giant file becoming unmanageable.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence


ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PACKS_DIR = os.path.join(ROOT, "styles", "packs")


Z_SEP = ", "

# Base prompt fragments per category. These are intentionally short and "model-agnostic"
# so they help both SD-like and Flux-like text encoders without drowning the user prompt.
CATEGORY_BASE_PREFIX = {
    "Cinema": (
        "cinematic film still",
        "professional cinematography",
        "cinematic framing",
        "carefully composed shot",
        "atmospheric depth",
        "realistic lighting",
    ),
    "Photography": (
        "professional photography",
        "realistic lighting",
        "natural color rendition",
        "coherent shadows",
        "true-to-life textures",
    ),
    "Product": (
        "commercial product photography",
        "studio strobe lighting",
        "seamless background",
        "controlled reflections",
        "clean composition",
    ),
    "Fashion": (
        "fashion editorial photography",
        "magazine look",
        "high-end styling",
        "clean composition",
        "stylized studio lighting",
    ),
    "Architecture/Interior": (
        "architectural photography",
        "straight verticals",
        "clean geometry",
        "wide-angle lens",
        "realistic materials",
        "balanced natural light",
    ),
    "Nature": (
        "nature photography",
        "natural light",
        "atmospheric depth",
        "fine detail",
        "realistic textures",
        "environmental realism",
    ),
    "3D/CG": (
        "3d render",
        "high quality render",
        "clean geometry",
        "global illumination",
        "studio lighting",
        "soft shadows",
    ),
    "Graphic Design": (
        "graphic design",
        "poster-like composition",
        "clear hierarchy",
        "bold shapes",
        "limited palette",
        "print-ready layout",
    ),
    "Illustration": (
        "detailed illustration",
        "cohesive style",
        "readable shapes",
        "intentional composition",
        "handcrafted look",
    ),
    "Anime/Manga": (
        "anime/manga illustration",
        "clean linework",
        "cel shading",
        "expressive character design",
        "vibrant palette",
    ),
    "Pixel Art": ("pixel art", "16-bit", "limited palette", "pixel-perfect"),
    "Vector": ("vector illustration", "flat colors", "clean shapes", "crisp edges", "smooth curves"),
    "Technical": ("technical illustration", "clean lines", "diagrammatic layout", "precise geometry", "labels and callouts"),
    "Printmaking": ("printmaking", "ink on paper", "handcrafted texture", "carved lines", "high contrast"),
    "Experimental": ("experimental aesthetic", "bold composition", "graphic lighting", "textural detail"),
    "Color Grade": ("intentional color grade", "filmic tone mapping"),
    "Fine Art": ("fine art", "museum-quality", "traditional techniques", "gallery piece", "handcrafted"),
    "Mixed Media": ("mixed media artwork", "layered textures", "handcrafted marks", "tactile surface"),
    "Street Art": ("street art mural", "spray paint texture", "urban wall", "bold graphic shapes"),
}

CATEGORY_BASE_SUFFIX = {
    "Cinema": (
        "filmic color science",
        "smooth highlight rolloff",
        "deep blacks",
        "subtle film grain",
        "soft halation",
        "high dynamic range",
    ),
    "Photography": (
        "sharp focus",
        "high detail",
        "balanced exposure",
        "fine texture detail",
        "natural contrast",
        "clean highlights",
    ),
    "Product": (
        "crisp edges",
        "clean specular highlights",
        "premium look",
        "high detail",
        "minimal clutter",
    ),
    "Fashion": (
        "editorial color grade",
        "sharp focus",
        "skin texture",
        "catchlights",
        "high detail",
    ),
    "Architecture/Interior": (
        "crisp lines",
        "balanced exposure",
        "clean shadows",
        "high detail",
        "material realism",
    ),
    "Nature": (
        "natural color",
        "clean contrast",
        "high detail",
        "fine microtexture",
        "realistic atmosphere",
    ),
    "3D/CG": (
        "clean render",
        "high detail",
        "sharp edges",
        "high resolution",
        "clean shading",
    ),
    "Graphic Design": (
        "crisp edges",
        "high contrast",
        "clean alignment",
        "balanced negative space",
        "print texture",
    ),
    "Illustration": ("cohesive palette", "clean composition", "high detail", "believable texture"),
    "Anime/Manga": ("high clarity", "crisp edges", "clean gradients", "sharp eyes"),
    "Pixel Art": ("crisp pixels", "dithered shading", "readable silhouette", "sprite-like clarity"),
    "Vector": ("clean layout", "consistent stroke weight", "crisp edges", "smooth curves"),
    "Technical": ("high legibility", "crisp lines", "precise layout", "flat lighting"),
    "Printmaking": ("paper texture", "ink texture", "rough edges", "high contrast"),
    "Experimental": ("intentional design", "high contrast", "tactile texture", "coherent palette"),
    "Color Grade": ("smooth highlight rolloff", "clean shadows", "color separation", "balanced contrast"),
    "Fine Art": ("high detail", "handcrafted surface texture", "gallery lighting", "balanced composition"),
    "Mixed Media": ("high detail", "tactile texture", "paper grain", "layered depth", "cohesive composition"),
    "Street Art": ("bold color", "high contrast", "wall texture", "urban grit", "spray paint overspray"),
}


@dataclass(frozen=True)
class StyleSpec:
    id: str
    name: str
    category: str
    tags: Sequence[str]
    z_prefix: Sequence[str]
    z_suffix: Sequence[str]
    flux_suffix_sentences: Sequence[str]


def z_join(parts: Sequence[str]) -> str:
    parts2 = [p.strip() for p in parts if (p or "").strip()]
    # Stable de-dupe (case-insensitive) so base fragments don't create repeats.
    seen = set()
    out: List[str] = []
    for p in parts2:
        k = p.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return Z_SEP.join(out)


def flux_join_sentences(parts: Sequence[str]) -> str:
    # Keep Flux guidance in mind: prose works well, and the model doesn't support negative prompts.
    parts2 = [p.strip().rstrip(".") for p in parts if (p or "").strip()]
    return ". ".join(parts2).strip() + ("." if parts2 else "")


def to_style_dict(s: StyleSpec) -> Dict:
    base_prefix = CATEGORY_BASE_PREFIX.get(s.category, ())
    base_suffix = CATEGORY_BASE_SUFFIX.get(s.category, ())
    d = {
        "id": s.id,
        "name": s.name,
        "category": s.category,
        "default": {
            "prefix": z_join(tuple(base_prefix) + tuple(s.z_prefix)),
            "suffix": z_join(tuple(s.z_suffix) + tuple(base_suffix)),
        },
        "models": {
            # For FLUX 2 Klein, we keep style annotations at the end so the user's prompt
            # can still lead with the subject/action (word order matters).
            "flux_2_klein": {"prefix": "", "suffix": flux_join_sentences(s.flux_suffix_sentences)},
        },
        "tags": list(s.tags),
    }
    return d


def write_pack(filename: str, styles: Iterable[StyleSpec]) -> None:
    os.makedirs(PACKS_DIR, exist_ok=True)
    path = os.path.join(PACKS_DIR, filename)
    payload = {"version": 1, "styles": [to_style_dict(s) for s in styles]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def _make_id(prefix: str, name: str) -> str:
    base = "".join(ch.lower() if (ch.isalnum()) else "_" for ch in name).strip("_")
    while "__" in base:
        base = base.replace("__", "_")
    return f"{prefix}_{base}"


def _uniq(specs: List[StyleSpec]) -> List[StyleSpec]:
    seen = set()
    out: List[StyleSpec] = []
    for s in specs:
        if s.id in seen:
            raise ValueError(f"duplicate style id: {s.id}")
        seen.add(s.id)
        out.append(s)
    return out


def build() -> None:
    # Shared, reusable FLUX lighting phrases (keep them positive and concrete).
    flux_light_soft_window = (
        "Lighting: soft, diffused natural light from a large window camera-left, gentle shadows"
    )
    flux_light_dramatic_side = "Lighting: dramatic side lighting with deep shadows and bright highlights"
    flux_light_golden_back = "Lighting: golden hour backlight with subtle lens flare and warm rim light"
    flux_light_overcast = "Lighting: overcast daylight, even illumination, soft shadow transitions"
    flux_light_studio_softbox = "Lighting: studio strobe with a large softbox, clean specular highlights"
    flux_light_neon = "Lighting: mixed neon and streetlight sources, colored rim light, reflective surfaces"

    # A small seed set that we can scale via curated variations.
    cinema: List[StyleSpec] = []
    photo: List[StyleSpec] = []
    illustration: List[StyleSpec] = []
    graphic: List[StyleSpec] = []
    cg3d: List[StyleSpec] = []
    experimental: List[StyleSpec] = []
    arch: List[StyleSpec] = []
    fashion: List[StyleSpec] = []
    product: List[StyleSpec] = []
    nature: List[StyleSpec] = []
    grades: List[StyleSpec] = []
    fine_art: List[StyleSpec] = []
    mixed_media: List[StyleSpec] = []
    street_art: List[StyleSpec] = []

    def illustration_category(style_name: str) -> str:
        """Small UX win: split illustration-heavy styles into browsable buckets."""
        n = (style_name or "").casefold()
        if any(k in n for k in ("anime", "manga", "chibi", "mecha")):
            return "Anime/Manga"
        if "pixel" in n:
            return "Pixel Art"
        if any(k in n for k in ("diagram", "blueprint", "technical")):
            return "Technical"
        if any(k in n for k in ("linocut", "woodcut", "engraving", "etching", "ukiyo", "stippling")):
            return "Printmaking"
        if any(k in n for k in ("vector", "isometric")):
            return "Vector"
        return "Illustration"

    # --- Cinema / film looks ---
    cinema.append(
        StyleSpec(
            id="cinematic_anamorphic",
            name="Cinematic Anamorphic",
            category="Cinema",
            tags=("cinematic", "film", "anamorphic"),
            z_prefix=("cinematic", "anamorphic lens", "shallow depth of field", "dramatic lighting"),
            z_suffix=("film grain", "subtle halation", "rich contrast", "color graded"),
            flux_suffix_sentences=(
                "Style: cinematic anamorphic film still, shallow depth of field",
                flux_light_dramatic_side,
                "Mood: tense, grounded, realistic",
                "Texture: subtle film grain and halation",
            ),
        )
    )

    cinema_core = [
        ("Film Noir", ("film noir", "high contrast", "hard shadows", "black and white"), flux_light_dramatic_side),
        ("Neo Noir", ("neo-noir", "moody contrast", "deep shadows", "night scene"), flux_light_neon),
        ("Gritty Crime Thriller", ("gritty crime thriller", "handheld feel", "muted colors"), flux_light_dramatic_side),
        ("Dreamy Romance", ("dreamy cinematic", "soft focus", "warm tones"), flux_light_golden_back),
        ("Sci-Fi Neon", ("sci-fi cinematic", "neon glow", "wet streets", "atmospheric haze"), flux_light_neon),
        ("Epic Fantasy", ("epic cinematic", "volumetric light rays", "dramatic scale"), "Lighting: god rays through haze, high dynamic range"),
        ("Documentary Handheld", ("documentary", "handheld camera", "natural light", "authentic moments"), flux_light_overcast),
        ("Vintage 16mm", ("16mm film look", "visible grain", "soft contrast"), "Lighting: practical tungsten lamps, warm falloff"),
        ("Vintage 35mm", ("35mm film look", "gentle grain", "natural color"), flux_light_soft_window),
        ("IMAX Blockbuster", ("large format cinema", "crisp detail", "dramatic composition"), "Lighting: high-impact key light with controlled fill"),
        ("Horror Suspense", ("cinematic horror", "low key lighting", "ominous atmosphere"), flux_light_dramatic_side),
        ("Cozy Slice-of-Life", ("warm cinematic", "intimate framing", "soft contrast"), flux_light_soft_window),
    ]
    for name, ztags, flux_light in cinema_core:
        cinema.append(
            StyleSpec(
                id=_make_id("cin", name),
                name=name,
                category="Cinema",
                tags=("cinema", "film"),
                z_prefix=ztags,
                z_suffix=("cinematic color grade", "subtle film grain"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, cinematic film still",
                    flux_light,
                    "Mood: cohesive, story-driven",
                ),
            )
        )

    cinema_more = [
        ("Desert Western", ("cinematic western", "wide landscape", "dusty atmosphere"), "Lighting: harsh sun with long shadows, heat haze"),
        ("Cold War Spy Thriller", ("spy thriller", "moody interiors", "controlled palette"), flux_light_dramatic_side),
        ("Post-Apocalyptic", ("post-apocalyptic cinematic", "weathered textures", "dusty haze"), "Lighting: harsh daylight filtered through dust and smoke"),
        ("Space Opera", ("space opera cinematic", "high contrast", "dramatic scale"), "Lighting: bright rim light against deep space, high contrast"),
        ("Underwater Drama", ("underwater cinematic", "caustics", "floating particles"), "Lighting: underwater caustic patterns, shafts of light through water"),
        ("Candlelit Period Drama", ("period drama", "candlelit", "warm shadows"), "Lighting: warm candlelight with soft falloff and deep shadows"),
        ("Rainy Night Alley", ("cinematic night scene", "rainy street", "wet reflections"), flux_light_neon),
        ("Bright Day Comedy", ("bright cinematic", "clean colors", "lighthearted tone"), "Lighting: bright daylight with soft fill, cheerful contrast"),
        ("Mystery Thriller", ("mystery thriller", "moody", "subtle haze"), flux_light_dramatic_side),
        ("High-Speed Action", ("action blockbuster", "dynamic camera", "sharp highlights"), "Lighting: high-impact lighting, crisp highlights, controlled motion blur"),
        ("Courtroom Drama", ("dramatic courtroom scene", "serious tone", "clean framing"), flux_light_soft_window),
        ("Coming-of-Age", ("warm cinematic", "naturalistic", "gentle grain"), flux_light_golden_back),
        ("Slow Cinema", ("slow cinema", "minimalist framing", "quiet atmosphere"), flux_light_overcast),
        ("Surreal Dream Sequence", ("surreal cinematic", "soft diffusion", "dreamlike haze"), "Lighting: ethereal soft light with gentle bloom and haze"),
        ("War Documentary", ("war documentary", "gritty realism", "handheld"), flux_light_overcast),
        ("Sports Broadcast Cinematic", ("sports cinematic", "telephoto compression", "fast shutter feel"), "Lighting: stadium lights, crisp highlights, dynamic contrast"),
        ("Retro Futurism", ("retro futurism", "clean shapes", "neon accents"), flux_light_neon),
        ("Urban Nightscape", ("urban night cinematic", "city lights", "bokeh"), flux_light_neon),
        ("Snowstorm Survival", ("cinematic survival", "snowstorm", "cold palette"), "Lighting: cold overcast light with blowing snow and low visibility"),
        ("Tropical Heat", ("cinematic tropical", "humid atmosphere", "vibrant greens"), "Lighting: bright sun filtered through foliage, humid haze"),
        ("Firelit Camp Scene", ("cinematic firelight", "warm glow", "night ambience"), "Lighting: warm firelight with flicker and soft smoke haze"),
        ("Neon Club Scene", ("cinematic club", "colored lights", "smoke haze"), "Lighting: saturated neon lights, moving beams, haze in the air"),
        ("Foggy Harbor", ("cinematic fog", "dock lights", "atmospheric depth"), "Lighting: fog diffusion around practical lights, soft silhouettes"),
        ("Vintage Home Video", ("retro home video", "soft focus", "analog feel"), "Lighting: simple indoor practical lights, gentle falloff"),
        ("Coastal Road Trip", ("cinematic road trip", "sunlit coastline", "nostalgic tone"), flux_light_golden_back),
        ("Subway Platform", ("urban cinematic", "subway platform", "gritty realism"), "Lighting: practical fluorescent lights with mixed color temperature"),
        ("Rainy Car Interior", ("cinematic car interior", "rain streaks", "reflections"), "Lighting: streetlights and dashboard glow, rain reflections on glass"),
        ("Desaturated War Film", ("war film look", "desaturated palette", "gritty texture"), flux_light_overcast),
        ("Bright Musical Number", ("classic musical", "clean stage lighting", "bold colors"), "Lighting: bright stage key light with clean fill and saturated colors"),
        ("Sunlit Kitchen Scene", ("slice-of-life cinematic", "sunlit interior", "warm realism"), flux_light_soft_window),
        ("Neon Diner", ("retro diner cinematic", "neon accents", "night scene"), flux_light_neon),
        ("Storm Chase", ("cinematic storm", "dramatic clouds", "high tension"), "Lighting: storm light with dramatic contrast and wind-driven rain"),
        ("Quiet Library Mystery", ("mystery cinematic", "dusty light beams", "quiet tension"), "Lighting: soft window beams through dust, warm practical accents"),
    ]
    for name, ztags, flux_light in cinema_more:
        cinema.append(
            StyleSpec(
                id=_make_id("cin", name),
                name=name,
                category="Cinema",
                tags=("cinema", "film"),
                z_prefix=ztags,
                z_suffix=("cinematic color grade", "subtle film grain"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, cinematic film still",
                    flux_light,
                    "Mood: cinematic, cohesive, story-driven",
                ),
            )
        )

    # --- Color grades (category-agnostic) ---
    grade_specs = [
        ("Teal and Orange", ("cinematic color grade", "teal and orange", "rich contrast"), "Color grade: teal shadows and warm highlights, cinematic contrast"),
        ("Muted Pastels", ("muted pastel palette", "soft contrast", "gentle highlights"), "Color palette: muted pastels with soft contrast"),
        ("High Contrast Monochrome", ("black and white", "high contrast", "deep blacks"), "Color grade: monochrome with deep blacks and bright whites"),
        ("Warm Vintage", ("warm vintage grade", "slightly faded", "soft highlights"), "Color grade: warm vintage tones with gentle fade"),
        ("Cool Desaturated", ("cool tones", "desaturated palette", "clean contrast"), "Color palette: cool and slightly desaturated"),
        ("Bleach Bypass Look", ("bleach bypass look", "desaturated", "high contrast"), "Color grade: desaturated high-contrast bleach-bypass look"),
        ("Soft Cinematic Pastel", ("soft cinematic", "pastel grade", "subtle bloom"), "Color grade: soft cinematic pastel with gentle bloom"),
        ("Vibrant Pop", ("vibrant colors", "punchy saturation", "crisp contrast"), "Color grade: vibrant, punchy saturation with crisp contrast"),
        ("Earthy Documentary", ("earthy tones", "natural contrast", "subtle grain"), "Color palette: earthy documentary tones, natural contrast"),
        ("Neon Night Grade", ("neon grade", "deep shadows", "bright neon"), "Color grade: deep shadows with bright neon highlights"),
        ("Golden Hour Warmth", ("golden hour grade", "warm highlights", "soft shadows"), "Color grade: golden-hour warmth with soft shadow rolloff"),
        ("Cold Winter Blues", ("cold winter grade", "blue shadows", "crisp air"), "Color palette: cold winter blues with crisp contrast"),
        ("Sepia Tone", ("sepia tone", "vintage print", "soft contrast"), "Color grade: sepia tone with vintage print feel"),
        ("Film Grain Matte", ("matte grade", "lifted blacks", "film grain"), "Color grade: matte look with lifted blacks and fine grain"),
        ("Clean Commercial", ("clean commercial grade", "neutral whites", "natural color"), "Color grade: clean commercial neutrality with accurate whites"),
        ("Moody Low Saturation", ("moody", "low saturation", "deep shadows"), "Color palette: low saturation with deep shadows and moody contrast"),
        ("Bright Airy", ("bright airy", "high key", "soft highlights"), "Color grade: bright airy look with soft highlights"),
        ("Vintage Slide Look", ("vintage slide look", "rich reds", "crisp contrast"), "Color grade: rich reds and crisp contrast, vintage slide feel"),
        ("Cyanotype Look", ("cyanotype look", "blue monochrome", "paper texture"), "Color grade: blue monochrome cyanotype print feel"),
        ("Duotone Blue/Red", ("duotone", "blue and red", "graphic contrast"), "Color grade: duotone blue and red with graphic contrast"),
    ]
    for name, ztags, flux_line in grade_specs:
        grades.append(
            StyleSpec(
                id=_make_id("grade", name),
                name=f"Color Grade: {name}",
                category="Color Grade",
                tags=("grade", "color"),
                z_prefix=ztags,
                z_suffix=("clean tones",),
                flux_suffix_sentences=(
                    "Style: realistic image with an intentional color grade",
                    flux_line,
                    "Tone mapping: smooth highlights and coherent shadows",
                ),
            )
        )

    # --- Photography ---
    photo.append(
        StyleSpec(
            id="clean_product_photo",
            name="Clean Product Photo",
            category="Product",
            tags=("product", "studio", "commercial"),
            z_prefix=("studio product photography", "clean background", "softbox lighting", "sharp focus"),
            z_suffix=("high detail", "minimal reflections", "crisp edges"),
            flux_suffix_sentences=(
                "Style: professional studio product photograph on a clean seamless background",
                flux_light_studio_softbox,
                "Composition: centered, clean silhouette, crisp edges",
            ),
        )
    )

    portrait_light_setups = [
        ("Rembrandt Portrait", ("portrait photography", "Rembrandt lighting", "85mm lens", "shallow depth of field"), flux_light_soft_window),
        ("Butterfly Lighting Portrait", ("portrait photography", "butterfly lighting", "beauty dish", "clean catchlights"), "Lighting: beauty dish overhead, soft fill, clean shadows under cheekbones"),
        ("Split Lighting Portrait", ("portrait photography", "split lighting", "high contrast"), flux_light_dramatic_side),
        ("High Key Studio Portrait", ("high key portrait", "bright background", "soft shadows"), "Lighting: broad soft key, high fill ratio, bright seamless background"),
        ("Low Key Studio Portrait", ("low key portrait", "deep shadows", "dramatic contrast"), flux_light_dramatic_side),
        ("Golden Hour Portrait", ("golden hour portrait", "warm backlight", "natural skin tones"), flux_light_golden_back),
        ("Street Portrait", ("street portrait", "candid", "natural light"), flux_light_overcast),
        ("Editorial Portrait", ("editorial portrait", "stylized lighting", "clean composition"), flux_light_studio_softbox),
        ("Rim Light Portrait", ("portrait photography", "rim light", "dark background", "subject separation"), "Lighting: strong rim light from behind, soft key, deep background"),
        ("Broad Lighting Portrait", ("portrait photography", "broad lighting", "soft shadows"), "Lighting: key light on the camera side of the face, soft fill"),
        ("Short Lighting Portrait", ("portrait photography", "short lighting", "sculpted face"), "Lighting: key light on the far side of the face, controlled fill"),
    ]
    for name, ztags, flux_light in portrait_light_setups:
        photo.append(
            StyleSpec(
                id=_make_id("photo", name),
                name=name,
                category="Photography",
                tags=("photo", "portrait"),
                z_prefix=ztags,
                z_suffix=("natural skin texture", "sharp eyes", "subtle background blur"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, realistic photograph",
                    flux_light,
                    "Focus: sharp eyes, natural skin texture, gentle background blur",
                ),
            )
        )

    photo_genres = [
        ("Street Photography", ("street photography", "candid moment", "natural light"), flux_light_overcast),
        ("Travel Documentary", ("travel documentary photography", "authentic details", "natural color"), flux_light_soft_window),
        ("Food Photography", ("food photography", "shallow depth of field", "appetizing lighting"), flux_light_soft_window),
        ("Macro Photography", ("macro photography", "extreme close-up", "micro texture", "shallow depth of field"), "Lighting: diffused macro lighting, controlled reflections, crisp microtexture"),
        ("Wildlife Photography", ("wildlife photography", "telephoto lens", "natural habitat"), flux_light_golden_back),
        ("Architecture Photography", ("architecture photography", "straight lines", "clean geometry"), flux_light_overcast),
        ("Interior Photography", ("interior photography", "wide angle lens", "natural window light"), flux_light_soft_window),
        ("Aerial Drone Photo", ("aerial drone photography", "top-down view", "sharp detail"), "Lighting: clear daylight with defined but soft shadows"),
        ("Long Exposure", ("long exposure photography", "motion blur trails", "tripod shot"), "Lighting: dusk ambient with long exposure light trails"),
        ("Black and White", ("black and white photography", "strong tonal range", "fine grain"), flux_light_dramatic_side),
        ("Infrared", ("infrared photography", "surreal foliage tones", "high contrast"), "Lighting: bright midday sun, strong infrared contrast"),
        ("Tilt-Shift Miniature", ("tilt-shift photography", "miniature effect", "selective focus"), "Lighting: daylight with crisp miniature-scale shadows"),
        ("Night Street Photo", ("night street photography", "city lights", "bokeh", "wet reflections"), flux_light_neon),
        ("Concert Photography", ("concert photography", "stage lights", "dynamic contrast"), "Lighting: dramatic stage lighting with colored highlights"),
        ("Automotive Photo", ("automotive photography", "clean reflections", "sharp lines"), "Lighting: controlled reflections, crisp highlights, studio or golden hour"),
        ("Wedding Photo", ("wedding photography", "soft romantic light", "candid moments"), flux_light_golden_back),
        ("Still Life Photo", ("still life photography", "careful composition", "soft shadows"), flux_light_soft_window),
        ("Flat Lay", ("flat lay photography", "top-down", "organized composition"), "Lighting: soft overhead diffused light, minimal harsh shadows"),
        ("On-Camera Flash", ("direct flash photography", "hard shadows", "party snapshot"), "Lighting: on-camera flash, hard shadows, punchy contrast"),
        ("Ring Flash Portrait", ("ring flash portrait", "crisp catchlight", "high clarity"), "Lighting: ring flash with crisp shadows and clean contrast"),
        ("Cinematic Backlight", ("backlit photography", "rim light", "atmospheric haze"), flux_light_golden_back),
        ("Silhouette", ("silhouette photography", "strong backlight", "clean outline"), "Lighting: strong backlight creating a crisp silhouette"),
        ("Rainy Window", ("moody window scene", "raindrops on glass", "soft bokeh"), flux_light_soft_window),
        ("Astrophotography", ("astrophotography", "night sky", "stars", "clean exposure"), "Lighting: moonless night, crisp stars, low noise look"),
        ("Milky Way Landscape", ("milky way", "night landscape", "wide angle", "stars"), "Lighting: starlight and faint airglow, crisp night contrast"),
        ("Underwater Photo", ("underwater photography", "clear water", "floating particles", "blue tones"), "Lighting: underwater light beams and caustics, soft particulate haze"),
        ("Real Estate Photo", ("real estate photography", "wide angle", "clean lines", "bright interior"), flux_light_soft_window),
        ("Sports Action Freeze", ("sports photography", "fast shutter", "sharp action", "telephoto"), "Lighting: stadium lighting, crisp highlights, frozen motion"),
        ("Motion Blur Action", ("motion blur", "panning shot", "dynamic movement"), "Lighting: controlled highlights supporting motion blur and panning"),
    ]
    for name, ztags, flux_light in photo_genres:
        photo.append(
            StyleSpec(
                id=_make_id("photo", name),
                name=name,
                category="Photography",
                tags=("photo",),
                z_prefix=ztags,
                z_suffix=("realistic detail", "clean color", "natural contrast"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, realistic photograph",
                    flux_light,
                    "Mood: grounded, natural, believable",
                ),
            )
        )

    # Film / color processes (generic look descriptors, not brand names)
    film_looks = [
        ("Soft 35mm Film Look", ("35mm film look", "soft contrast", "gentle grain"), flux_light_soft_window),
        ("Vibrant Slide Film Look", ("slide film look", "punchy colors", "crisp contrast"), "Lighting: bright daylight with saturated color separation"),
        ("Muted Documentary Film", ("documentary film look", "muted palette", "fine grain"), flux_light_overcast),
        ("Warm Tungsten Film", ("warm tungsten film look", "practical lights", "soft glow"), "Lighting: warm practical lamps, gentle falloff, cozy ambience"),
        ("Cool Blue Hour Film", ("blue hour film look", "cool tones", "city lights"), "Lighting: blue hour ambient mixed with warm practicals, subtle glow"),
    ]
    for name, ztags, flux_light in film_looks:
        photo.append(
            StyleSpec(
                id=_make_id("film", name),
                name=name,
                category="Photography",
                tags=("film", "photo"),
                z_prefix=ztags,
                z_suffix=("natural skin tones", "subtle halation", "film grain"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, realistic photograph",
                    flux_light,
                    "Texture: subtle grain and gentle halation",
                ),
            )
        )

    # Technique-focused photo styles.
    photo_techniques = [
        ("Deep Focus", ("deep focus", "sharp foreground and background", "clean optics"), "Lighting: even controlled light supporting deep focus clarity"),
        ("Shallow DOF Bokeh", ("shallow depth of field", "creamy bokeh", "subject isolation"), flux_light_soft_window),
        ("High Dynamic Range", ("high dynamic range", "balanced highlights and shadows", "realistic tones"), "Lighting: naturalistic scene lighting with preserved highlights"),
        ("Soft Diffusion Glow", ("soft diffusion", "gentle glow", "dreamy highlights"), "Lighting: soft diffused key light with gentle bloom"),
        ("Hard Flash Shadow", ("hard flash", "sharp shadows", "crisp contrast"), "Lighting: hard flash with sharp shadows and specular highlights"),
        ("Moody Window Light", ("window light", "soft shadows", "intimate mood"), flux_light_soft_window),
        ("Backlit Rim Light", ("backlit", "rim light", "atmospheric haze"), flux_light_golden_back),
        ("Volumetric Light Beams", ("volumetric light", "god rays", "haze"), "Lighting: strong directional light creating volumetric beams through haze"),
        ("Rain Reflections", ("wet streets", "reflections", "night bokeh"), flux_light_neon),
        ("Minimalist Studio", ("minimalist studio photo", "clean seamless", "controlled reflections"), flux_light_studio_softbox),
        ("Close-Up Texture Study", ("close-up photo", "micro texture", "tactile detail"), "Lighting: raking light to reveal texture and surface detail"),
        ("Soft Overcast Natural", ("soft overcast", "even skin tones", "gentle contrast"), flux_light_overcast),
        ("High Key Commercial", ("high key commercial", "clean whites", "soft shadows"), "Lighting: large soft sources with high fill for clean whites"),
        ("Low Key Dramatic", ("low key", "deep shadows", "controlled highlights"), flux_light_dramatic_side),
        ("Specular Highlight Study", ("specular highlights", "controlled reflections", "shiny surfaces"), "Lighting: small hard sources for crisp specular highlights with controlled fill"),
    ]
    for name, ztags, flux_light in photo_techniques:
        photo.append(
            StyleSpec(
                id=_make_id("tech", name),
                name=name,
                category="Photography",
                tags=("photo", "technique"),
                z_prefix=ztags,
                z_suffix=("realistic detail", "natural contrast"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, realistic photograph",
                    flux_light,
                    "Focus: clear subject, believable materials, coherent lighting",
                ),
            )
        )

    # Lens / camera vibes (helpful shorthand; keep it generic).
    lens_vibes = [
        ("24mm Wide Angle", ("wide angle", "24mm lens feel", "strong perspective"), "Composition: wide-angle perspective with strong leading lines"),
        ("35mm Documentary", ("35mm lens feel", "documentary framing", "natural perspective"), "Composition: documentary framing with natural perspective"),
        ("50mm Natural", ("50mm lens feel", "natural perspective", "balanced framing"), "Composition: balanced perspective and natural proportions"),
        ("85mm Portrait", ("85mm lens feel", "portrait compression", "shallow depth of field"), "Composition: flattering compression with shallow depth of field"),
        ("135mm Telephoto", ("telephoto compression", "135mm lens feel", "compressed background"), "Composition: strong telephoto compression and layered background"),
    ]
    for name, ztags, flux_comp in lens_vibes:
        photo.append(
            StyleSpec(
                id=_make_id("lens", name),
                name=f"Lens Vibe: {name}",
                category="Photography",
                tags=("photo", "lens"),
                z_prefix=ztags,
                z_suffix=("clean optics", "natural contrast"),
                flux_suffix_sentences=(
                    "Style: realistic photograph with a specific lens perspective",
                    flux_comp,
                    flux_light_overcast,
                ),
            )
        )

    # --- Illustration ---
    illustration.append(
        StyleSpec(
            id="ink_wash_illustration",
            name="Ink Wash Illustration",
            category="Illustration",
            tags=("ink", "wash", "illustration"),
            z_prefix=("ink wash illustration", "expressive brushwork", "paper texture"),
            z_suffix=("soft diffusion", "monochrome ink tones", "subtle bleeding edges"),
            flux_suffix_sentences=(
                "Style: ink wash illustration on textured paper",
                "Lighting: soft ambient light emphasizing paper texture and brush edges",
                "Mood: calm, minimal, expressive",
            ),
        )
    )

    illustration.append(
        StyleSpec(
            id="anime_style",
            name="Anime Style",
            category="Anime/Manga",
            tags=("anime", "manga", "illustration"),
            z_prefix=("anime style", "clean line art", "cel shading", "vibrant colors"),
            z_suffix=("sharp eyes", "expressive face", "crisp edges", "detailed background"),
            flux_suffix_sentences=(
                "Style: anime illustration with clean linework and cel shading",
                "Lighting: clear, readable key light with soft fill",
                "Mood: vibrant, expressive, high clarity",
            ),
        )
    )

    art_media = [
        ("Watercolor Illustration", ("watercolor illustration", "translucent washes", "soft edges", "granulation", "textured paper")),
        ("Gouache Painting", ("gouache painting", "opaque matte paint", "bold shapes", "flat color blocks", "brush strokes")),
        ("Oil Painting", ("oil painting", "painterly", "rich brush strokes", "impasto texture", "canvas texture")),
        ("Acrylic Painting", ("acrylic painting", "bold brushwork", "layered paint", "matte finish", "clean edges")),
        ("Colored Pencil Drawing", ("colored pencil drawing", "fine hatching", "paper grain", "soft shading", "hand-drawn texture")),
        ("Graphite Pencil Sketch", ("graphite pencil sketch", "linework", "shaded rendering", "paper texture", "loose sketch")),
        ("Charcoal Drawing", ("charcoal drawing", "smudged shading", "dusty texture", "high contrast", "paper grain")),
        ("Pastel Drawing", ("soft pastel drawing", "powdery texture", "blended gradients", "soft edges", "paper tooth")),
        ("Ink Line Art", ("ink line art", "clean linework", "high contrast", "minimal shading", "smooth contours")),
        ("Marker Illustration", ("marker illustration", "smooth gradients", "bold shapes", "clean outlines", "paper texture")),
        ("Children's Book Illustration", ("children's book illustration", "storybook style", "soft shapes", "warm palette", "gentle shading")),
        ("Graphic Novel Panel", ("graphic novel panel", "dramatic inking", "heavy shadows", "panel composition", "high contrast")),
        ("Manga Panel", ("manga panel", "black ink", "screentones", "dynamic paneling", "clean linework")),
        ("Anime Keyframe", ("anime key visual", "clean lineart", "cel shading", "expressive faces", "vibrant colors")),
        ("Pixel Art", ("pixel art", "16-bit", "limited palette", "dithering", "crisp pixels")),
        ("Vector Flat", ("vector illustration", "flat colors", "clean shapes", "minimal shading", "crisp edges")),
        ("Isometric Vector", ("isometric vector illustration", "clean geometry", "consistent shadows", "flat colors", "crisp lines")),
        ("Technical Diagram", ("technical illustration", "clean lines", "diagrammatic layout", "labeled parts", "flat lighting")),
        ("Linocut Print", ("linocut print", "carved line texture", "rough edges", "high contrast", "ink on paper")),
        ("Woodcut Print", ("woodcut print", "carved texture", "bold lines", "high contrast", "ink on paper")),
        ("Engraving", ("engraving", "fine hatching", "crosshatching", "vintage print", "antique paper")),
        ("Etching", ("etching", "crosshatching", "fine lines", "paper texture", "vintage print")),
        ("Stippling", ("stippling", "ink dots", "dot shading", "high detail", "paper texture")),
        ("Pointillism", ("pointillism", "tiny color dots", "optical blending", "painterly", "soft edges")),
        ("Ukiyo-e Woodblock", ("ukiyo-e woodblock print", "flat color areas", "stylized linework", "traditional print texture", "limited palette")),
        ("Impressionist Painting", ("impressionist painting", "broken brush strokes", "soft edges", "painterly light", "colorful palette")),
        ("Expressionist Painting", ("expressionist painting", "bold color", "emotional brushwork", "strong shapes", "high contrast")),
        ("Minimal Line Illustration", ("minimal line illustration", "single line drawing", "clean negative space", "simple forms", "minimal shading")),
        ("Sticker Illustration", ("sticker illustration", "thick outline", "flat colors", "simple shading", "die-cut sticker")),
        ("Chalkboard Sketch", ("chalkboard drawing", "chalk texture", "hand-drawn", "dusty strokes", "blackboard background")),
        ("Blueprint Drawing", ("blueprint drawing", "white lines on blue", "technical diagram", "schematic layout", "clean labels")),
        ("Paper Cutout", ("paper cutout illustration", "layered paper", "handcrafted", "soft cast shadows", "cut edges")),
        ("Collage Illustration", ("collage illustration", "torn paper edges", "mixed media", "layered textures", "paper grain")),
    ]
    for name, ztags in art_media:
        illustration.append(
            StyleSpec(
                id=_make_id("illu", name),
                name=name,
                category=illustration_category(name),
                tags=("illustration",),
                z_prefix=ztags,
                z_suffix=("clean composition", "cohesive palette"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}",
                    "Lighting: soft even light that supports the medium",
                    "Mood: consistent, intentional, cohesive",
                ),
            )
        )

    illustration_movements = [
        ("Art Nouveau", ("art nouveau illustration", "ornamental lines", "flowing forms")),
        ("Art Deco Illustration", ("art deco illustration", "geometric elegance", "stylized forms")),
        ("Surrealism", ("surreal illustration", "dream logic", "unexpected juxtapositions")),
        ("Cubism", ("cubist painting style", "geometric planes", "fragmented forms")),
        ("Fauvism", ("fauvist colors", "bold palette", "simplified shapes")),
        ("Minimalist Illustration", ("minimalist illustration", "simple forms", "strong negative space")),
        ("Retro 1950s Illustration", ("retro 1950s illustration", "mid-century shapes", "limited palette")),
        ("Vintage Scientific Plate", ("vintage scientific illustration", "fine lines", "paper texture")),
        ("Fantasy Map", ("fantasy map illustration", "ink lines", "parchment texture")),
        ("Isometric Pixel Art", ("isometric pixel art", "limited palette", "crisp pixels")),
        ("Chibi Character", ("chibi style", "cute proportions", "clean outlines")),
        ("Mecha Blueprint", ("mecha blueprint", "technical drawing", "clean labels")),
        ("Storybook Pencil", ("storybook pencil drawing", "soft shading", "gentle lines")),
        ("Painterly Concept Art", ("painterly concept art", "loose brushwork", "atmospheric perspective")),
    ]
    for name, ztags in illustration_movements:
        illustration.append(
            StyleSpec(
                id=_make_id("illu", name),
                name=name,
                category=illustration_category(name),
                tags=("illustration", "movement"),
                z_prefix=ztags,
                z_suffix=("cohesive palette", "clean composition"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()} illustration",
                    "Lighting: soft even light appropriate to the medium",
                    "Mood: cohesive and intentional",
                ),
            )
        )

    # --- Fine art / artistic styles ---
    flux_light_gallery = "Lighting: soft gallery spotlights with gentle falloff and controlled highlights"

    def add_art_style(
        bucket: List[StyleSpec],
        id_prefix: str,
        name: str,
        category: str,
        z_prefix: Sequence[str],
        z_suffix: Sequence[str],
        flux_suffix_sentences: Sequence[str],
        tags: Sequence[str],
    ) -> None:
        bucket.append(
            StyleSpec(
                id=_make_id(id_prefix, name),
                name=name,
                category=category,
                tags=tuple(tags),
                z_prefix=z_prefix,
                z_suffix=z_suffix,
                flux_suffix_sentences=flux_suffix_sentences,
            )
        )

    fine_art_specs = [
        (
            "Old Master Chiaroscuro",
            ("old master painting", "baroque chiaroscuro", "tenebrism", "oil on canvas"),
            ("warm highlights", "deep shadows", "classical composition"),
            (
                "Style: old master oil painting with dramatic chiaroscuro",
                flux_light_dramatic_side,
                "Texture: rich brushwork and subtle canvas grain",
            ),
        ),
        (
            "Dutch Golden Age Still Life",
            ("dutch golden age still life", "oil on canvas", "dramatic light", "rich materials"),
            ("realistic textures", "careful composition", "deep shadows"),
            (
                "Style: Dutch golden age still life oil painting",
                flux_light_dramatic_side,
                "Texture: fine brushwork, varnished depth, canvas grain",
            ),
        ),
        (
            "Baroque Religious Painting",
            ("baroque painting", "dramatic composition", "chiaroscuro", "oil on canvas"),
            ("smoke haze", "golden highlights", "deep shadows"),
            (
                "Style: baroque religious painting, dramatic and monumental",
                flux_light_dramatic_side,
                "Mood: solemn, powerful, cinematic",
            ),
        ),
        (
            "Renaissance Fresco",
            ("renaissance fresco", "classical anatomy", "balanced composition", "plaster wall texture"),
            ("muted pigments", "aged patina", "architectural framing"),
            (
                "Style: Renaissance fresco painting on plaster",
                "Lighting: soft ambient daylight like a museum interior",
                "Texture: subtle plaster grain and aged pigment",
            ),
        ),
        (
            "Rococo Pastel Elegance",
            ("rococo painting", "pastel palette", "ornate details", "soft romantic light"),
            ("delicate brushwork", "silky fabrics", "light airy mood"),
            (
                "Style: rococo fine art painting with pastel colors and ornate detail",
                flux_light_soft_window,
                "Mood: elegant, playful, airy",
            ),
        ),
        (
            "Neoclassical Painting",
            ("neoclassical painting", "clean forms", "classical composition", "marble-like skin tones"),
            ("precise edges", "balanced lighting", "restrained palette"),
            (
                "Style: neoclassical fine art painting with clean forms and balanced composition",
                flux_light_soft_window,
                "Mood: calm, disciplined, timeless",
            ),
        ),
        (
            "Romantic Sublime Landscape",
            ("romantic landscape painting", "dramatic sky", "atmospheric perspective", "sublime scale"),
            ("mist", "light rays", "painterly clouds"),
            (
                "Style: romantic landscape oil painting with sublime atmosphere",
                "Lighting: dramatic breaks in cloud cover with volumetric rays",
                "Mood: awe, grandeur, nature overpowering",
            ),
        ),
        (
            "Symbolist Dream Painting",
            ("symbolist painting", "mystical symbolism", "dreamlike atmosphere", "soft haze"),
            ("muted jewel tones", "ornamental motifs", "surreal calm"),
            (
                "Style: symbolist fine art painting, dreamlike and mystical",
                "Lighting: soft diffuse light with gentle glow",
                "Mood: enigmatic, poetic, symbolic",
            ),
        ),
        (
            "Pre-Raphaelite Detail",
            ("pre-raphaelite painting", "intricate detail", "luminous color", "naturalistic textures"),
            ("delicate florals", "sharp detail", "storybook realism"),
            (
                "Style: pre-raphaelite inspired fine art painting with meticulous detail",
                flux_light_soft_window,
                "Texture: fine brushwork with luminous color",
            ),
        ),
        (
            "Academic Realism",
            ("academic realism", "oil painting", "realistic anatomy", "studio composition"),
            ("controlled edges", "subtle gradients", "natural skin tones"),
            (
                "Style: academic realism oil painting with controlled edges",
                flux_light_soft_window,
                "Mood: refined, realistic, classical",
            ),
        ),
        (
            "Classical Portrait Painting",
            ("classical portrait painting", "oil on canvas", "soft modeling", "elegant pose"),
            ("subtle skin shading", "rich fabrics", "balanced composition"),
            (
                "Style: classical portrait oil painting",
                flux_light_soft_window,
                "Mood: dignified, timeless, refined",
            ),
        ),
        (
            "Icon Painting with Gold Leaf",
            ("icon painting", "gold leaf", "flat stylization", "ornamental halo"),
            ("tempera", "aged varnish", "ornate border"),
            (
                "Style: traditional icon painting with gold leaf accents",
                flux_light_gallery,
                "Texture: gilded highlights, painted tempera surface",
            ),
        ),
        (
            "Illuminated Manuscript",
            ("illuminated manuscript", "gold leaf", "vellum parchment", "ornate border"),
            ("medieval miniature", "fine ink lines", "decorative motifs"),
            (
                "Style: illuminated manuscript on parchment with ornate borders",
                flux_light_gallery,
                "Texture: vellum grain, gold leaf shine, ink linework",
            ),
        ),
        (
            "Persian Miniature Painting",
            ("persian miniature painting", "intricate detail", "flat perspective", "ornate patterns"),
            ("bright pigments", "gold accents", "decorative motifs"),
            (
                "Style: Persian miniature painting with intricate detail and flat perspective",
                flux_light_gallery,
                "Mood: ornate, delicate, storybook",
            ),
        ),
        (
            "Mughal Miniature Painting",
            ("mughal miniature painting", "fine detail", "flat perspective", "ornamental patterns"),
            ("jewel tones", "gold accents", "delicate linework"),
            (
                "Style: Mughal miniature painting with fine detail and ornate motifs",
                flux_light_gallery,
                "Mood: refined, decorative, historical",
            ),
        ),
        (
            "Japanese Sumi-e Ink Painting",
            ("sumi-e ink painting", "expressive brush strokes", "rice paper texture", "minimal composition"),
            ("monochrome ink", "negative space", "soft ink bleed"),
            (
                "Style: Japanese sumi-e ink painting on rice paper",
                "Lighting: soft ambient light emphasizing paper texture",
                "Mood: calm, minimal, expressive",
            ),
        ),
        (
            "Chinese Ink Landscape (Shan Shui)",
            ("shan shui ink painting", "mountain landscape", "mist", "rice paper texture"),
            ("monochrome ink", "atmospheric depth", "soft ink wash"),
            (
                "Style: Chinese ink landscape painting with misty mountains",
                "Lighting: soft diffuse light, gentle contrast",
                "Mood: serene, expansive, meditative",
            ),
        ),
        (
            "Stained Glass Art",
            ("stained glass", "lead outlines", "translucent colored glass", "ornamental pattern"),
            ("glowing light", "high contrast shapes", "jewel tones"),
            (
                "Style: stained glass artwork with bold lead lines",
                "Lighting: backlit translucent glass with glowing color",
                "Mood: luminous, ornate, sacred",
            ),
        ),
        (
            "Mosaic Tile Art",
            ("mosaic art", "tesserae", "stone tiles", "handcrafted texture"),
            ("tactile surface", "irregular pieces", "historic feel"),
            (
                "Style: mosaic tile artwork made from small tesserae",
                flux_light_gallery,
                "Texture: tactile tile surface with irregular pieces",
            ),
        ),
        (
            "Fresco Mural",
            ("fresco mural", "plaster wall texture", "pigment", "large-scale composition"),
            ("aged patina", "subtle cracks", "historic atmosphere"),
            (
                "Style: large fresco mural on plaster wall",
                "Lighting: soft ambient light revealing wall texture and patina",
                "Mood: monumental, historical, timeless",
            ),
        ),
        (
            "Encaustic Wax Painting",
            ("encaustic painting", "wax medium", "layered translucency", "tactile texture"),
            ("subtle cracks", "surface depth", "handmade feel"),
            (
                "Style: encaustic wax painting with layered translucency",
                flux_light_gallery,
                "Texture: tactile wax surface with depth and subtle cracking",
            ),
        ),
        (
            "Tempera Painting",
            ("tempera painting", "matte surface", "fine detail", "egg tempera"),
            ("clean edges", "layered strokes", "historic palette"),
            (
                "Style: egg tempera fine art painting with a matte surface",
                flux_light_gallery,
                "Texture: fine layered strokes, crisp detail",
            ),
        ),
        (
            "Impressionism (Plein Air)",
            ("plein air painting", "impressionist brushwork", "broken color", "sunlit atmosphere"),
            ("visible strokes", "soft edges", "light-filled palette"),
            (
                "Style: impressionist plein-air oil painting with broken brushwork",
                flux_light_golden_back,
                "Mood: lively, light-filled, outdoors",
            ),
        ),
        (
            "Post-Impressionist Bold Brushwork",
            ("post-impressionist painting", "bold brushwork", "strong outlines", "rich color"),
            ("textured paint", "expressive strokes", "vivid palette"),
            (
                "Style: post-impressionist painting with bold brushwork and rich color",
                flux_light_soft_window,
                "Mood: expressive, vibrant, painterly",
            ),
        ),
        (
            "Expressionism (Emotive)",
            ("expressionist painting", "emotive color", "exaggerated forms", "energetic brushwork"),
            ("strong contrast", "painterly texture", "raw emotion"),
            (
                "Style: expressionist painting with emotive color and energetic brushwork",
                "Lighting: dramatic but painterly, emphasizing form and color",
                "Mood: intense, emotional, raw",
            ),
        ),
        (
            "Cubist Still Life",
            ("cubist still life", "geometric planes", "fragmented forms", "muted palette"),
            ("hard edges", "abstracted shapes", "structured composition"),
            (
                "Style: cubist still life painting with geometric planes",
                flux_light_gallery,
                "Mood: analytical, structured, modernist",
            ),
        ),
        (
            "Surreal Oil Painting",
            ("surreal oil painting", "dreamlike realism", "unexpected juxtapositions", "soft haze"),
            ("smooth gradients", "quiet atmosphere", "symbolic imagery"),
            (
                "Style: surreal oil painting with dreamlike realism",
                "Lighting: soft controlled light with subtle shadows",
                "Mood: uncanny, calm, symbolic",
            ),
        ),
        (
            "Abstract Expressionism (Gestural)",
            ("abstract expressionism", "gestural brushstrokes", "paint splatter", "dynamic composition"),
            ("thick paint", "high energy", "raw texture"),
            (
                "Style: abstract expressionist painting with gestural brushstrokes",
                flux_light_gallery,
                "Texture: thick paint, visible strokes, energetic marks",
            ),
        ),
        (
            "Color Field Painting",
            ("color field painting", "large color blocks", "soft edges", "minimal forms"),
            ("smooth gradients", "subtle texture", "meditative mood"),
            (
                "Style: color field painting with large blocks of color",
                flux_light_gallery,
                "Mood: calm, meditative, minimal",
            ),
        ),
        (
            "Geometric Abstraction",
            ("geometric abstraction", "clean shapes", "balanced composition", "flat color planes"),
            ("crisp edges", "minimal texture", "modern palette"),
            (
                "Style: geometric abstract painting with clean shapes and balanced composition",
                flux_light_gallery,
                "Mood: modern, designed, calm",
            ),
        ),
        (
            "Suprematist Composition",
            ("suprematism", "geometric forms", "minimal palette", "floating shapes"),
            ("flat colors", "strong negative space", "bold composition"),
            (
                "Style: suprematist abstract composition with floating geometric forms",
                flux_light_gallery,
                "Mood: minimal, bold, abstract",
            ),
        ),
        (
            "De Stijl Composition",
            ("de stijl", "primary colors", "black lines", "grid composition"),
            ("flat color blocks", "clean geometry", "balanced layout"),
            (
                "Style: De Stijl composition with primary colors and black grid lines",
                "Lighting: flat graphic lighting with minimal shading",
                "Mood: clean, rational, designed",
            ),
        ),
        (
            "Op Art Illusion",
            ("op art", "optical illusion pattern", "high contrast geometry", "repeating lines"),
            ("sharp edges", "bold contrast", "graphic rhythm"),
            (
                "Style: op art optical illusion with high-contrast repeating geometry",
                "Lighting: flat even lighting, emphasis on contrast and pattern",
                "Mood: energetic, vibrating, graphic",
            ),
        ),
        (
            "Hard-Edge Painting",
            ("hard-edge painting", "flat color areas", "crisp boundaries", "minimal texture"),
            ("clean shapes", "bold palette", "precise edges"),
            (
                "Style: hard-edge painting with crisp boundaries and flat color areas",
                flux_light_gallery,
                "Mood: clean, modern, precise",
            ),
        ),
        (
            "Minimalist Painting",
            ("minimalist painting", "simple forms", "strong negative space", "restrained palette"),
            ("quiet composition", "subtle texture", "calm mood"),
            (
                "Style: minimalist painting with simple forms and strong negative space",
                flux_light_gallery,
                "Mood: calm, quiet, minimal",
            ),
        ),
        (
            "Neo-Expressionist Canvas",
            ("neo-expressionism", "bold brushwork", "raw texture", "intense color"),
            ("aggressive strokes", "high contrast", "emotive forms"),
            (
                "Style: neo-expressionist painting with bold brushwork and intense color",
                flux_light_gallery,
                "Mood: raw, energetic, contemporary",
            ),
        ),
        (
            "Art Brut / Outsider Art",
            ("outsider art", "raw naive style", "bold lines", "textured paint"),
            ("handmade imperfections", "vivid color", "childlike forms"),
            (
                "Style: outsider art with raw naive forms and bold lines",
                flux_light_gallery,
                "Mood: raw, honest, handmade",
            ),
        ),
        (
            "Naive Folk Painting",
            ("naive folk art painting", "flat perspective", "bright colors", "simple forms"),
            ("hand-painted texture", "decorative motifs", "cheerful mood"),
            (
                "Style: naive folk painting with simple forms and bright color",
                flux_light_soft_window,
                "Mood: charming, playful, handmade",
            ),
        ),
    ]

    for name, zpre, zsu, flux_sents in fine_art_specs:
        add_art_style(
            fine_art,
            id_prefix="fine",
            name=name,
            category="Fine Art",
            z_prefix=zpre,
            z_suffix=zsu,
            flux_suffix_sentences=flux_sents,
            tags=("fine_art",),
        )

    mixed_media_specs = [
        (
            "Paper Collage (Mixed Media)",
            ("paper collage", "torn paper edges", "layered textures", "cutout shapes"),
            ("glue marks", "paper grain", "handmade feel"),
            (
                "Style: mixed media paper collage with torn edges and layered shapes",
                flux_light_gallery,
                "Texture: paper grain, glue marks, layered cutouts",
            ),
        ),
        (
            "Photomontage Collage",
            ("photomontage", "cutout photo fragments", "layered collage", "high contrast"),
            ("paper texture", "rough edges", "analog zine aesthetic"),
            (
                "Style: photomontage collage made from cutout photo fragments",
                flux_light_gallery,
                "Mood: bold, surreal, graphic",
            ),
        ),
        (
            "Mixed Media Acrylic + Ink",
            ("mixed media", "acrylic paint", "ink linework", "layered marks"),
            ("texture paste", "splatter", "handmade imperfections"),
            (
                "Style: mixed media artwork combining acrylic paint and ink linework",
                flux_light_gallery,
                "Texture: layered paint, ink marks, tactile surface",
            ),
        ),
        (
            "Gel Plate Monoprint",
            ("gel plate monoprint", "ink layers", "brayer texture", "printmaking"),
            ("paper grain", "ink transfer artifacts", "handmade print"),
            (
                "Style: gel plate monoprint with layered ink textures",
                flux_light_gallery,
                "Texture: ink transfer artifacts, paper grain, layered prints",
            ),
        ),
        (
            "Cyanotype Print (Analog)",
            ("cyanotype print", "blue monochrome", "sun print", "paper texture"),
            ("grain", "chemical texture", "vintage print"),
            (
                "Style: analog cyanotype print on paper",
                flux_light_gallery,
                "Mood: minimal, photographic, deep blue",
            ),
        ),
        (
            "Assemblage Artwork",
            ("assemblage", "found objects", "mixed materials", "handcrafted"),
            ("tactile texture", "rough surfaces", "layered depth"),
            (
                "Style: assemblage artwork built from found objects and mixed materials",
                flux_light_gallery,
                "Texture: rough surfaces, layered depth, tactile materials",
            ),
        ),
        (
            "Textured Impasto Mixed Media",
            ("impasto texture", "palette knife marks", "thick paint", "mixed media"),
            ("surface relief", "paint ridges", "tactile depth"),
            (
                "Style: textured mixed media with thick impasto paint and palette knife marks",
                flux_light_gallery,
                "Texture: surface relief, paint ridges, tactile depth",
            ),
        ),
    ]

    for name, zpre, zsu, flux_sents in mixed_media_specs:
        add_art_style(
            mixed_media,
            id_prefix="mixed",
            name=name,
            category="Mixed Media",
            z_prefix=zpre,
            z_suffix=zsu,
            flux_suffix_sentences=flux_sents,
            tags=("mixed_media",),
        )

    street_art_specs = [
        (
            "Graffiti Wildstyle Lettering",
            ("graffiti", "wildstyle lettering", "spray paint", "urban wall"),
            ("paint drips", "overspray", "high contrast"),
            (
                "Style: graffiti wildstyle lettering on an urban wall",
                "Lighting: harsh streetlight with strong highlights and deep shadows",
                "Texture: spray paint overspray, drips, wall grit",
            ),
        ),
        (
            "Stencil Street Art",
            ("stencil street art", "spray paint", "sharp cutout shapes", "wall texture"),
            ("paint bleed", "rough edges", "high contrast"),
            (
                "Style: stencil street art sprayed on a textured wall",
                "Lighting: streetlight with strong contrast",
                "Texture: wall grit, paint bleed, sharp stencil edges",
            ),
        ),
        (
            "Spray Paint Mural",
            ("spray paint mural", "bold color", "large shapes", "urban wall"),
            ("overspray", "wall texture", "vibrant palette"),
            (
                "Style: large spray paint mural with bold color and clean shapes",
                "Lighting: daylight or streetlight depending on scene, crisp contrast",
                "Texture: subtle overspray and wall grain",
            ),
        ),
        (
            "Wheatpaste Poster Wall",
            ("wheatpaste poster wall", "layered posters", "torn paper", "street texture"),
            ("paper wrinkles", "glue stains", "gritty wall"),
            (
                "Style: wheatpaste posters layered on a city wall",
                "Lighting: overcast daylight for clear texture",
                "Texture: torn paper, wrinkles, glue stains, wall grit",
            ),
        ),
        (
            "Sticker Slap Wall",
            ("sticker slap wall", "sticker collage", "layered decals", "urban grit"),
            ("scratches", "torn stickers", "street texture"),
            (
                "Style: sticker slap wall covered in layered decals",
                "Lighting: overcast daylight with even illumination",
                "Texture: scratches, torn stickers, adhesive residue",
            ),
        ),
    ]

    for name, zpre, zsu, flux_sents in street_art_specs:
        add_art_style(
            street_art,
            id_prefix="street",
            name=name,
            category="Street Art",
            z_prefix=zpre,
            z_suffix=zsu,
            flux_suffix_sentences=flux_sents,
            tags=("street_art",),
        )

    # --- Graphic / print design ---
    print_styles = [
        ("Risograph Print", ("risograph print", "misregistration", "paper texture", "limited inks")),
        ("Screen Print Poster", ("screen print", "bold shapes", "ink texture", "poster design")),
        ("Halftone Comic", ("halftone dots", "comic print texture", "high contrast")),
        ("Duotone Poster", ("duotone", "bold contrast", "graphic poster")),
        ("Swiss Design", ("international typographic style", "grid layout", "minimal poster")),
        ("Bauhaus", ("bauhaus design", "geometric shapes", "primary colors")),
        ("Constructivist Poster", ("constructivist poster", "bold diagonals", "limited palette")),
        ("Art Deco", ("art deco poster", "ornamental geometry", "luxury vibe")),
        ("Pop Art", ("pop art", "bold outlines", "saturated colors")),
        ("Psychedelic Poster", ("psychedelic poster", "wavy typography", "vibrant gradients")),
        ("Vintage Travel Poster", ("vintage travel poster", "flat illustration", "retro palette")),
        ("Brutalist Graphic", ("brutalist graphic design", "raw typography", "high contrast layout")),
        ("Memphis Pattern", ("memphis design", "playful shapes", "bold colors", "pattern")),
        ("Y2K Graphic", ("y2k design", "chrome gradients", "tech vibes", "glossy")),
        ("Vaporwave Poster", ("vaporwave aesthetic", "neon gradients", "retro futurism")),
        ("Grunge Flyer", ("grunge design", "rough texture", "photocopy noise")),
        ("Newspaper Collage", ("newspaper collage", "cutout typography", "paper texture")),
        ("Minimal Poster", ("minimal poster", "simple shapes", "strong negative space")),
        ("Geometric Pattern", ("geometric pattern", "repeating shapes", "clean layout")),
        ("Retro Pixel UI", ("retro pixel ui", "8-bit interface", "limited palette")),
        ("Sticker Bomb", ("sticker bomb", "busy collage", "bold outlines")),
        ("Isometric Infographic", ("isometric infographic", "icons", "clean labels")),
        ("Editorial Layout", ("editorial layout", "clean typography", "grid composition")),
        ("Monochrome Typography", ("monochrome typography", "bold type", "high contrast")),
        ("Holographic Chrome", ("holographic chrome", "iridescent gradient", "glossy")),
        ("Liquid Gradient", ("liquid gradient", "smooth color blends", "modern poster")),
        ("Sticker Sheet", ("sticker sheet", "die-cut outlines", "playful icons")),
        ("Packaging Label", ("packaging label design", "clean hierarchy", "print-ready")),
        ("Blueprint Poster", ("blueprint poster", "technical lines", "clean labels")),
    ]
    for name, ztags in print_styles:
        graphic.append(
            StyleSpec(
                id=_make_id("gfx", name),
                name=name,
                category="Graphic Design",
                tags=("graphic", "print"),
                z_prefix=ztags,
                z_suffix=("clean edges", "intentional composition"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, graphic print aesthetic",
                    "Lighting: flat even light, minimal shading",
                    "Mood: bold, designed, poster-like",
                ),
            )
        )

    # --- 3D / CG ---
    cg_modes = [
        ("Photoreal 3D Render", ("photorealistic 3d render", "physically based materials", "global illumination")),
        ("Stylized 3D Toon", ("stylized 3d", "toon shading", "soft gradients")),
        ("Clay Render", ("clay render", "matte material", "soft studio lighting")),
        ("Wireframe Overlay", ("wireframe overlay", "technical render", "clean topology")),
        ("Low Poly", ("low poly 3d", "faceted geometry", "flat shading")),
        ("Isometric 3D Room", ("isometric 3d room", "miniature diorama", "clean lighting")),
        ("Subsurface Skin Render", ("3d render", "subsurface scattering", "realistic skin shader")),
        ("Hard Surface Sci-Fi", ("hard surface 3d", "sci-fi details", "panel lines", "clean bevels")),
        ("Miniature Diorama", ("miniature diorama", "tiny details", "tilt-shift feel")),
        ("Stop Motion Look", ("stop motion aesthetic", "handmade texture", "slight imperfections")),
        ("Plastic Toy Render", ("toy photography look", "plastic materials", "clean highlights")),
        ("Glass and Caustics", ("glass render", "caustics", "refractive highlights")),
        ("Subtle Stylized PBR", ("stylized pbr", "clean shapes", "soft materials")),
        ("CAD Product Render", ("cad render", "clean surfaces", "studio reflections")),
        ("Neon Cyber Render", ("3d render", "neon emissive", "wet reflections", "fog")),
        ("Stylized Miniature Set", ("miniature set", "tiny props", "diorama lighting")),
        ("Paper Craft 3D", ("paper craft", "folded paper", "layered cutouts")),
        ("Wax Subsurface Render", ("subsurface scattering", "wax material", "soft translucency")),
    ]
    for name, ztags in cg_modes:
        cg3d.append(
            StyleSpec(
                id=_make_id("cg", name),
                name=name,
                category="3D/CG",
                tags=("3d", "cg"),
                z_prefix=ztags,
                z_suffix=("high detail", "clean render", "sharp edges"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, clean 3D render",
                    flux_light_studio_softbox,
                    "Materials: physically based, realistic roughness and specular response",
                ),
            )
        )

    # --- Architecture / interior ---
    arch_styles = [
        ("Minimalist Interior", ("minimalist interior", "clean lines", "neutral palette", "natural light"), flux_light_soft_window),
        ("Scandinavian Interior", ("scandinavian interior", "light wood", "cozy minimalism"), flux_light_soft_window),
        ("Brutalist Architecture", ("brutalist architecture", "raw concrete", "monolithic forms"), flux_light_overcast),
        ("Art Deco Lobby", ("art deco interior", "geometric ornament", "luxury materials"), "Lighting: warm art deco sconces and soft ambient glow"),
        ("Modern Glass Tower", ("modern architecture", "glass facade", "clean geometry"), flux_light_overcast),
        ("Cozy Cabin Interior", ("rustic cabin interior", "wood textures", "warm practical lights"), "Lighting: warm fireplace glow mixed with soft lamp light"),
        ("Industrial Loft", ("industrial loft", "exposed brick", "steel beams", "large windows"), flux_light_soft_window),
        ("Mid-Century Modern", ("mid-century modern interior", "clean lines", "warm wood", "retro furniture"), flux_light_soft_window),
        ("Japanese Wabi-Sabi", ("wabi-sabi interior", "natural materials", "imperfection", "calm minimalism"), flux_light_soft_window),
        ("Mediterranean Villa", ("mediterranean architecture", "stucco walls", "arched openings", "sunlit"), "Lighting: warm sun, sharp but pleasing shadows, bright highlights"),
        ("Gothic Cathedral", ("gothic architecture", "tall arches", "stained glass", "dramatic scale"), "Lighting: colored light beams through stained glass, dust in the air"),
        ("Futurist Interior", ("futurist interior", "sleek curves", "clean materials", "ambient light"), "Lighting: soft ambient strips with crisp accent highlights"),
        ("Moroccan Riad", ("moroccan architecture", "tile patterns", "courtyard light", "arched doorways"), "Lighting: warm sun filtering into courtyard, soft bounce light"),
        ("Tropical Modern", ("tropical modern architecture", "open air", "natural materials", "lush greenery"), "Lighting: bright sun with soft shade from overhangs, humid ambience"),
        ("Victorian Parlor", ("victorian interior", "ornate details", "rich textures"), "Lighting: warm practical lamps with soft ambient fill"),
        ("Concrete Minimalism", ("concrete interior", "minimalism", "soft light", "clean geometry"), flux_light_soft_window),
    ]
    for name, ztags, flux_light in arch_styles:
        arch.append(
            StyleSpec(
                id=_make_id("arch", name),
                name=name,
                category="Architecture/Interior",
                tags=("architecture", "interior"),
                z_prefix=ztags,
                z_suffix=("realistic materials", "clean perspective"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, realistic architectural photograph",
                    flux_light,
                    "Composition: clean verticals, strong geometry, intentional lines",
                ),
            )
        )

    # --- Fashion / editorial ---
    fashion_styles = [
        ("Glossy Fashion Editorial", ("fashion editorial", "studio lighting", "high contrast", "clean backdrop"), flux_light_studio_softbox),
        ("Streetwear Lookbook", ("streetwear lookbook", "candid pose", "urban backdrop"), flux_light_overcast),
        ("Runway Backstage", ("backstage fashion", "documentary feel", "available light"), flux_light_soft_window),
        ("High Fashion Beauty Shot", ("beauty shot", "clean skin", "beauty lighting", "sharp eyes"), "Lighting: beauty dish with soft fill, clean catchlights, smooth gradients"),
        ("Minimal Editorial", ("minimal fashion editorial", "neutral palette", "clean composition"), flux_light_studio_softbox),
        ("Vintage Editorial", ("vintage fashion editorial", "film grain", "muted palette"), flux_light_soft_window),
        ("Outdoor Editorial", ("fashion editorial outdoors", "wind", "natural light"), flux_light_golden_back),
        ("Street Style Snapshot", ("street style", "candid", "natural color"), flux_light_overcast),
        ("Luxury Beauty Macro", ("beauty macro", "skin texture", "cosmetic detail"), "Lighting: soft macro beauty light, clean specular highlights"),
        ("Athleisure Campaign", ("athleisure campaign", "clean energy", "natural light"), flux_light_overcast),
        ("Couture Runway", ("couture runway", "runway lights", "dramatic pose"), "Lighting: runway spotlights with controlled haze and crisp highlights"),
        ("Vintage Street Fashion", ("vintage street fashion", "film grain", "candid"), flux_light_soft_window),
    ]
    for name, ztags, flux_light in fashion_styles:
        fashion.append(
            StyleSpec(
                id=_make_id("fash", name),
                name=name,
                category="Fashion",
                tags=("fashion", "editorial"),
                z_prefix=ztags,
                z_suffix=("sharp focus", "editorial color grade"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, fashion photograph",
                    flux_light,
                    "Mood: confident, curated, magazine-ready",
                ),
            )
        )

    # --- Product ---
    product_styles = [
        ("Luxury Watch Ad", ("luxury product shot", "watch photography", "controlled reflections"), flux_light_studio_softbox),
        ("Cosmetics Packshot", ("cosmetics product shot", "clean studio setup", "soft reflections"), flux_light_studio_softbox),
        ("Food Packshot", ("food packshot", "studio tabletop", "appetizing highlights"), flux_light_soft_window),
        ("Perfume Ad", ("perfume product shot", "glass bottle", "luxury lighting"), flux_light_studio_softbox),
        ("Tech Gadget Shot", ("tech product photography", "clean highlights", "premium materials"), flux_light_studio_softbox),
        ("Jewelry Macro", ("jewelry macro photography", "sparkle highlights", "shallow depth of field"), "Lighting: small hard highlights for sparkle, controlled fill, clean reflections"),
        ("Skincare Bottle Ad", ("skincare product shot", "clean studio", "dewy highlights"), flux_light_studio_softbox),
        ("Sneaker Product Shot", ("sneaker photography", "clean background", "sharp detail"), flux_light_studio_softbox),
        ("Beverage Splash", ("beverage ad", "splash photography", "frozen droplets"), "Lighting: hard backlight with crisp droplets, high-speed flash feel"),
    ]
    for name, ztags, flux_light in product_styles:
        product.append(
            StyleSpec(
                id=_make_id("prod", name),
                name=name,
                category="Product",
                tags=("product",),
                z_prefix=ztags,
                z_suffix=("crisp edges", "high detail", "clean background"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, commercial product photograph",
                    flux_light,
                    "Composition: clean silhouette, premium materials, crisp details",
                ),
            )
        )

    # --- Nature ---
    nature_styles = [
        ("Misty Forest", ("nature photography", "misty forest", "atmospheric depth"), "Lighting: diffused fog light, soft beams through trees"),
        ("Mountain Vista", ("landscape photography", "mountain vista", "wide angle"), flux_light_golden_back),
        ("Seascape", ("seascape photography", "waves", "horizon line"), "Lighting: soft overcast coastal light, subtle specular highlights"),
        ("Desert Dunes", ("desert landscape", "sand dunes", "ripples", "wide angle"), "Lighting: low sun casting long shadows across dune ridges"),
        ("Autumn Leaves", ("nature close-up", "autumn leaves", "rich colors", "bokeh"), flux_light_soft_window),
        ("Rainforest", ("rainforest", "lush greens", "humid haze", "detailed foliage"), "Lighting: filtered sunlight through canopy, humid atmosphere"),
        ("Aurora Night", ("aurora", "night sky", "wide angle", "stars"), "Lighting: moonless night with aurora glow, crisp stars"),
        ("Stormy Coast", ("stormy seascape", "dramatic clouds", "waves"), "Lighting: storm light with high contrast clouds, moody atmosphere"),
        ("Wildflower Meadow", ("wildflower meadow", "soft bokeh", "pastel colors"), flux_light_golden_back),
        ("Snowy Pines", ("snowy forest", "cold palette", "fine detail"), "Lighting: bright overcast snow light, soft shadow transitions"),
        ("Waterfall Mist", ("waterfall", "mist", "long exposure feel", "lush rocks"), "Lighting: overcast forest light with mist diffusion"),
        ("Volcanic Landscape", ("volcanic landscape", "black rocks", "dramatic sky"), "Lighting: dramatic overcast with breaks of sunlight"),
        ("Coral Reef", ("coral reef", "underwater", "colorful fish", "clear water"), "Lighting: underwater caustics with clear blue light"),
        ("Savanna Sunset", ("savanna", "sunset", "dust haze", "warm tones"), flux_light_golden_back),
    ]
    for name, ztags, flux_light in nature_styles:
        nature.append(
            StyleSpec(
                id=_make_id("nature", name),
                name=name,
                category="Nature",
                tags=("nature", "landscape"),
                z_prefix=ztags,
                z_suffix=("natural color", "fine detail", "realistic texture"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, nature photograph",
                    flux_light,
                    "Mood: calm, immersive, natural",
                ),
            )
        )

    # --- Experimental / abstract ---
    exp_styles = [
        ("Glitch Art", ("glitch art", "digital distortion", "chromatic aberration", "scanlines")),
        ("Double Exposure", ("double exposure", "layered silhouettes", "surreal composition")),
        ("Light Painting", ("light painting", "long exposure trails", "dark background")),
        ("Prismatic Refraction", ("prismatic refraction", "rainbow dispersion", "glass texture")),
        ("Abstract Geometry", ("abstract geometric", "clean shapes", "bold composition")),
        ("Minimal Monochrome", ("minimal monochrome", "high contrast", "negative space")),
        ("Analog Photocopy", ("photocopy aesthetic", "paper noise", "high contrast", "xerox texture")),
        ("Datamosh", ("datamosh", "compression artifacts", "blocky smears")),
        ("Liquid Marble", ("liquid marble", "swirling ink", "organic patterns")),
        ("Neon Wireframe", ("neon wireframe", "glowing lines", "dark background")),
        ("Kaleidoscope", ("kaleidoscope", "symmetry", "prismatic pattern")),
        ("Minimal Gradient", ("minimal gradient", "soft color field", "smooth transitions")),
        ("Paper Grain Texture", ("paper grain", "subtle texture", "soft noise")),
        ("Chromatic Prism", ("chromatic prism", "color separation", "light leaks")),
        ("Mirror Kaleidoscope", ("mirror kaleidoscope", "fragmented reflections", "symmetry")),
        ("Thermal Vision", ("thermal vision", "false color", "heat map look")),
    ]
    for name, ztags in exp_styles:
        experimental.append(
            StyleSpec(
                id=_make_id("exp", name),
                name=name,
                category="Experimental",
                tags=("experimental", "abstract"),
                z_prefix=ztags,
                z_suffix=("clean composition", "intentional design"),
                flux_suffix_sentences=(
                    f"Style: {name.lower()}, experimental visual aesthetic",
                    "Lighting: intentional and graphic, emphasizing form and contrast",
                    "Mood: bold, modern, designed",
                ),
            )
        )

    # Finalize packs.
    write_pack("10_cinema.json", _uniq(cinema))
    write_pack("20_photography.json", _uniq(photo))
    write_pack("30_illustration.json", _uniq(illustration))
    write_pack("35_fine_art.json", _uniq(fine_art))
    write_pack("36_mixed_media.json", _uniq(mixed_media))
    write_pack("37_street_art.json", _uniq(street_art))
    write_pack("40_graphic_design.json", _uniq(graphic))
    write_pack("50_3d_cg.json", _uniq(cg3d))
    write_pack("60_architecture_interior.json", _uniq(arch))
    write_pack("70_fashion.json", _uniq(fashion))
    write_pack("80_product.json", _uniq(product))
    write_pack("90_nature.json", _uniq(nature))
    write_pack("95_experimental.json", _uniq(experimental))
    write_pack("96_color_grades.json", _uniq(grades))

    total = sum(
        len(x)
        for x in (
            cinema,
            photo,
            illustration,
            fine_art,
            mixed_media,
            street_art,
            graphic,
            cg3d,
            arch,
            fashion,
            product,
            nature,
            experimental,
            grades,
        )
    )
    print(f"Wrote style packs: {total} styles -> {PACKS_DIR}")


if __name__ == "__main__":
    build()
