import base64
import concurrent.futures
import hashlib
import json
import logging
import os
import threading
import time
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.storage import get_photo_bytes, save_photo
from app.db.database import SessionLocal as _SessionLocal
from app.db.database import get_db
from app.models.models import (
    AppUser,
    GarmentPhoto,
    InspectionAIResult,
    IssueEditHistory,
    InspectionIssue,
    InspectionRecord,
    InspectionStatus,
    LaundryOrderItem,
)

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_ISSUE_TYPES = {
    "stain", "tear", "hole", "wear", "wrinkle",
    "fade", "missing_button", "zipper", "pilling", "other",
}


def _sample_issue_archetypes() -> str:
    """Confirmed issue archetypes distilled from user-provided reference images."""
    return """=== CONFIRMED POSITIVE ISSUE ARCHETYPES (from verified reference photos) ===

── SOFT LEATHER JACKETS (gray, silver, white, cream, light-colored nappa/lambskin) ──
- WIDESPREAD MOTTLED DARK STAINING: Large irregular dark patches covering 30-80% of visible
  panel surface — looks like uneven water damage or oil transfer creating a blotchy "wet"
  appearance. The original pale leather color is still visible in un-affected areas, making
  the contrast clear. Report each distinctly darker zone as a SEPARATE stain issue.
- FULL FRONT PANEL staining: The entire visible front may show uneven darkening following
  the leather's natural creases/wrinkles. Do NOT dismiss this as shadow — shadow follows
  folds uniformly, staining creates irregular color boundaries.
- Concentrated dark spot near zipper placket or stitching lines: small focused dark dot
  2-4cm across on light leather near zipper guard.
- Scuff marks: localized lighter or darker patch on the leather surface showing abrasion,
  different texture from surrounding area.

── SUEDE / NUBUCK (beige, tan, camel, brown tones) ──
- Inner collar seam contact stain: concentrated ORANGE-BROWN or rust-colored stain 2-4cm
  diameter exactly where the collar meets the lining fold — this is a skin/sweat contact
  area. Against beige suede, the stain is clearly more saturated orange or brown.
- Diffuse large-area darkening on suede body: irregular patch where suede appears visibly
  darker/more saturated than surrounding areas — NOT nap direction change (nap is uniform
  texture variation, stain has an irregular spatial boundary).
- Collar line accumulation: darker band running along the inner collar edge 0.5-1cm wide
  from repeated neck contact.

── DOWN JACKETS (yellow/orange/gold nylon) ──
- Multiple diagonal gray or dark scratch-like rub marks distributed across several puff
  panels (front, side, and near pocket areas) — surface abrasion transfers visually
  distinct from the bright yellow ground color. Each marked panel = separate issue.
- Near zipper pocket edges: discoloration patch where pocket flap meets main panel.
- Pocket zipper pull area: grime buildup or stitch-area darkening.
- Faint parallel scratch lines running across individual puff bulges, 2-8cm long.
- Small punctures or feather leaks near quilting seam intersections.
- If 3+ puff panels in the same photo show irregularly colored spots — report each separately.

── DOWN JACKETS (dark navy / black / charcoal puffer) ──
- FEATHER LEAK (issue_type=hole): At a quilting seam intersection, a small bright-white or
  pale triangular feather tip is visibly protruding through the fabric — looks like a tiny
  spike or thread of white fluff poking out from a dark seam. Confidence ≥ 0.25.
- Multiple seam intersections should each be checked independently.
- Surface stains: irregular grayish or faint discolored patch on a puff panel — often low
  contrast against dark fabric. Report as stain.
- Zipper and pocket edges: accumulated grime appearing as a slightly lighter or glossy line.
- Cuff and hem stitching: abrasion wear appearing as fraying threads or shine marks.
- Underarm panel: diffuse lighter patch from repeated friction (wear type).

── LIGHT/WHITE HARD SHELL JACKETS (gray, pearl, cream) ──
- Low-contrast diffuse gray or beige stain near the front chest panel beside zipper line —
  softened dirty smudge 4-8cm diameter, easy to miss. Look carefully at the overall
  brightness uniformity of the panel.
- Subtle grime at sleeve cuffs or inner collar with a slightly yellowed or grayish ring.
- Any area appearing locally more matte or dimmer than adjacent fabric.

── BLUE TECHNICAL SHELL JACKETS (Arc'teryx or similar) ──
- Clearly visible dark smear/stain alongside or just below the chest pocket flap — strong
  color contrast against blue fabric. Often looks like a darker blue or greenish smear.
- Abrasion haze or scuff zone on outer forearm/sleeve — matte dull patch vs shiny surface.
- Cuff grime ring: darker band encircling the sleeve cuff where the cuff bends.

── VARSITY / WOOL JACKETS (white/cream wool body with dark contrast panels) ──
- Dust, lint, or fine particle accumulation on DARK collar/sleeve panels — appears as
  scattered white/gray specks or overall lightening of the dark fabric area.
- White/cream wool body: subtle gray or yellow discoloration vs the freshly white areas,
  look especially at front panel center and pocket openings.
- Metal hardware (snaps, zipper pullers): green/dark oxidation tarnish around the base.

── SHIRTS / DRESS SHIRTS / POLO SHIRTS ──
- Inner collar ring stain: gray or yellowish-brown band running along the INSIDE of the
  collar, 0.5-1.5cm wide, from repeated skin/sweat contact — entire collar circumference
  may be affected. Compare to the clean outer collar color.
- Cuff dual-side grime: dark band at the shirt cuff edge (inside face) from wrist contact.
- Underarm: yellow-brown perspiration stain, area 5-15cm, bilateral.
- Front placket button area: food drop or small round stain near buttons.

── SWEATERS / KNITWEAR / CASHMERE ──
- Surface pilling clusters: raised fuzzy ball clusters distributed across body/elbows —
  pilling IS reportable for premium knitwear before cleaning.
- Snag/pull: single strand pulled out of knit creating a visible loop or ridge line.
- Small hole: circular gap 3-10mm in the knit, possibly moth damage.
- Underarm discoloration: yellow-brown perspiration in the armpit zone of lighter-colored knits.

── TRENCH COAT / OVERCOAT ──
- Inner collar lining stain: concentrated grayish-brown ring on the inner collar lining
  from skin/makeup contact. Very common on beige/tan trench coats.
- Shoulder pad moisture mark: irregular darker patch on the shoulder area where water
  sat on the fabric.
- Cuff outer and inner face: grime accumulation from hand contact.
- Hem edge: ground contact soiling (especially on longer overcoats).

── JEANS / DENIM ──
- Ink or pen stain: sharp-edged dark stain with visible color transfer on thigh/pocket area.
- Dye bleed/crocking: areas where dark dye transferred onto the lighter sections of the denim.
- Knee area: lighter patch from abrasion/wear (if not intentional distressing — compare with other areas).
- Belt loop area: concentrated grime or discoloration ring.

── WHITE ATHLETIC SHOES (Nike, Adidas or similar) ──
- Toe-box forward area: obvious gray or brown dirtiness, extends 3-5cm from front edge.
  Report BOTH shoes as separate issues if both are affected.
- Heel collar (inside top rim): dark grime in the fabric fold at the ankle opening —
  both left and right sides separately.
- Sidewall / midsole edge: continuous dirt line along the upper-sole junction.
- Tongue surface and around laces: yellowing or gray transfer.
- LEATHER UPPER OVERALL YELLOWING: the entire leather upper surface (especially on
  classic/retro styles like Nike Cortez) may appear uniformly yellow or cream instead
  of white — report as a "fade/yellowing" issue covering the full upper area.
- Grime buildup inside the logo swoosh edge: concentrated dark accumulation where the
  branded logo stitching meets the outer leather panel.
- Midsole edge YELLOWING: white rubber midsole that has turned cream or yellow overall.

── PINK / PASTEL STRUCTURED JACKETS (tweed, boucle, piqué, Chanel-style) ──
- BRIGHT CONTRASTING STAIN on lower front panel or hem area: a clearly visible
  yellow-green, lime, orange, or other bright-colored stain against the light pink or
  pastel fabric. The stain has irregular shape (oval/splash pattern) 3-10cm across.
  High confidence — these stand out strongly from the uniform light background.
- Center button placket area: subtle discoloration between buttons or around satin-covered
  button edges — may look slightly darker or yellowed.
- Collar/lapel underside: sweat/skin contact marks forming a faint ring or dark band.
- Fabric texture note: the woven boucle/piqué grain is intentional — flag only COLOR
  anomalies that do not align with the weave structure.

── WHITE SATIN / SILK FORMAL WEAR (wedding dress, evening gown, bridal wear) ──
- LARGE GRAY-BROWN SOILING PATCH: on white satin, soiling appears as a grayish or brownish
  zone covering a significant area (10-40cm). The satin's reflectivity makes it easy to
  compare — soiled areas lose the natural sheen and appear dull/matte or grayish.
- Hemline soiling: ground-contact brown or gray at the very bottom edge of long gowns.
- Yellowish cast compared to clean satin sections: yellowing from storage over time.
- Any area where the white satin appears flat/dull instead of reflective → potential stain.
- Underarm of bodice: yellow/gray perspiration mark.

── DARK BLAZER / SUIT JACKET / DARK STRUCTURED FABRIC (navy, black, charcoal) ──
- SCATTERED WHITE LINT OR DUST FLECKS: small bright white particles (2-8mm each) scattered
  irregularly across the dark fabric surface — 4+ visible particles = a reportable issue.
  Report as: "scattered white lint particles across [region] panel".
- White thread or fiber fragments embedded in dark woven fabric texture.
- Any localized lighter patch on the dark surface from abrasion (shiny woven fabric can
  develop dull zones or vice versa from rubbing).
- Lapel and collar inside edge: darker transfer from neck/skin contact.

── GENERAL PATTERNS (apply to all garments) ──
- Any color difference between adjacent same-fabric areas that does NOT align with seams,
  intentional dye patterns, or uniform lighting gradient → potential stain.
- 2+ localized discolored spots in one photo not aligned with structure → report each
  with individual bboxes.
- On LEATHER/SUEDE: If the surface looks "wet" or "blotchy" and patchy — it's staining.

=== NEGATIVE CONTROLS (do NOT report) ===
- Quilted puff panel shadows, stitching lines, seam ridges, fold creases.
- Zipper teeth shadows, hanger shadows, finger/hand shadows in the frame.
- Natural fabric texture, intended multi-color patterns (plaid, tartan, etc.).
- Reflective glare patches on shiny surfaces.
- UNIFORM smooth-gradient shading across a large area with no localized residue.
- Natural suede nap direction changes or leather grain natural variation.
- Intentional color blocking between different fabric panels."""


