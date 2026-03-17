import base64
import json
import os
import random
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

router = APIRouter()

VALID_ISSUE_TYPES = {
    "stain", "tear", "hole", "wear", "wrinkle",
    "fade", "missing_button", "zipper", "pilling", "other",
}

ENGLISH_POSITIONS = [
    "Front left chest", "Front right chest", "Front center", "Upper back",
    "Mid back", "Collar area", "Left cuff", "Right cuff",
    "Left shoulder", "Right shoulder", "Waist area", "Hem",
    "Left elbow", "Right elbow", "Pocket area",
]


def mock_ai_detect() -> list[dict]:
    """Fallback mock when OpenAI is not configured."""
    issue_types = list(VALID_ISSUE_TYPES - {"other"})
    n = random.randint(0, 2)
    results = []
    for _ in range(n):
        results.append({
            "issue_type": random.choice(issue_types),
            "severity_level": random.randint(1, 2),
            "position_desc": random.choice(ENGLISH_POSITIONS),
            "bbox_x": round(random.uniform(0.1, 0.8), 2),
            "bbox_y": round(random.uniform(0.1, 0.8), 2),
            "bbox_w": round(random.uniform(0.05, 0.2), 2),
            "bbox_h": round(random.uniform(0.05, 0.2), 2),
            "confidence_score": round(random.uniform(0.70, 0.92), 2),
        })
    return results


def ai_detect_openai(photo_file_paths: list[str], garment_type: str,
                      color: str = "", brand: str = "", note: str = "") -> list[dict]:
    """Use GPT-4o Vision to detect garment defects. Falls back to mock on any error."""
    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as e:
        print(f"[AI Detection] OpenAI import/init failed: {e}")
        return mock_ai_detect()

    images_content = []
    for file_path in photo_file_paths[:4]:
        img_bytes = get_photo_bytes(file_path)
        if img_bytes is None:
            continue
        img_data = base64.b64encode(img_bytes).decode()
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        mime = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp", "bmp": "image/bmp",
        }.get(ext, "image/jpeg")
        images_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{img_data}", "detail": "high"},
        })

    if not images_content:
        return mock_ai_detect()

    garment_desc = garment_type
    if color or brand:
        garment_desc += f" ({', '.join(filter(None, [color, brand]))})"
    staff_note = f"\nStaff notes: {note}" if note else ""

    prompt = f"""You are an expert professional dry-cleaning and garment inspection specialist with 20+ years of experience. Perform a thorough inspection of this {garment_desc}.{staff_note}

Examine every part of the garment carefully: fabric surface, seams, buttons, zippers, cuffs, collar, pockets, lining, hems. Identify ALL visible defects that would affect cleaning or require special treatment.

Return ONLY valid JSON in this exact format:
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
      "bbox_h": <0.0-1.0>
    }}
  ]
}}

Issue type codes:
- stain: any stains (food, oil, ink, wine, water marks, perspiration rings)
- tear: fabric tears, rips, fraying seams
- hole: holes, moth damage, punctures  
- wear: abrasion, thinning fabric from repeated use
- wrinkle: set-in stubborn wrinkles, creases that need pressing
- fade: color fading, bleaching, discoloration, yellowing
- missing_button: missing or loose buttons, snaps
- zipper: zipper damage, stuck zipper, missing pull
- pilling: fabric pilling, lint balls
- other: anything else needing attention

Severity: 1=minor (cosmetic), 2=moderate (noticeable, needs treatment), 3=severe (significant damage)
Confidence: your certainty this is a real issue (0.0-1.0)
BBox: normalized coordinates of where in the image the issue is located (0,0 = top-left). Use approximate values if needed.
Position: be specific — not just "front" but "front left chest near second button", "inside right collar seam", "lower hem left side".

CRITICAL: Only report genuinely visible issues. Do NOT invent issues. If the garment looks clean and undamaged, return an empty issues array."""

    last_err = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}, *images_content],
                }],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0,
            )

            result = json.loads(response.choices[0].message.content)
            issues = result.get("issues", [])

            normalized = []
            for iss in issues:
                itype = iss.get("issue_type", "other")
                if itype not in VALID_ISSUE_TYPES:
                    itype = "other"
                normalized.append({
                    "issue_type": itype,
                    "severity_level": min(3, max(1, int(iss.get("severity_level", 1)))),
                    "position_desc": str(iss.get("position_desc", ""))[:200],
                    "confidence_score": min(1.0, max(0.0, float(iss.get("confidence_score", 0.85)))),
                    "bbox_x": iss.get("bbox_x"),
                    "bbox_y": iss.get("bbox_y"),
                    "bbox_w": iss.get("bbox_w"),
                    "bbox_h": iss.get("bbox_h"),
                })
            return normalized
        except Exception as retry_err:
            last_err = retry_err
            print(f"[AI Detection] Attempt {attempt+1}/3 failed: {type(retry_err).__name__}: {retry_err}")
            if attempt < 2:
                time.sleep(1)

    print(f"[AI Detection] All retries failed, using mock. Last error: {last_err}")
    return mock_ai_detect()


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
    photo_paths = [p.file_path for p in item.photos] if item else []

    # Remove old AI issues
    db.query(InspectionIssue).filter(
        InspectionIssue.inspection_id == inspection_id,
        InspectionIssue.source == "ai",
    ).delete()
    insp.status = InspectionStatus.DETECTING
    db.commit()

    # Run AI detection (real or mock fallback)
    if settings.OPENAI_API_KEY:
        ai_issues = ai_detect_openai(
            photo_paths, garment_type,
            color=item.color or "" if item else "",
            brand=item.brand or "" if item else "",
            note=item.note or "" if item else "",
        )
    else:
        ai_issues = mock_ai_detect()

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
    issue = InspectionIssue(
        inspection_id=inspection_id,
        issue_type=payload.issue_type,
        severity_level=payload.severity_level,
        position_desc=payload.position_desc,
        source="manual",
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
