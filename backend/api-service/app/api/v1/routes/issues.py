from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.models.models import AppUser, InspectionIssue

router = APIRouter()


class IssueUpdate(BaseModel):
    issue_type: str | None = None
    severity_level: int | None = None
    position_desc: str | None = None


@router.put("/{issue_id}")
def update_issue(issue_id: str, payload: IssueUpdate, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    issue = db.query(InspectionIssue).filter(InspectionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if payload.issue_type is not None:
        issue.issue_type = payload.issue_type
    if payload.severity_level is not None:
        issue.severity_level = payload.severity_level
    if payload.position_desc is not None:
        issue.position_desc = payload.position_desc
    db.commit()
    db.refresh(issue)
    return issue.to_dict()


@router.delete("/{issue_id}")
def delete_issue(issue_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    issue = db.query(InspectionIssue).filter(InspectionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    db.delete(issue)
    db.commit()
    return {"ok": True}