def _build_garment_type_hint(garment_type: str) -> str:
    """Returns garment-type-specific detection guidance based on the input garment type.

    This function leverages the garment_type string provided by staff before running AI
    detection, specializing the primary prompt to maximize recall for that specific garment.
    """
    g = garment_type.lower()

    if any(k in g for k in ("trench coat", "overcoat", "trench", "大衣", "風衣")):
        return """\nGARMENT-TYPE GUIDANCE — Trench Coat/Overcoat:
- PRIORITY: Inner collar lining — concentrated gray-brown ring from skin contact.
- Shoulder area: darker moisture mark patch.
- Cuffs inner and outer face: grime band.
- Hem edge: ground-contact soiling.\n"""

    if any(k in g for k in ("shirt", "dress shirt", "polo shirt", "blouse", "恤", "衬衫")):
        return """\nGARMENT-TYPE GUIDANCE — Shirt/Blouse:
- PRIORITY: INSIDE collar — gray or yellowish ring 0.5-1.5cm wide all along the collar.
- Cuffs inner face: dark grime band at the edge.
- Underarm: bilateral yellow-brown perspiration stain.
- Front placket near buttons: small food drops or spots.\n"""

    if any(k in g for k in ("sweater", "cashmere", "knitwear", "cardigan", "wool knit", "毛衣", "針織")):
        return """\nGARMENT-TYPE GUIDANCE — Sweater/Knitwear/Cashmere:
- Surface pilling: raised fuzzy ball clusters across body — reportable on premium knitwear.
- Snag/pull: single strand pulled forming a visible loop (report as 'tear').
- Small hole: 3-10mm gap in knit, possible moth damage.
- Underarm discoloration on lighter colors.\n"""

    if any(k in g for k in ("jeans", "denim", "牛仔")):
        return """\nGARMENT-TYPE GUIDANCE — Jeans/Denim:
- Pen or ink stain: sharp-edged dark marks on thigh or hip pocket area.
- Knee area: unintentional lighter patch from abrasion.
- Belt loop: concentrated grime or dark ring.
- Pocket corner: wear marks.\n"""

    if any(k in g for k in ("wedding", "bride", "bridal", "gown", "evening gown", "ball gown", "婚纱", "礼服", "晚礼服")):
        return """\nGARMENT-TYPE GUIDANCE — White Formal/Bridal Wear (Satin/Silk):
- Scan for GRAY or BROWN soiling patches that appear dull/matte against reflective white satin.
- Compare reflectivity: clean satin = shiny; stained areas = flat/dull.
- Check hemline and lower skirt for ground-contact soil.
- Look for yellowish cast on any section vs the cleaner white areas.
- Underarm of bodice: perspiration marks.\n"""

    if any(k in g for k in ("tweed", "boucle", "bouclé", "pique", "piqué", "chanel", "structured jacket", "粗花呢")):
        return """\nGARMENT-TYPE GUIDANCE — Structured/Tweed/Boucle Jacket:
- PRIORITY: Lower front panel near hemline — look for BRIGHT CONTRASTING STAIN (yellow-green,
  lime, orange) that stands out against the light-colored textured fabric. High confidence.
- Button placket center: discoloration between or around covered buttons.
- Collar lapel inner face: skin contact marks or faint ring.
- The woven texture is intentional — flag COLOR anomalies only.\n"""

    if any(k in g for k in ("blazer", "suit jacket", "sport coat", "dark jacket", "navy jacket", "西装", "西裝", "夾克")):
        return """\nGARMENT-TYPE GUIDANCE — Blazer/Suit/Dark Structured Jacket:
- PRIORITY: Look for scattered WHITE LINT FLECKS or dust particles on the dark fabric — small
  bright specks (2-8mm). 4+ visible = reportable. Report as 'scattered lint on [panel]'.
- Any lighter patch from abrasion on woven dark fabric.
- Lapel and collar inside: transfer/contact marks.
- Elbow area: shiny abrasion zones on woven fabric.\n"""

    if any(k in g for k in ("silk", "satin", "chiffon", "organza", "georgette", "crepe", "丝绸", "絲綢", "緞")):
        return """\nGARMENT-TYPE GUIDANCE — Silk/Satin Fabric:
- Stained satin loses its sheen: compare reflectivity between panels — matte zone = stain.
- Watermarks: ring-shaped stain outline from evaporated liquid droplets.
- Color shifts: any area with different hue than surrounding same-fabric area.\n"""

    if any(k in g for k in ("down", "puffer", "puff", "duvet", "羽绒", "羽絨")):
        return """\nGARMENT-TYPE GUIDANCE — Down Jacket:
- PRIORITY 1 — FEATHER LEAK (issue_type=hole): At any quilting seam intersection, look for
  a small bright-white or pale triangular feather tip visibly poking through the outer fabric.
  On DARK jackets this appears as a tiny bright spike against black/navy fabric near a seam.
  Even one feather tip visible = report as hole, confidence 0.3+.
- PRIORITY 2: Inspect EVERY visible puff panel individually for stains or gray scratch marks.
  Each affected panel = separate issue.
- Pocket edge seams: grime or discoloration.
- Zipper area: grime buildup, stitch darkening.\n"""

    if any(k in g for k in ("shoe", "sneaker", "boot", "trainer", "运动鞋", "球鞋", "鞋")):
        return """\nGARMENT-TYPE GUIDANCE — Footwear:
- Treat LEFT and RIGHT shoe as independent items — report each shoe's issues separately.
- Toe box leather: yellowing or gray-brown dirtiness.
- Brand logo edge (Swoosh, stripe): dark grime along logo stitching.
- Midsole edge: yellowing or continuous dirt line.
- Lace area and tongue: yellowing or staining.\n"""

    if any(k in g for k in ("leather jacket", "nappa", "lambskin", "皮衣", "皮革夹克", "皮革外套")):
        return """\nGARMENT-TYPE GUIDANCE — Leather Jacket (Nappa/Lambskin):
- Widespread mottled dark patches on the SAME leather panel = staining, NOT shadow.
  Shadow follows folds; staining crosses fold lines freely.
- Compare a darker zone against an adjacent lighter zone of identical leather — the boundary
  where they meet is a stain edge.
- Near zipper placket: concentrated dark marks.\n"""

    if any(k in g for k in ("suede", "nubuck", "麂皮", "绒面革")):
        return """\nGARMENT-TYPE GUIDANCE — Suede/Nubuck:
- PRIORITY: Inner collar seam fold — concentrated ORANGE-BROWN stain where collar meets lining.
- Body: areas darker/more saturated than adjacent same-material area = staining (not nap).
- Nap direction changes are uniform; stain has irregular spatial boundary.\n"""

    if any(k in g for k in ("varsity", "baseball jacket", "college jacket", "wool body", "大学夹克")):
        return """\nGARMENT-TYPE GUIDANCE — Varsity/Wool Jacket:
- Dark collar and sleeve panels: scattered white/gray dust particles or lint lightening the dark fabric.
- White/cream wool body: gray or yellowish tinge in any region.
- Metal snaps/hardware: oxidation tarnish.\n"""

    if any(k in g for k in ("shell", "windbreaker", "softshell", "soft shell", "冲锋衣", "衝鋒衣")):
        return """\nGARMENT-TYPE GUIDANCE — Shell/Technical Jacket:
- Low-contrast diffuse gray stain on light-colored front panel — check brightness uniformity.
- Any localized area that looks MORE MATTE or DIMMER than adjacent fabric panel.
- Sleeve cuffs and collar: grime ring.\n"""

    return ""


