import json
import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.models.models import (
    AppUser,
    InspectionAIResult,
    InspectionIssue,
    InspectionRecord,
    InspectionStatus,
    LaundryOrderItem,
)

router = APIRouter()


def mock_ai_detect() -> list[dict]:
    issue_types = ["stain", "tear", "hole", "wear"]
    positions = [
        "front upper left", "front upper right", "front lower left", "front lower right",
        "front center", "back upper", "back center", "back lower",
        "collar area", "left sleeve", "right sleeve", "hem area", "cuff area",
    ]
    n = random.randint(1, 4)
    results = []
    for _ in range(n):
        results.append({
            "issue_type": random.choice(issue_types),
            "severity_level": random.randint(1, 3),
            "position_desc": random.choice(positions),
            "bbox_x": round(random.uniform(0.1, 0.8), 2),
            "bbox_y": round(random.uniform(0.1, 0.8), 2),
            "bbox_w": round(random.uniform(0.05, 0.2), 2),
            "bbox_h": round(random.uniform(0.05, 0.2), 2),
            "confidence_score": round(random.uniform(0.65, 0.99), 2),
        })
    return results


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
    # Remove old AI issues
    db.query(InspectionIssue).filter(
        InspectionIssue.inspection_id == inspection_id,
        InspectionIssue.source == "ai",
    ).delete()
    insp.status = InspectionStatus.DETECTING
    db.commit()
    ai_issues = mock_ai_detect()
    ai_result = InspectionAIResult(inspection_id=inspection_id, raw_result=json.dumps(ai_issues))
    db.add(ai_result)
    for ai_issue in ai_issues:
        issue = InspectionIssue(
            inspection_id=inspection_id,
            issue_type=ai_issue["issue_type"],
            severity_level=ai_issue["severity_level"],
            position_desc=ai_issue["position_desc"],
            bbox_x=ai_issue["bbox_x"],
            bbox_y=ai_issue["bbox_y"],
            bbox_w=ai_issue["bbox_w"],
            bbox_h=ai_issue["bbox_h"],
            confidence_score=ai_issue["confidence_score"],
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
