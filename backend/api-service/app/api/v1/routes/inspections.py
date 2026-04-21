import base64
import json
import logging
import os
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.storage import get_photo_bytes, save_photo
from app.db.database import get_db
from app.models.models import (
    AppUser,
    GarmentPhoto,
    InspectionAIResult,
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


def _prepare_image_content(file_path: str) -> dict | None:
    """Prepare an image for the OpenAI Vision API.
    Always use base64 encoding for reliability.
    If file_path is an HTTP(S) URL, download it first.
    """
    if file_path.startswith("http://") or file_path.startswith("https://"):
        try:
            import urllib.request
            with urllib.request.urlopen(file_path, timeout=15) as resp:
                img_bytes = resp.read()
        except Exception as e:
            logger.warning("Failed to download image from URL %s: %s", file_path, e)
            return None
    else:
        img_bytes = get_photo_bytes(file_path)
    if not img_bytes:
        return None
    img_data = base64.b64encode(img_bytes).decode()
    ext = os.path.splitext(file_path.split("?")[0])[-1].lower().lstrip(".")
    mime = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp", "bmp": "image/bmp",
    }.get(ext, "image/jpeg")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{img_data}", "detail": "high"},
    }


def _build_system_prompt() -> str:
    """Build the system prompt with expert knowledge for garment inspection."""
    return """You are a professional garment inspection assistant for a dry-cleaning business. Your task is to examine clothing item photos and identify visible problems that need attention before cleaning.

Look for these types of issues:
- Stains (food, drink, dirt, makeup, or other marks on the fabric)
- Fabric damage (tears, holes, fraying, or worn-through areas)
- Pilling or bobbling on fabric surface
- Missing buttons, broken zippers, or loose threads
- Fading or discoloration in specific areas
- Wrinkles or creases that need attention

For each issue you find, provide:
- issue_type: one of [stain, tear, hole, wear, wrinkle, fade, missing_button, zipper, pilling, other]
- severity_level: 1 (minor), 2 (moderate), or 3 (severe)
- position_desc: where on the garment (e.g. "front center", "left sleeve cuff", "collar")
- confidence_score: 0.0-1.0 (how confident you are this is a real issue)
- bbox_x, bbox_y, bbox_w, bbox_h: approximate bounding box (0.0-1.0 as fraction of image dimensions)

Important guidelines:
- Only report issues you can actually see in the photos
- Ignore shadows, intentional patterns, or normal fabric texture
- If the garment looks clean and undamaged, return an empty issues array
- You MUST respond with valid JSON only"""
def _build_stain_fallback_prompt(garment_desc: str, photo_desc: str, note: str) -> str:
    """Second pass prompt used when primary detection returns zero issues."""
    staff_note = f"\nStaff notes: {note}" if note else ""
    return f"""Look again carefully at this {garment_desc} for any stains or marks that may have been missed.

Photos: {photo_desc}{staff_note}

Check specifically for:
- Discoloration or marks on collar, cuffs, underarms
- Ring marks, splash marks, or irregular color patches
- Any localized area that looks different from surrounding fabric

Return JSON with only issue_type="stain" items that have confidence_score >= 0.40.
If you genuinely cannot see any stains, return an empty issues array.
"""