def _load_image_bytes(file_path: str) -> bytes | None:
    """Load raw image bytes from URL or storage."""
    if file_path.startswith("http://") or file_path.startswith("https://"):
        try:
            import urllib.request
            with urllib.request.urlopen(file_path, timeout=15) as resp:
                return resp.read()
        except Exception as e:
            logger.warning("Failed to download image from URL %s: %s", file_path, e)
            return None
    return get_photo_bytes(file_path)


def _prepare_image_content_from_bytes(image_bytes: bytes, source_name: str) -> dict | None:
    """Prepare raw image bytes for the OpenAI Vision API."""
    if not image_bytes:
        return None
    img_data = base64.b64encode(image_bytes).decode()
    ext = os.path.splitext(source_name.split("?")[0])[-1].lower().lstrip(".")
    mime = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp", "bmp": "image/bmp",
    }.get(ext, "image/jpeg")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{img_data}", "detail": "high"},
    }


def _prepare_image_content(file_path: str) -> dict | None:
    """Prepare an image for the OpenAI Vision API."""
    image_bytes = _load_image_bytes(file_path)
    if not image_bytes:
        return None
    return _prepare_image_content_from_bytes(image_bytes, file_path)


def _generate_focus_crops(file_path: str, garment_type: str = "") -> list[dict]:
    """Generate overlapping local crops so subtle stains/scuffs become easier to detect.

    For down jackets and sneakers a denser 3x3 grid is used to catch issues spread
    across multiple puff panels or across both shoes.  For other garments a standard
    9-crop layout is used.  The number of crops is capped by
    settings.OPENAI_DETECT_MAX_FOCUS_CROPS (default 9).
    """
    image_bytes = _load_image_bytes(file_path)
    if not image_bytes:
        return []

    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        logger.warning("Failed to open image for crop generation %s: %s", file_path, exc)
        return []

    width, height = image.size
    if width < 480 or height < 480:
        return []

    gtype_lower = garment_type.lower()
    is_down_jacket = any(k in gtype_lower for k in ("down", "puffer", "puff", "duvet", "羽絨", "jacket"))
    is_shoes = any(k in gtype_lower for k in ("shoe", "sneaker", "boot", "鞋"))
    is_leather = any(k in gtype_lower for k in ("leather", "suede", "nubuck", "lambskin", "nappa", "皮"))
    is_varsity = any(k in gtype_lower for k in ("varsity", "wool", "college", "baseball"))
    is_formal_wear = any(k in gtype_lower for k in ("wedding", "gown", "bridal", "evening", "formal wear", "silk", "satin", "婚纱", "礼服", "絲綢", "緞"))
    is_tweed = any(k in gtype_lower for k in ("tweed", "boucle", "bouclé", "pique", "piqué", "chanel", "structured jacket", "粗花呢"))
    is_suit = any(k in gtype_lower for k in ("blazer", "suit jacket", "sport coat", "dark jacket", "西装", "西裝"))

    if is_formal_wear:
        # Wedding/formal: full top-to-bottom coverage, hemline band gets extra attention
        crop_specs = [
            ("full_front",   0.05, 0.05, 0.95, 0.95),
            ("top_left",     0.00, 0.00, 0.55, 0.50),
            ("top_right",    0.45, 0.00, 1.00, 0.50),
            ("mid_left",     0.00, 0.25, 0.55, 0.75),
            ("mid_right",    0.45, 0.25, 1.00, 0.75),
            ("bot_left",     0.00, 0.50, 0.55, 1.00),
            ("bot_right",    0.45, 0.50, 1.00, 1.00),
            ("hem_band",     0.00, 0.72, 1.00, 1.00),
            ("bodice",       0.15, 0.00, 0.85, 0.45),
        ]
    elif is_tweed:
        # Structured jacket: lower hem stain focus + button placket + collar + full grid
        crop_specs = [
            ("lower_left",   0.00, 0.55, 0.55, 1.00),  # lower left panel — stain hotspot
            ("lower_right",  0.45, 0.55, 1.00, 1.00),  # lower right panel
            ("button_strip", 0.30, 0.10, 0.70, 0.95),  # button placket center strip
            ("full_front",   0.05, 0.05, 0.95, 0.95),
            ("upper_body",   0.08, 0.00, 0.92, 0.55),
            ("lower_body",   0.08, 0.45, 0.92, 1.00),
            ("left_panel",   0.00, 0.10, 0.52, 0.90),
            ("right_panel",  0.48, 0.10, 1.00, 0.90),
            ("collar_lapel", 0.10, 0.00, 0.90, 0.35),
        ]
    elif is_suit:
        # Dark blazer/suit: full coverage to detect scattered lint
        crop_specs = [
            ("full_front",   0.05, 0.05, 0.95, 0.95),
            ("left_panel",   0.00, 0.05, 0.55, 0.95),
            ("right_panel",  0.45, 0.05, 1.00, 0.95),
            ("upper_body",   0.05, 0.00, 0.95, 0.55),
            ("lower_body",   0.05, 0.45, 0.95, 1.00),
            ("lapel_collar", 0.10, 0.00, 0.90, 0.40),
            ("left_elbow",   0.00, 0.35, 0.50, 0.85),
            ("right_elbow",  0.50, 0.35, 1.00, 0.85),
            ("center_chest", 0.25, 0.10, 0.75, 0.70),
        ]
    elif is_leather:
        # Leather/suede: dense full-coverage grid to catch widespread surface staining
        crop_specs = [
            ("full_front",   0.05, 0.05, 0.95, 0.95),
            ("top_left",     0.00, 0.00, 0.55, 0.55),
            ("top_center",   0.22, 0.00, 0.78, 0.55),
            ("top_right",    0.45, 0.00, 1.00, 0.55),
            ("mid_left",     0.00, 0.22, 0.55, 0.78),
            ("mid_center",   0.22, 0.22, 0.78, 0.78),
            ("mid_right",    0.45, 0.22, 1.00, 0.78),
            ("bot_left",     0.00, 0.45, 0.55, 1.00),
            ("bot_right",    0.45, 0.45, 1.00, 1.00),
        ]
    elif is_down_jacket:
        # 3x3 dense grid covering the full garment, overlapping by ~20%
        crop_specs = [
            ("top_left",     0.00, 0.00, 0.55, 0.55),
            ("top_center",   0.22, 0.00, 0.78, 0.55),
            ("top_right",    0.45, 0.00, 1.00, 0.55),
            ("mid_left",     0.00, 0.22, 0.55, 0.78),
            ("mid_center",   0.22, 0.22, 0.78, 0.78),
            ("mid_right",    0.45, 0.22, 1.00, 0.78),
            ("bot_left",     0.00, 0.45, 0.55, 1.00),
            ("bot_center",   0.22, 0.45, 0.78, 1.00),
            ("bot_right",    0.45, 0.45, 1.00, 1.00),
        ]
    elif is_varsity:
        # Varsity/wool: collar band + contrast panels + full body
        crop_specs = [
            ("collar_band",  0.00, 0.00, 1.00, 0.32),  # dark collar — dust accumulation
            ("left_chest",   0.00, 0.18, 0.52, 0.72),
            ("right_chest",  0.48, 0.18, 1.00, 0.72),
            ("full_front",   0.05, 0.08, 0.95, 0.92),
            ("upper_body",   0.10, 0.00, 0.90, 0.52),
            ("lower_body",   0.10, 0.48, 0.90, 1.00),
            ("left_panel",   0.00, 0.08, 0.55, 0.95),
            ("right_panel",  0.45, 0.08, 1.00, 0.95),
            ("center_zip",   0.28, 0.05, 0.72, 0.95),
        ]
    elif is_shoes:
        # Hotspot crops for shoes: toe boxes, heels, sides
        crop_specs = [
            ("left_toe",     0.00, 0.00, 0.52, 0.55),
            ("right_toe",    0.48, 0.00, 1.00, 0.55),
            ("left_heel",    0.00, 0.45, 0.52, 1.00),
            ("right_heel",   0.48, 0.45, 1.00, 1.00),
            ("center_lace",  0.20, 0.10, 0.80, 0.70),
            ("left_side",    0.00, 0.20, 0.40, 0.90),
            ("right_side",   0.60, 0.20, 1.00, 0.90),
            ("full_top",     0.05, 0.00, 0.95, 0.60),
            ("sole_edge",    0.05, 0.65, 0.95, 1.00),
        ]
    else:
        # Standard dense layout: 5 half-splits + 4 corners
        crop_specs = [
            ("center_panel", 0.15, 0.15, 0.85, 0.85),
            ("left_panel",   0.00, 0.15, 0.58, 0.92),
            ("right_panel",  0.42, 0.15, 1.00, 0.92),
            ("upper_panel",  0.12, 0.00, 0.88, 0.58),
            ("lower_panel",  0.12, 0.42, 0.88, 1.00),
            ("top_left",     0.00, 0.00, 0.55, 0.55),
            ("top_right",    0.45, 0.00, 1.00, 0.55),
            ("bot_left",     0.00, 0.45, 0.55, 1.00),
            ("bot_right",    0.45, 0.45, 1.00, 1.00),
        ]

    crops: list[dict] = []
    for crop_label, x1, y1, x2, y2 in crop_specs[: max(0, settings.OPENAI_DETECT_MAX_FOCUS_CROPS)]:
        left = int(width * x1)
        top = int(height * y1)
        right = int(width * x2)
        bottom = int(height * y2)
        if right - left < 220 or bottom - top < 220:
            continue

        crop = image.crop((left, top, right, bottom))
        buffer = BytesIO()
        crop.save(buffer, format="JPEG", quality=92)
        image_content = _prepare_image_content_from_bytes(buffer.getvalue(), f"{file_path}#{crop_label}.jpg")
        if not image_content:
            continue

        crops.append({
            "crop_label": crop_label,
            "image_content": image_content,
            "region_norm": {
                "x": left / width,
                "y": top / height,
                "w": (right - left) / width,
                "h": (bottom - top) / height,
            },
        })
    return crops


