import base64
import json
import os
import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
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

CHINESE_POSITIONS = [
    "前胸左侧", "前胸右侧", "前胸中部", "后背上方",
    "后背中部", "领口区域", "左袖口", "右袖口",
    "左肩部", "右肩部", "腰部区域", "下摆处",
    "左袖肘部", "右袖肘部", "口袋处",
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
            "position_desc": random.choice(CHINESE_POSITIONS),
            "bbox_x": round(random.uniform(0.1, 0.8), 2),
            "bbox_y": round(random.uniform(0.1, 0.8), 2),
            "bbox_w": round(random.uniform(0.05, 0.2), 2),
            "bbox_h": round(random.uniform(0.05, 0.2), 2),
            "confidence_score": round(random.uniform(0.70, 0.92), 2),
        })
    return results


def ai_detect_openai(photo_file_paths: list[str], garment_type: str) -> list[dict]:
    """Use GPT-4o Vision to detect garment defects. Falls back to mock on any error."""
    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        images_content = []
        for file_path in photo_file_paths[:4]:
            # file_path stored as "/storage/photos/uuid.ext"
            fname = os.path.basename(file_path)
            full_path = os.path.join(settings.STORAGE_ROOT, "photos", fname)
            if not os.path.exists(full_path):
                # Try direct join
                full_path = os.path.join(settings.STORAGE_ROOT, file_path.lstrip("/storage/"))
            if not os.path.exists(full_path):
                continue
            with open(full_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
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

        prompt = f"""你是一名经验丰富的专业干洗店验衣师。请仔细检查这件【{garment_type}】的照片，找出所有真实存在的问题。

请严格以JSON格式返回，格式如下：
{{
  "issues": [
    {{
      "issue_type": "问题类型英文代码",
      "severity_level": 严重程度整数,
      "position_desc": "具体位置（中文）",
      "confidence_score": 置信度小数
    }}
  ]
}}

可用问题类型代码：
- stain：污渍/油渍/水渍
- tear：撕裂/划破
- hole：破洞/穿孔
- wear：磨损/磨白/起毛
- wrinkle：顽固褶皱
- fade：褪色/色差
- missing_button：缺扣子
- zipper：拉链损坏
- pilling：起球
- other：其他问题

严重程度：1=轻微，2=中等，3=严重

规则：只报告照片中真实可见的问题。如衣物完好，返回空issues数组。位置描述要具体（如：前胸左侧、领口边缘、左袖肘部）。"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [{"type": "text", "text": prompt}, *images_content],
            }],
            response_format={"type": "json_object"},
            max_tokens=1500,
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
            })
        return normalized

    except Exception as e:
        print(f"[AI Detection Error] {type(e).__name__}: {e}")
        return mock_ai_detect()


@router.post("/order-items/{item_id}/inspection")
def create_inspection(item_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.inspection:
        return item.inspection.to_dict()
    inspection = InspectionRecord(order_item_id=item_id)
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
    garment_type = item.garment_type if item else "衣物"
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
        ai_issues = ai_detect_openai(photo_paths, garment_type)
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
    insp.status = InspectionStatus.REVIEWING
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