def ai_detect_openai(photo_file_paths: list[str], garment_type: str,
                      color: str = "", brand: str = "", note: str = "",
                      fabric_type: str = "", service_type: str = "",
                      photo_labels: list[str] | None = None) -> list[dict]:
    """Use GPT-4o Vision to detect garment defects with batch processing for large photo sets."""
    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    # Process in batches of 3 images max (OpenAI Vision API limit)
    # Too many images in one request causes token overflow
    BATCH_SIZE = 3
    all_issues = []
    
    # Load all valid images
    all_images = []
    for idx, file_path in enumerate(photo_file_paths[:12]):  # Max 12 photos total
        img_content = _prepare_image_content(file_path)
        if img_content is None:
            logger.debug("Skipping unloadable image: %s", file_path)
            continue
        label = (photo_labels[idx] if photo_labels and idx < len(photo_labels) else None) or f"photo_{idx + 1}"
        all_images.append((img_content, label, idx + 1))  # Store 1-based photo index
    
    if not all_images:
        logger.warning("No loadable images found for AI detection")
        return []
    
    logger.info("AI Detection: Processing %d images in batches of %d", len(all_images), BATCH_SIZE)

    # Build detailed garment description (used for all batches)
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
    
    # Process in batches
    for batch_idx in range(0, len(all_images), BATCH_SIZE):
        batch = all_images[batch_idx:batch_idx + BATCH_SIZE]
        images_content = [img for img, _, _ in batch]
        labels = [lbl for _, lbl, _ in batch]
        
        logger.info("Processing batch %d: %d images", batch_idx // BATCH_SIZE + 1, len(batch))
        
        photo_desc = ", ".join(f"Image {i+1}: {lbl}" for i, lbl in enumerate(labels))
        staff_note = f"\nStaff notes: {note}" if note else ""

        user_prompt = f"""Inspect this garment for pre-cleaning defect documentation.

Garment: {garment_desc}
Photos provided ({len(images_content)}): {photo_desc}{staff_note}

Primary objective for this run:
- Maximize detection quality for stains while still detecting non-stain defects.
- Use conservative severity, but do not miss visible stain candidates.

Execution protocol (follow in order):
Step A: For EACH photo, run a dense stain scan at 100% mental zoom over collar, underarm, chest, cuffs, hem, and any high-contact area.
Step B: Mark stain candidates first, then scan for tear/hole/wear/wrinkle/fade/pilling/hardware issues.
Step C: Cross-check each stain candidate against other photos; if uncertain, keep it with lower confidence (0.35-0.59) instead of dropping.
Step D: Remove only obvious lighting/shadow artifacts.

For each photo, perform a systematic inspection covering ALL of these areas (where applicable):
- Collar and neckline (stains from skin contact, fraying)
- Shoulders and upper back (dandruff marks, wear patterns)
- Chest area (food stains, button condition)
- Sleeves and cuffs (wear at edges, stains at wrists)
- Underarm areas (perspiration stains, yellowing)
- Back panel (sitting wear, unknown stains)
- Pockets (wear, sagging, loose threads)
- Hem and lower edges (dragging wear, mud marks)
- Zippers and closures (function, damage)
- Lining (if visible — tears, detachment)
- Seams (splitting, loose threads, puckering)

When multiple photos show the same garment from different angles, cross-reference your findings. If you see something suspicious in one photo, check if other photos confirm or clarify it.

Return ONLY valid JSON:
{{
  "issues": [
    {{
      "issue_type": "<type_code>",
      "severity_level": <1|2|3>,
      "position_desc": "<precise anatomical location on the garment>",
      "confidence_score": <0.0-1.0>,
      "bbox_x": <0.0-1.0>,
      "bbox_y": <0.0-1.0>,
      "bbox_w": <0.0-1.0>,
      "bbox_h": <0.0-1.0>,
      "photo_index": <1-based index of which photo shows this issue most clearly>
    }}
  ]
}}

Type codes: stain, tear, hole, wear, wrinkle, fade, missing_button, zipper, pilling, other
Severity: 1=minor (cosmetic only), 2=moderate (noticeable, needs treatment), 3=severe (significant damage/risk)
BBox: normalized coordinates in the specific photo indicated by photo_index (0,0=top-left, values 0.0-1.0). Use TIGHT bounding boxes around the actual defect.
Position: be anatomically specific — e.g. "left chest, 3cm below second button", "inner right collar seam near tag", "right sleeve cuff, outer edge".

Important for stain output quality:
- Prefer issue_type="stain" for visible local discoloration/residue even if stain type is unknown.
- Do not merge two spatially separate stains into one box.
- Small but visible stain spots are valid issues if confidence_score >= 0.35.
- If no convincing issues exist after Step D, return an empty issues array."""
        
        batch_issues = []
        last_err = None
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": _build_system_prompt()},
                        {"role": "user", "content": [{"type": "text", "text": user_prompt}, *images_content]},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=3000,
                    temperature=0.1,
                )

                raw_content = response.choices[0].message.content
                if not raw_content:
                    finish_reason = response.choices[0].finish_reason
                    refusal = getattr(response.choices[0].message, "refusal", None)
                    logger.warning("OpenAI empty content: finish_reason=%s refusal=%s", finish_reason, refusal)
                    raise ValueError(f"OpenAI returned empty content (finish_reason={finish_reason}, refusal={refusal})")
                result = json.loads(raw_content)
                batch_issues = result.get("issues", [])
                logger.info("Batch %d: Got %d issues from AI (attempt %d)", batch_idx // BATCH_SIZE + 1, len(batch_issues), attempt + 1)
                break  # Success, exit retry loop
                
            except Exception as retry_err:
                last_err = retry_err
                logger.warning("AI Detection batch %d attempt %d/3 failed: %s: %s", batch_idx // BATCH_SIZE + 1, attempt + 1, type(retry_err).__name__, retry_err)
                if attempt < 2:
                    time.sleep(2 ** attempt)
        
        if not batch_issues:
            logger.debug("Batch %d returned no issues, skipping fallback", batch_idx // BATCH_SIZE + 1)
            continue
            
        # Normalize and add batch issues
        for iss in batch_issues:
            itype = iss.get("issue_type", "other")
            if itype not in VALID_ISSUE_TYPES:
                itype = "other"

            # Validate bbox values are in range
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
            # Clamp bbox to image bounds
            if bbox_x is not None and bbox_w is not None and bbox_x + bbox_w > 1.0:
                bbox_w = 1.0 - bbox_x
            if bbox_y is not None and bbox_h is not None and bbox_y + bbox_h > 1.0:
                bbox_h = 1.0 - bbox_y

            all_issues.append({
                "issue_type": itype,
                "severity_level": min(3, max(1, int(iss.get("severity_level", 1)))),
                "position_desc": str(iss.get("position_desc", ""))[:200],
                "confidence_score": min(1.0, max(0.0, float(iss.get("confidence_score", 0.85)))),
                "bbox_x": bbox_x,
                "bbox_y": bbox_y,
                "bbox_w": bbox_w,
                "bbox_h": bbox_h,
            })
    
    # Deduplicate all collected issues
    if all_issues:
        deduplicated = _deduplicate_issues(all_issues)
        logger.info("AI Detection complete: %d issues found (after dedup: %d)", len(all_issues), len(deduplicated))
        return deduplicated
    
    logger.info("AI Detection complete: No issues found in any batch")
    return []


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


@router.post("/inspections/{inspection_id}/detect")
def trigger_detection(inspection_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    insp = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    # Get garment info and photos for AI
    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == insp.order_item_id).first()
    garment_type = item.garment_type if item else "garment"
    photos = list(item.photos) if item else []
    photo_paths = [p.file_path for p in photos]
    photo_labels = [p.photo_label or f"photo_{i+1}" for i, p in enumerate(photos)]

    # Remove old AI issues
    db.query(InspectionIssue).filter(
        InspectionIssue.inspection_id == inspection_id,
        InspectionIssue.source == "ai",
    ).delete()
    insp.status = InspectionStatus.DETECTING
    db.commit()

    # Run AI detection
    if not settings.OPENAI_API_KEY:
        insp.status = InspectionStatus.PENDING
        db.commit()
        raise HTTPException(status_code=503, detail="AI detection unavailable: OPENAI_API_KEY is not configured")

    try:
        ai_issues = ai_detect_openai(
            photo_paths, garment_type,
            color=item.color or "" if item else "",
            brand=item.brand or "" if item else "",
            note=item.note or "" if item else "",
            fabric_type=item.fabric_type or "" if item else "",
            service_type=item.service_type or "" if item else "",
            photo_labels=photo_labels,
        )
    except HTTPException:
        insp.status = InspectionStatus.PENDING
        db.commit()
        raise
    except Exception as e:
        insp.status = InspectionStatus.PENDING
        db.commit()
        raise HTTPException(status_code=500, detail=f"AI detection failed: {str(e)}")

    ai_result = InspectionAIResult(inspection_id=inspection_id, raw_result=json.dumps(ai_issues))
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
        )
        db.add(issue)
    insp.status = InspectionStatus.COMPLETED
    db.commit()
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