def _project_crop_issue_to_full(issue: dict, region_norm: dict) -> dict:
    """Convert crop-relative bbox back into full-image normalized coordinates."""
    projected = dict(issue)
    bbox_x = issue.get("bbox_x")
    bbox_y = issue.get("bbox_y")
    bbox_w = issue.get("bbox_w")
    bbox_h = issue.get("bbox_h")
    if None in (bbox_x, bbox_y, bbox_w, bbox_h):
        return projected

    region_x = region_norm["x"]
    region_y = region_norm["y"]
    region_w = region_norm["w"]
    region_h = region_norm["h"]
    projected["bbox_x"] = min(1.0, max(0.0, region_x + bbox_x * region_w))
    projected["bbox_y"] = min(1.0, max(0.0, region_y + bbox_y * region_h))
    projected["bbox_w"] = min(1.0 - projected["bbox_x"], max(0.01, bbox_w * region_w))
    projected["bbox_h"] = min(1.0 - projected["bbox_y"], max(0.01, bbox_h * region_h))
    return projected


def _build_system_prompt() -> str:
    """Build the system prompt with expert knowledge for garment inspection."""
    return f"""You are a professional garment inspection assistant for a dry-cleaning business. Your task is to examine clothing item photos and identify ALL visible problems that need attention before cleaning.

MANDATORY: You MUST report EVERY visible issue. Missing a real issue is a serious business failure. When in doubt, report it with a lower confidence score rather than omitting it.

Look for these types of issues:
- Stains: ANY localized discoloration, smudge, grease mark, water ring, dirty patch, or color transfer that differs from surrounding fabric.
- Fabric damage: tears, holes, fraying, worn-through areas, needle punctures, scratch marks on nylon/down fabric.
- Pilling or bobbling on fabric surface.
- Missing buttons, broken zippers, loose threads.
- Fading or discoloration in specific areas.
- Wear marks / abrasion: areas where surface finish is matte, lighter, or darker due to rubbing.
- For shoes: toe-box dirtiness, heel collar grime, sidewall dirt, sole edge discoloration — inspect BOTH shoes independently.

Verified reference patterns from real inspections:
{_sample_issue_archetypes()}

For each issue you find, provide:
- issue_type: one of [stain, tear, hole, wear, wrinkle, fade, missing_button, zipper, pilling, other]
- severity_level: 1 (minor), 2 (moderate), or 3 (severe)
- position_desc: precise location — must include left/right side + garment region + sub-region
- confidence_score: 0.0-1.0 (calibrated — see below)
- bbox_x, bbox_y, bbox_w, bbox_h: bounding box as fraction of image dimensions (0.0-1.0)

Confidence calibration (strict, never use same value for all):
- 0.85-0.98: crystal clear, strong color/texture contrast with surrounding fabric.
- 0.70-0.84: clearly visible but partially affected by lighting or fold angle.
- 0.50-0.69: plausible localized abnormality, not fully certain but likely real.
- 0.30-0.49: weak candidate — visible local difference, matches known problem archetype.
- 0.20-0.29: very subtle — only use when garment type is known to have this issue at this location.
- Use up to 2 decimal places. Reflect strength differences between issues.

Severity calibration:
- 1 = small/localized issue, limited area.
- 2 = clearly visible or multiple spots in one region.
- 3 = large area, structural damage, or severe staining.

Position description (be specific):
- Good: "right sleeve forearm, 8cm above wrist cuff, gray abrasion rub mark".
- Bad: "front" or "sleeve" (too generic).

CRITICAL rules:
- If you see MULTIPLE distinct spots/marks, report EACH as a SEPARATE issue with its own bbox.
- Do NOT merge multiple spots into one entry.
- Do NOT return early with an empty list unless the garment is genuinely pristine.
- Respond with ONLY valid JSON. No other text."""
def _build_stain_fallback_prompt(garment_desc: str, photo_desc: str, note: str) -> str:
    """Second pass prompt used when primary detection returns zero issues."""
    staff_note = f"\nStaff notes: {note}" if note else ""
    return f"""Look again carefully at this {garment_desc} for any stains or marks that may have been missed.

Photos: {photo_desc}{staff_note}

Check specifically for:
- Discoloration or marks on collar, cuffs, underarms
- Ring marks, splash marks, or irregular color patches
- Any localized area that looks different from surrounding fabric

Return JSON with only issue_type="stain" items that have confidence_score >= 0.25.
If you genuinely cannot see any stains, return an empty issues array.
"""


def _build_high_recall_rescue_prompt(garment_desc: str, photo_index: int, label: str, note: str) -> str:
        """Last-pass high-recall prompt to avoid false all-clear outputs."""
        staff_note = f"\nStaff notes: {note}" if note else ""
        return f"""High-recall rescue pass for garment inspection.

Garment: {garment_desc}
Photo: Image {photo_index} ({label}){staff_note}

Goal:
- Prefer recall over precision.
- If there is any plausible localized abnormality (stain/discoloration/wear/tear), return it as a candidate.
- Only return empty if the garment truly looks pristine with no localized anomalies.

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "issue_type": "<type_code>",
            "severity_level": <1|2|3>,
            "position_desc": "<precise location>",
            "confidence_score": <0.0-1.0>,
            "bbox_x": <0.0-1.0>,
            "bbox_y": <0.0-1.0>,
            "bbox_w": <0.0-1.0>,
            "bbox_h": <0.0-1.0>,
            "photo_index": {photo_index}
        }}
    ]
}}

Use confidence 0.25-0.55 for weak but plausible candidates.
Type codes: stain, tear, hole, wear, wrinkle, fade, missing_button, zipper, pilling, other."""


def _build_focus_crop_prompt(garment_desc: str, photo_index: int, label: str, crop_label: str, note: str, garment_type: str = "") -> str:
        """Prompt for zoomed local crop inspection based on the user's example issue patterns."""
        staff_note = f"\nStaff notes: {note}" if note else ""
        type_hint = _build_garment_type_hint(garment_type)
        return f"""Inspect this zoomed local crop from a garment photo.

Garment: {garment_desc}
Source photo: Image {photo_index} ({label})
Crop region label: {crop_label}{staff_note}{type_hint}
This crop is meant to reveal subtle local issues that whole-image scans often miss.
Prioritize patterns specific to this garment type. General examples:
- faint gray smudge on light shell jacket panels
- gray scratch marks on individual down jacket puff panels
- toe-box yellowing or grime on sneakers
- scattered white lint flecks on dark blazer/suit fabric
- bright contrasting stain (lime/orange) on pastel structured jacket lower panel
- soiling patch on white satin/silk reducing fabric sheen

Rules:
- Prefer recall over precision for this crop.
- Return only issues visible inside this crop.
- Weak but plausible local abnormalities: confidence 0.22-0.55.

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "issue_type": "<type_code>",
            "severity_level": <1|2|3>,
            "position_desc": "<precise location>",
            "confidence_score": <0.0-1.0>,
            "bbox_x": <0.0-1.0>,
            "bbox_y": <0.0-1.0>,
            "bbox_w": <0.0-1.0>,
            "bbox_h": <0.0-1.0>,
            "photo_index": {photo_index}
        }}
    ]
}}"""


def _build_precision_review_prompt(garment_desc: str, photo_index: int, label: str, note: str, candidates: list[dict]) -> str:
        """Final precision-oriented review using the sample archetypes as guidance."""
        staff_note = f"\nStaff notes: {note}" if note else ""
        return f"""Precision review for one garment photo.

Garment: {garment_desc}
Photo: Image {photo_index} ({label}){staff_note}
Candidate issues (JSON): {json.dumps(candidates, ensure_ascii=True)}

Use these confirmed reference archetypes to judge the candidates:
{_sample_issue_archetypes()}

Tasks:
1) Remove any candidate that is better explained by lighting, folds, seam shadow, reflection, normal texture, or nap direction.
2) Keep candidates that match the positive archetypes even if contrast is subtle, as long as there is localized evidence.
3) Improve position_desc so it names the exact panel/edge/cuff/toe/sole/pocket area.
4) Recalibrate confidence_score precisely. Do not use repeated default scores.
5) Use issue_type="stain" for transfer, grime, grease, discoloration, and dirty smears; use "wear" for abrasion haze without obvious residue; use "hole" or "tear" for puncture or split.

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "issue_type": "<type_code>",
            "severity_level": <1|2|3>,
            "position_desc": "<precise location>",
            "confidence_score": <0.0-1.0>,
            "bbox_x": <0.0-1.0>,
            "bbox_y": <0.0-1.0>,
            "bbox_w": <0.0-1.0>,
            "bbox_h": <0.0-1.0>,
            "photo_index": {photo_index}
        }}
    ]
}}"""


def _build_verify_prompt(garment_desc: str, photo_index: int, label: str, candidates: list[dict]) -> str:
        """Verification pass prompt to refine confidence and remove weak false positives."""
        return f"""Re-check the same garment photo and verify candidate issues.

Garment: {garment_desc}
Photo: Image {photo_index} ({label})
Candidate issues (JSON): {json.dumps(candidates, ensure_ascii=True)}

Tasks:
1) Keep only candidates with real visual evidence.
2) Correct issue_type/severity_level/position_desc/bbox if needed.
3) Re-calibrate confidence_score using evidence strength. Do not use identical confidence by default.
4) If all candidates look wrong, return an empty list.

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "issue_type": "<type_code>",
            "severity_level": <1|2|3>,
            "position_desc": "<precise location>",
            "confidence_score": <0.0-1.0>,
            "bbox_x": <0.0-1.0>,
            "bbox_y": <0.0-1.0>,
            "bbox_w": <0.0-1.0>,
            "bbox_h": <0.0-1.0>,
            "photo_index": {photo_index}
        }}
    ]
}}"""


def _build_hotspot_scan_prompt(garment_desc: str, photo_index: int, label: str, note: str) -> str:
    """Garment-type-specific hotspot scan targeting the most error-prone areas."""
    staff_note = f"\nStaff notes: {note}" if note else ""
    gtype_lower = garment_desc.lower()
    is_down = any(k in gtype_lower for k in ("down", "puffer", "puff", "jacket"))
    is_shoes = any(k in gtype_lower for k in ("shoe", "sneaker", "boot"))
    is_leather = any(k in gtype_lower for k in ("leather", "suede", "nubuck", "lambskin", "nappa", "皮"))
    is_varsity = any(k in gtype_lower for k in ("varsity", "wool", "college", "baseball", "bomber"))
    is_formal_wear = any(k in gtype_lower for k in ("wedding", "gown", "bridal", "evening", "silk", "satin", "formal", "婚纱", "礼服"))
    is_tweed = any(k in gtype_lower for k in ("tweed", "boucle", "bouclé", "pique", "piqué", "chanel", "structured jacket", "粗花呢"))
    is_suit = any(k in gtype_lower for k in ("blazer", "suit jacket", "sport coat", "dark jacket", "navy jacket", "西装", "西裝"))
    is_light_shell = any(k in gtype_lower for k in ("shell", "jacket", "coat", "windbreaker"))

    is_shirt = any(k in gtype_lower for k in ("shirt", "blouse", "polo", "dress shirt"))
    is_sweater = any(k in gtype_lower for k in ("sweater", "cashmere", "knit", "cardigan"))
    is_trench = any(k in gtype_lower for k in ("trench", "overcoat", "trenchcoat"))
    is_jeans = any(k in gtype_lower for k in ("jeans", "denim"))

    if is_shoes:
        hotspot_instructions = """You are scanning WHITE or LIGHT shoes. Focus exclusively on:
1. Toe cap area on EACH shoe: gray/brown dirtiness from the front tip.
2. Heel collar on EACH shoe: grime ring at the ankle opening.
3. Sidewall between upper and sole: continuous dirt line.
4. Tongue surface and around laces: yellowing or gray transfer.
Report LEFT and RIGHT shoe issues separately."""
    elif is_leather or any(k in gtype_lower for k in ("suede", "nubuck", "lambskin", "nappa")):
        is_suede = any(k in gtype_lower for k in ("suede", "nubuck"))
        if is_suede:
            hotspot_instructions = """You are scanning a SUEDE or NUBUCK garment. Focus on:
1. Inner collar seam area: concentrated orange-brown or rust-colored contact stain — look
   carefully right where the collar lining folds against the suede body. Even a 2cm spot counts.
2. Upper back collar line: darker band from repeated neck contact.
3. Front body: any irregular dark patch where suede appears more saturated than surrounding
   areas — this is staining, NOT nap direction variation. Stains have irregular spatial
   boundaries; nap changes are more uniform and directional.
4. Cuffs and pocket edges: oil/grime accumulation from hand contact.
Be thorough — suede stains are REAL even if subtle against the tan/beige background."""
        else:
            hotspot_instructions = """You are scanning a LEATHER jacket (soft nappa/lambskin).
This garment type commonly shows WIDESPREAD mottled dark surface staining. Focus on:
1. ENTIRE visible front panel: look for irregular darkened areas, blotchy "wet" appearance,
   or uneven color distribution. Multiple separate dark zones = multiple stain entries.
2. The area beside/around the zipper placket: dark transfer marks or grime buildup.
3. Elbow/forearm zone: scuff marks or worn surface patches.
4. Any clear boundary between darker and lighter areas of the SAME leather panel — that
   boundary marks a stain edge. Report each zone separately.
5. The difference key: shadow follows a fold uniformly; staining creates irregular color
   boundaries that cross folds freely.
Return high recall. Even cover 50-70% of the panel area qualifies if staining is visible."""
    elif is_varsity or any(k in gtype_lower for k in ("varsity", "wool", "college", "baseball", "bomber")):
        hotspot_instructions = """You are scanning a VARSITY or WOOL jacket. Focus on:
1. Dark contrast panels (navy, black collar/sleeves): check for dust, lint, or white
   particulate accumulation that lightens the dark fabric — this IS an issue.
2. Light/white wool body: check for gray or yellow tinge vs pristine white areas.
   Look especially at center front, around pocket openings.
3. Metal hardware (snaps, zipper pullers): oxidation or tarnish at the base.
4. Hem and cuff edges: grime accumulation from handling."""
    elif is_formal_wear:
        hotspot_instructions = """You are scanning WHITE SATIN/SILK FORMAL WEAR (wedding dress, evening gown).
Focus on:
1. ENTIRE visible surface: compare reflectivity panel by panel. Soiled satin appears MATTE/DULL
   while clean satin is reflective and shiny. Any 5cm+ dull zone = potential soiling.
2. Hemline / lower skirt area: ground-contact brown or gray soil — even faint discoloration counts.
3. Bodice upper chest area: any grayish or yellowish cast compared to pristine white.
4. Underarm zones: perspiration marks with yellow or gray tinge.
5. Any irregular color — off-white, cream, gray, yellow — vs the dominant white satin.
HIGH RECALL — it is better to over-report subtle soiling than to miss it."""
    elif is_tweed:
        hotspot_instructions = """You are scanning a PINK/PASTEL STRUCTURED JACKET (tweed, boucle, piqué).
Focus on:
1. LOWER FRONT PANEL near the hem: look for any bright contrasting stain — yellow-green,
   lime, orange, or other vivid color against the light pink/pastel fabric. These stand out
   strongly and are HIGH CONFIDENCE — report immediately.
2. Button placket center strip: discoloration between or around covered buttons.
3. Collar lapel inner face: skin contact marks or dark ring.
4. Fabric note: the woven piqué/boucle texture is intentional — flag COLOR anomalies only."""
    elif is_suit:
        hotspot_instructions = """You are scanning a DARK BLAZER or SUIT JACKET (navy, black, charcoal).
Focus on:
1. ENTIRE visible dark fabric surface: look for scattered WHITE or LIGHT-COLORED LINT FLECKS,
   dust particles, or fiber fragments — small bright specks (2-8mm) against the dark background.
   4+ visible particles = a reportable issue. Report as "scattered lint particles on [panel]".
2. Front left and right panels: any area appearing lighter or different texture from surrounding
   dark fabric — abrasion or wear zones.
3. Lapel and collar inner fold: contact marks or transfer from skin/neck.
4. Elbow area: shiny worn abrasion zones in woven fabric."""
    elif is_down:
        hotspot_instructions = """You are scanning a DOWN JACKET. Focus on:
1. FEATHER LEAK CHECK — examine EVERY quilting seam intersection for a bright-white or pale
   feather tip poking through the fabric. On dark jackets it appears as a tiny bright spike or
   filament emerging from the seam. Report each occurrence as issue_type=hole, confidence≥0.25.
2. Every INDIVIDUAL puff panel that shows ANY gray, dark, or scratch-like rub mark — each panel
   is a separate issue (stain or wear type).
3. Pocket flap edges and zipper areas: discoloration or wear marks.
4. Lower front panels and side panels: diffuse grime or rub accumulation.
Be exhaustive — if 4 panels are marked, report 4 issues."""
    elif is_light_shell:
        hotspot_instructions = """You are scanning a LIGHT-COLORED SHELL JACKET (white, gray, pearl, cream). Focus on:
1. Front chest panels: very subtle diffuse gray stains even if low contrast.
2. Sleeve cuffs: grime ring or yellowing.
3. Collar and neckline: oils or transfer.
4. Underarm area: discoloration.
5. Any area that looks locally more matte or dimmer than surrounding fabric."""
    elif is_shirt:
        hotspot_instructions = """You are scanning a SHIRT or BLOUSE. Focus on:
1. INNER COLLAR: gray or yellowish ring inside the collar fold — compare to outer collar.
2. CUFFS (inner face): dark grime band at the edge.
3. UNDERARM: yellow-brown perspiration stain, bilateral.
4. Front placket near buttons: food drop spots.
HIGH RECALL — collar rings and cuff grime are often subtle on patterned or non-white shirts."""
    elif is_sweater:
        hotspot_instructions = """You are scanning a SWEATER, KNITWEAR, or CASHMERE garment. Focus on:
1. Surface pilling: raised fuzzy clusters across body and elbows — each cluster zone = reportable.
2. Snags/pulls: single strand pulled into a loop or ridge.
3. Small holes: 3-10mm gaps in the knit (possible moth damage) — check seam areas.
4. Underarm: discoloration on lighter colors."""
    elif is_trench:
        hotspot_instructions = """You are scanning a TRENCH COAT or OVERCOAT. Focus on:
1. INNER COLLAR LINING: gray-brown contact ring along entire inner collar face.
2. Shoulder panels: irregular dark moisture patch.
3. Cuffs (inner and outer): grime band.
4. Hem: ground-contact soiling."""
    elif is_jeans:
        hotspot_instructions = """You are scanning JEANS or DENIM. Focus on:
1. Thigh and hip pocket area: ink, pen, or oil stain with sharp edges.
2. Knee zone: unintentional abrasion lightening vs surrounding fabric.
3. Belt loop area: concentrated grime ring.
4. Pocket corners: wear marks."""
    else:
        hotspot_instructions = """Focus on the most contamination-prone areas:
collar, cuffs, underarms, pocket openings, lower hem, and any area visibly different from surrounding fabric."""

    return f"""Hotspot-targeted garment inspection pass.

Garment: {garment_desc}
Photo: Image {photo_index} ({label}){staff_note}

{hotspot_instructions}

Rules:
- Prefer high recall. Missing a real issue is worse than a false positive here.
- Use confidence 0.20-0.55 for subtle but plausible issues in the hotspot regions.
- Report each distinct mark as a SEPARATE issue entry.

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "issue_type": "<type_code>",
            "severity_level": <1|2|3>,
            "position_desc": "<precise location>",
            "confidence_score": <0.0-1.0>,
            "bbox_x": <0.0-1.0>,
            "bbox_y": <0.0-1.0>,
            "bbox_w": <0.0-1.0>,
            "bbox_h": <0.0-1.0>,
            "photo_index": {photo_index}
        }}
    ]
}}
Type codes: stain, tear, hole, wear, wrinkle, fade, missing_button, zipper, pilling, other"""


def ai_detect_openai(photo_file_paths: list[str], garment_type: str,
                      color: str = "", brand: str = "", note: str = "",
                      fabric_type: str = "", service_type: str = "",
                      photo_labels: list[str] | None = None) -> list[dict]:
    """Use GPT-4o Vision to detect garment defects with per-photo retries for stability."""
    import openai

    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    model_candidates = [settings.OPENAI_DETECT_PRIMARY_MODEL] + [
        m.strip() for m in settings.OPENAI_DETECT_FALLBACK_MODELS.split(",") if m.strip()
    ]
    # Secondary (cheaper/faster) model candidates for non-critical passes
    secondary_candidates = [settings.OPENAI_DETECT_SECONDARY_MODEL] + [
        m.strip() for m in settings.OPENAI_DETECT_FALLBACK_MODELS.split(",") if m.strip()
    ]

    def _chat_json_with_fallback(
        prompt: str,
        image_content: dict,
        max_tokens: int,
        temperature: float,
        stage: str,
        models: list[str] | None = None,
    ) -> tuple[dict, str]:
        candidates = models if models is not None else model_candidates
        last_err: Exception | None = None
        for model in candidates:
            for attempt in range(max(1, settings.OPENAI_DETECT_MAX_RETRIES)):
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": _build_system_prompt()},
                            {"role": "user", "content": [{"type": "text", "text": prompt}, image_content]},
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=max_tokens,
                        temperature=temperature,
                        seed=42,
                    )
                    raw_content = response.choices[0].message.content
                    if not raw_content:
                        raise ValueError("OpenAI returned empty content")
                    return json.loads(raw_content), model
                except Exception as e:
                    last_err = e
                    logger.warning("AI %s failed (model=%s, attempt=%d): %s", stage, model, attempt + 1, e)
                    if attempt < max(1, settings.OPENAI_DETECT_MAX_RETRIES) - 1:
                        time.sleep(2 ** attempt)
        assert last_err is not None
        raise last_err

    def _avg_confidence(issues: list[dict]) -> float:
        if not issues:
            return 0.0
        return sum(i.get("confidence_score", 0.0) for i in issues) / len(issues)

    def _normalize_issues(raw_issues: list[dict], default_photo_index: int) -> list[dict]:
        normalized: list[dict] = []
        for iss in raw_issues:
            itype = iss.get("issue_type", "other")
            if itype not in VALID_ISSUE_TYPES:
                itype = "other"

            bbox_x = iss.get("bbox_x")
            bbox_y = iss.get("bbox_y")
            bbox_w = iss.get("bbox_w")
            bbox_h = iss.get("bbox_h")
            if bbox_x is not None:
                bbox_x = min(1.0, max(0.0, float(bbox_x)))
            if bbox_y is not None:
                bbox_y = min(1.0, max(0.0, float(bbox_y)))
            if bbox_w is not None:
                bbox_w = min(1.0, max(0.01, float(bbox_w)))
            if bbox_h is not None:
                bbox_h = min(1.0, max(0.01, float(bbox_h)))
            if bbox_x is not None and bbox_w is not None and bbox_x + bbox_w > 1.0:
                bbox_w = 1.0 - bbox_x
            if bbox_y is not None and bbox_h is not None and bbox_y + bbox_h > 1.0:
                bbox_h = 1.0 - bbox_y

            raw_idx = iss.get("photo_index")
            try:
                photo_index = int(raw_idx) if raw_idx is not None else default_photo_index
            except (TypeError, ValueError):
                photo_index = default_photo_index
            if photo_index < 1:
                photo_index = default_photo_index

            normalized.append({
                "issue_type": itype,
                "severity_level": min(3, max(1, int(iss.get("severity_level", 1)))),
                "position_desc": str(iss.get("position_desc", ""))[:200],
                "confidence_score": round(min(1.0, max(0.0, float(iss.get("confidence_score", 0.65)))), 2),
                "bbox_x": bbox_x,
                "bbox_y": bbox_y,
                "bbox_w": bbox_w,
                "bbox_h": bbox_h,
                "photo_index": photo_index,
            })
        return normalized

    garment_parts = [garment_type]
    if color:
        garment_parts.append(f"color: {color}")
    if brand:
        garment_parts.append(f"brand: {brand}")
    if fabric_type:
        garment_parts.append(f"fabric: {fabric_type}")
    if service_type:
        garment_parts.append(f"requested service: {service_type}")
    garment_desc = " | ".join(garment_parts)

    loaded_images: list[tuple[int, str, dict, str]] = []
    for idx, file_path in enumerate(photo_file_paths[:10]):
        img_content = _prepare_image_content(file_path)
        if img_content is None:
            logger.warning("Skipping unloadable image %d: %s", idx + 1, file_path)
            continue
        label = (photo_labels[idx] if photo_labels and idx < len(photo_labels) else None) or f"photo_{idx + 1}"
        loaded_images.append((idx + 1, file_path, img_content, label))

    if not loaded_images:
        logger.warning("No loadable images found for AI detection")
        return []

    all_issues: list[dict] = []
    failed_photo_count = 0
    garment_type_hint = _build_garment_type_hint(garment_type)
    for photo_index, file_path, image_content, label in loaded_images:
        staff_note = f"\nStaff notes: {note}" if note else ""
        per_photo_prompt = f"""Inspect this garment photo for pre-cleaning defect documentation.

Garment: {garment_desc}
Current photo: Image {photo_index} ({label}){staff_note}{garment_type_hint}
High-recall mode:
- Focus on stain recall first, then non-stain defects.
- If a region looks suspicious but not fully certain, keep it as a candidate with confidence 0.25-0.55.
- Do NOT default to empty. Return empty only when this photo is truly clean and uniform.

Return ONLY valid JSON:
{{
  "issues": [
    {{
      "issue_type": "<type_code>",
      "severity_level": <1|2|3>,
      "position_desc": "<precise location>",
      "confidence_score": <0.0-1.0>,
      "bbox_x": <0.0-1.0>,
      "bbox_y": <0.0-1.0>,
      "bbox_w": <0.0-1.0>,
      "bbox_h": <0.0-1.0>,
      "photo_index": {photo_index}
    }}
  ]
}}

Type codes: stain, tear, hole, wear, wrinkle, fade, missing_button, zipper, pilling, other
If no convincing issue is visible, return {{"issues": []}}."""

        photo_issues: list[dict] = []
        last_err: Exception | None = None
        try:
            parsed, used_model = _chat_json_with_fallback(per_photo_prompt, image_content, 1800, 0, f"primary-photo-{photo_index}")
            logger.info("Primary detection used model=%s on photo %d", used_model, photo_index)
            primary_issues = _normalize_issues(parsed.get("issues", []), photo_index)
        except Exception as retry_err:
            last_err = retry_err
            logger.warning("AI detection photo %d failed across model cascade: %s", photo_index, retry_err)
            primary_issues = []

        if not primary_issues and last_err is not None:
            failed_photo_count += 1

        if primary_issues:
            # Skip verify pass when primary already found many high-confidence issues —
            # it wastes time and can incorrectly drop real findings.
            avg_conf = _avg_confidence(primary_issues)
            skip_verify = len(primary_issues) >= 4 and avg_conf >= 0.68
            if skip_verify:
                logger.info("Skipping verify pass (primary found %d issues, avg_conf=%.2f)", len(primary_issues), avg_conf)
                photo_issues.extend(primary_issues)
            else:
                # Verification pass: use secondary model (faster/cheaper).
                try:
                    verify_prompt = _build_verify_prompt(garment_desc, photo_index, label, primary_issues)
                    verify_parsed, verify_model = _chat_json_with_fallback(
                        verify_prompt, image_content, 1400, 0,
                        f"verify-photo-{photo_index}", models=secondary_candidates,
                    )
                    logger.info("Verify pass used model=%s on photo %d", verify_model, photo_index)
                    verified_issues = _normalize_issues(verify_parsed.get("issues", []), photo_index)
                    if verified_issues:
                        photo_issues.extend(verified_issues)
                    else:
                        photo_issues.extend(primary_issues)
                except Exception as verify_err:
                    logger.warning("Verification pass failed on photo %d: %s", photo_index, verify_err)
                    photo_issues.extend(primary_issues)

        # Stain-only fallback to reduce first-run false negatives. Uses secondary model.
        if not photo_issues:
            try:
                fallback_prompt = _build_stain_fallback_prompt(garment_desc, f"Image {photo_index}: {label}", note)
                parsed_fallback, fallback_model = _chat_json_with_fallback(
                    fallback_prompt, image_content, 1200, 0,
                    f"fallback-photo-{photo_index}", models=secondary_candidates,
                )
                logger.info("Fallback pass used model=%s on photo %d", fallback_model, photo_index)
                fallback_issues = _normalize_issues(parsed_fallback.get("issues", []), photo_index)
                fallback_issues = [i for i in fallback_issues if i["issue_type"] == "stain" and i["confidence_score"] >= 0.22]
                photo_issues.extend(fallback_issues)
            except Exception as fallback_err:
                logger.warning("Fallback detection failed on photo %d: %s", photo_index, fallback_err)

        # Hotspot scan pass — runs when fewer than 3 issues found. Uses secondary model.
        if len(photo_issues) < 3:
            try:
                hotspot_prompt = _build_hotspot_scan_prompt(garment_desc, photo_index, label, note)
                hotspot_parsed, hotspot_model = _chat_json_with_fallback(
                    hotspot_prompt, image_content, 1600, 0,
                    f"hotspot-photo-{photo_index}", models=secondary_candidates,
                )
                logger.info("Hotspot scan used model=%s on photo %d", hotspot_model, photo_index)
                hotspot_issues = _normalize_issues(hotspot_parsed.get("issues", []), photo_index)
                hotspot_issues = [i for i in hotspot_issues if i["confidence_score"] >= 0.20]
                photo_issues.extend(hotspot_issues)
            except Exception as hotspot_err:
                logger.warning("Hotspot scan failed on photo %d: %s", photo_index, hotspot_err)

        if len(photo_issues) < 4 and settings.OPENAI_DETECT_MAX_FOCUS_CROPS > 0:
            crops = _generate_focus_crops(file_path, garment_type)
            if crops:
                def _process_crop(crop: dict) -> list[dict]:
                    try:
                        crop_prompt = _build_focus_crop_prompt(
                            garment_desc, photo_index, label, crop["crop_label"], note, garment_type
                        )
                        # Use secondary model for crops — faster and cheap
                        crop_parsed, crop_model = _chat_json_with_fallback(
                            crop_prompt, crop["image_content"], 1000, 0,
                            f"focus-crop-{photo_index}-{crop['crop_label']}",
                            models=secondary_candidates,
                        )
                        logger.info(
                            "Focus crop used model=%s on photo %d crop=%s",
                            crop_model, photo_index, crop["crop_label"],
                        )
                        crop_issues = _normalize_issues(crop_parsed.get("issues", []), photo_index)
                        return [
                            _project_crop_issue_to_full(issue, crop["region_norm"])
                            for issue in crop_issues
                            if issue["confidence_score"] >= 0.18
                        ]
                    except Exception as crop_err:
                        logger.warning(
                            "Focus crop detection failed on photo %d crop=%s: %s",
                            photo_index, crop["crop_label"], crop_err,
                        )
                        return []

                max_workers = min(len(crops), settings.OPENAI_DETECT_CROP_WORKERS)
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
                    for crop_results in pool.map(_process_crop, crops):
                        photo_issues.extend(crop_results)

        if photo_issues:
            photo_issues = _deduplicate_issues(photo_issues)
            try:
                precision_prompt = _build_precision_review_prompt(
                    garment_desc,
                    photo_index,
                    label,
                    note,
                    photo_issues,
                )
                precision_parsed, precision_model = _chat_json_with_fallback(
                    precision_prompt,
                    image_content,
                    1600,
                    0,
                    f"precision-review-{photo_index}",
                )
                logger.info("Precision review used model=%s on photo %d", precision_model, photo_index)
                refined_issues = _normalize_issues(precision_parsed.get("issues", []), photo_index)
                if refined_issues:
                    photo_issues = _deduplicate_issues(refined_issues)
            except Exception as precision_err:
                logger.warning("Precision review failed on photo %d: %s", photo_index, precision_err)

        all_issues.extend(photo_issues)

    if failed_photo_count == len(loaded_images):
        raise HTTPException(status_code=502, detail="AI detection failed after retries for all photos.")

    # Final rescue pass when all photos return empty but calls did not fail.
    if not all_issues and failed_photo_count < len(loaded_images):
        logger.warning("Primary + fallback produced no issues. Running high-recall rescue pass.")
        for photo_index, _file_path, image_content, label in loaded_images:
            try:
                rescue_prompt = _build_high_recall_rescue_prompt(garment_desc, photo_index, label, note)
                rescue_parsed, rescue_model = _chat_json_with_fallback(
                    rescue_prompt, image_content, 1200, 0,
                    f"rescue-photo-{photo_index}", models=secondary_candidates,
                )
                logger.info("Rescue pass used model=%s on photo %d", rescue_model, photo_index)
                rescue_issues = _normalize_issues(rescue_parsed.get("issues", []), photo_index)
                rescue_issues = [i for i in rescue_issues if i["confidence_score"] >= 0.25]
                all_issues.extend(rescue_issues)
            except Exception as rescue_err:
                logger.warning("Rescue pass failed on photo %d: %s", photo_index, rescue_err)

    deduplicated = _deduplicate_issues(all_issues)
    logger.info(
        "AI detection complete: photos=%d raw_issues=%d deduplicated=%d failed_photos=%d",
        len(loaded_images), len(all_issues), len(deduplicated), failed_photo_count,
    )
    return deduplicated


def _deduplicate_issues(issues: list[dict], iou_threshold: float = 0.5) -> list[dict]:
    """Remove duplicate issues that overlap significantly in the same photo region."""
    if len(issues) <= 1:
        return issues

    result = []
    used = set()
    for i, a in enumerate(issues):
        if i in used:
            continue
        best = a
        for j, b in enumerate(issues):
            if j <= i or j in used:
                continue
            if a["issue_type"] != b["issue_type"]:
                continue
            # Never merge issues from different photos.
            if a.get("photo_index") != b.get("photo_index"):
                continue
            # Check bbox overlap (IoU)
            if all(a.get(k) is not None and b.get(k) is not None for k in ("bbox_x", "bbox_y", "bbox_w", "bbox_h")):
                ax1, ay1 = a["bbox_x"], a["bbox_y"]
                ax2, ay2 = ax1 + a["bbox_w"], ay1 + a["bbox_h"]
                bx1, by1 = b["bbox_x"], b["bbox_y"]
                bx2, by2 = bx1 + b["bbox_w"], by1 + b["bbox_h"]
                ix1, iy1 = max(ax1, bx1), max(ay1, by1)
                ix2, iy2 = min(ax2, bx2), min(ay2, by2)
                inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                area_a = a["bbox_w"] * a["bbox_h"]
                area_b = b["bbox_w"] * b["bbox_h"]
                union = area_a + area_b - inter
                iou = inter / union if union > 0 else 0
                if iou > iou_threshold:
                    used.add(j)
                    if b.get("confidence_score", 0) > best.get("confidence_score", 0):
                        best = b
        result.append(best)
    return result


@router.post("/order-items/{item_id}/inspection")
def create_inspection(item_id: str, db: Session = Depends(get_db), user: AppUser = Depends(get_current_user)):
    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.inspection:
        return item.inspection.to_dict()
    inspection = InspectionRecord(order_item_id=item_id, inspector_id=user.id)
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection.to_dict()


@router.get("/inspections/{inspection_id}")
def get_inspection(inspection_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return insp.to_dict()


def _run_detection_background(
    inspection_id: str,
    photo_paths: list,
    photo_labels: list,
    garment_type: str,
    color: str,
    brand: str,
    note: str,
    fabric_type: str,
    service_type: str,
    photo_key: str = "",
) -> None:
    """Background thread: runs the full AI pipeline and persists results independently."""
    db = _SessionLocal()
    try:
        ai_issues = ai_detect_openai(
            photo_paths, garment_type,
            color=color, brand=brand, note=note,
            fabric_type=fabric_type, service_type=service_type,
            photo_labels=photo_labels,
        )
        ai_result = InspectionAIResult(
            inspection_id=inspection_id,
            raw_result=json.dumps(ai_issues),
        )
        db.add(ai_result)
        for ai_issue in ai_issues:
            issue = InspectionIssue(
                inspection_id=inspection_id,
                issue_type=ai_issue["issue_type"],
                severity_level=ai_issue["severity_level"],
                position_desc=ai_issue.get("position_desc", ""),
                bbox_x=ai_issue.get("bbox_x"),
                bbox_y=ai_issue.get("bbox_y"),
                bbox_w=ai_issue.get("bbox_w"),
                bbox_h=ai_issue.get("bbox_h"),
                confidence_score=ai_issue.get("confidence_score"),
                source="ai",
                photo_index=ai_issue.get("photo_index"),
            )
            db.add(issue)
        insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
        if insp:
            insp.status = InspectionStatus.COMPLETED
            if photo_key:
                insp.detected_photos_key = photo_key
        db.commit()
        logger.info(
            "Background detection completed for inspection %s: %d issues saved",
            inspection_id, len(ai_issues),
        )
    except Exception as exc:
        logger.error("Background detection failed for inspection %s: %s", inspection_id, exc)
        try:
            db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).update(
                {"status": InspectionStatus.PENDING}
            )
            db.commit()
        except Exception as db_err:
            logger.error("Failed to reset inspection status after bg failure: %s", db_err)
    finally:
        db.close()


@router.post("/inspections/{inspection_id}/detect")
def trigger_detection(inspection_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == insp.order_item_id).first()
    garment_type = item.garment_type if item else "garment"
    photos = list(item.photos) if item else []
    photo_paths = [p.file_path for p in photos]
    photo_labels = [p.photo_label or f"photo_{i+1}" for i, p in enumerate(photos)]

    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI detection unavailable: OPENAI_API_KEY is not configured")

    # Compute fingerprint of current photos to enable cache-hit detection.
    photo_key = hashlib.md5(json.dumps(sorted(photo_paths)).encode()).hexdigest() if photo_paths else ""

    # If photos haven't changed since last successful detection, return cached result.
    stored_key = getattr(insp, "detected_photos_key", None)
    if (
        insp.status == InspectionStatus.COMPLETED
        and photo_key
        and stored_key == photo_key
    ):
        logger.info(
            "Skipping re-detection for inspection %s — photos unchanged (key=%s)",
            inspection_id, photo_key,
        )
        return insp.to_dict()

    # Remove old AI issues synchronously (fast path)
    ai_issue_ids = [
        row[0]
        for row in db.query(InspectionIssue.id).filter(
            InspectionIssue.inspection_id == inspection_id,
            InspectionIssue.source == "ai",
        ).all()
    ]
    if ai_issue_ids:
        db.query(IssueEditHistory).filter(IssueEditHistory.issue_id.in_(ai_issue_ids)).delete(synchronize_session=False)
        db.query(InspectionIssue).filter(InspectionIssue.id.in_(ai_issue_ids)).delete(synchronize_session=False)
    insp.status = InspectionStatus.DETECTING
    db.commit()

    # Launch AI pipeline in a background daemon thread and return 202 immediately.
    # Clients should poll GET /inspections/{id} until status != "detecting".
    t = threading.Thread(
        target=_run_detection_background,
        args=(
            inspection_id, photo_paths, photo_labels, garment_type,
            item.color or "" if item else "",
            item.brand or "" if item else "",
            item.note or "" if item else "",
            item.fabric_type or "" if item else "",
            item.service_type or "" if item else "",
            photo_key,
        ),
        daemon=True,
    )
    t.start()

    db.refresh(insp)
    return insp.to_dict()


class IssueCreate(BaseModel):
    issue_type: str
    severity_level: int = 1
    position_desc: str = ""
    bbox_x: float | None = None
    bbox_y: float | None = None
    bbox_w: float | None = None
    bbox_h: float | None = None
    photo_index: int | None = None
    confidence_score: float | None = None
    source: str = "manual"


@router.post("/inspections/{inspection_id}/issues")
def add_manual_issue(
    inspection_id: str,
    payload: IssueCreate,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
):
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if payload.issue_type not in VALID_ISSUE_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid issue_type. Must be one of: {', '.join(sorted(VALID_ISSUE_TYPES))}")
    if payload.severity_level not in (1, 2, 3):
        raise HTTPException(status_code=422, detail="severity_level must be 1, 2, or 3")
    src = payload.source if payload.source in ("ai", "manual") else "manual"
    issue = InspectionIssue(
        inspection_id=inspection_id,
        issue_type=payload.issue_type,
        severity_level=payload.severity_level,
        position_desc=payload.position_desc,
        bbox_x=payload.bbox_x,
        bbox_y=payload.bbox_y,
        bbox_w=payload.bbox_w,
        bbox_h=payload.bbox_h,
        photo_index=payload.photo_index,
        confidence_score=payload.confidence_score,
        source=src,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue.to_dict()


# Color mapping for annotation boxes per design doc section 6.2
ISSUE_COLOR_MAP = {
    "stain": (255, 0, 0),       # Red
    "hole": (0, 0, 255),        # Blue
    "tear": (0, 0, 255),        # Blue
    "wear": (255, 200, 0),      # Yellow
    "wrinkle": (255, 165, 0),   # Orange
    "fade": (128, 0, 128),      # Purple
    "missing_button": (0, 128, 0),  # Green
    "zipper": (0, 128, 128),    # Teal
    "pilling": (255, 165, 0),   # Orange
    "other": (128, 128, 128),   # Gray
}


def generate_annotated_image(photo_bytes: bytes, issues: list[dict]) -> bytes:
    """Draw colored bounding boxes on the photo for each issue."""
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO

    img = Image.open(BytesIO(photo_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    for iss in issues:
        bx = iss.get("bbox_x")
        by = iss.get("bbox_y")
        bw = iss.get("bbox_w")
        bh = iss.get("bbox_h")
        if bx is None or by is None or bw is None or bh is None:
            continue

        x1 = int(bx * w)
        y1 = int(by * h)
        x2 = int((bx + bw) * w)
        y2 = int((by + bh) * h)
        color = ISSUE_COLOR_MAP.get(iss.get("issue_type", "other"), (128, 128, 128))

        # Draw rectangle with 3px border
        for offset in range(3):
            draw.rectangle([x1 - offset, y1 - offset, x2 + offset, y2 + offset], outline=color)

        # Label
        label = f"{iss.get('issue_type', '?')} S{iss.get('severity_level', '?')}"
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except (IOError, OSError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((x1, y1 - 18), label, font=font)
        draw.rectangle([bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2], fill=color)
        draw.text((x1, y1 - 18), label, fill=(255, 255, 255), font=font)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@router.get("/inspections/{inspection_id}/annotated/{photo_id}")
def get_annotated_image(
    inspection_id: str,
    photo_id: str,
    db: Session = Depends(get_db),
):
    """Generate and return an annotated image with bounding boxes drawn on the photo."""
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    photo = db.query(GarmentPhoto).filter(GarmentPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Check if annotated version already exists
    if photo.annotated_file_path:
        annotated_bytes = get_photo_bytes(photo.annotated_file_path)
        if annotated_bytes:
            return Response(content=annotated_bytes, media_type="image/jpeg")

    photo_bytes = get_photo_bytes(photo.file_path)
    if not photo_bytes:
        raise HTTPException(status_code=404, detail="Photo file not found")

    issues = [i.to_dict() for i in insp.issues]
    annotated_bytes = generate_annotated_image(photo_bytes, issues)

    # Save annotated image
    annotated_path, _ = save_photo(annotated_bytes, ".jpg")
    photo.annotated_file_path = annotated_path
    db.commit()

    return Response(content=annotated_bytes, media_type="image/jpeg")


@router.get("/inspections/{inspection_id}/report")
def get_inspection_report(
    inspection_id: str,
    db: Session = Depends(get_db),
):
    """Return a structured inspection report with all data for display."""
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == insp.order_item_id).first()
    photos = db.query(GarmentPhoto).filter(GarmentPhoto.order_item_id == insp.order_item_id).order_by(GarmentPhoto.created_at).all()

    return {
        "inspection": insp.to_dict(),
        "garment": item.to_dict() if item else None,
        "photos": [p.to_dict() for p in photos],
        "issues": [i.to_dict() for i in insp.issues],
        "ai_results": [r.raw_result for r in insp.ai_results],
        "inspector": insp.inspector.to_dict() if insp.inspector else None,
    }
