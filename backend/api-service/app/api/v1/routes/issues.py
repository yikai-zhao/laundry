from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.models.models import AppUser, InspectionIssue, IssueEditHistory

router = APIRouter()


class IssueUpdate(BaseModel):
    issue_type: str | None = None
    severity_level: int | None = None
    position_desc: str | None = None


@router.put("/{issue_id}")
def update_issue(issue_id: str, payload: IssueUpdate, db: Session = Depends(get_db), user: AppUser = Depends(get_current_user)):
    issue = db.query(InspectionIssue).filter(InspectionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Record edit history
    changes = []
    if payload.issue_type is not None and payload.issue_type != issue.issue_type:
        changes.append(("issue_type", issue.issue_type, payload.issue_type))
        issue.issue_type = payload.issue_type
    if payload.severity_level is not None and payload.severity_level != issue.severity_level:
        changes.append(("severity_level", str(issue.severity_level), str(payload.severity_level)))
        issue.severity_level = payload.severity_level
    if payload.position_desc is not None and payload.position_desc != issue.position_desc:
        changes.append(("position_desc", issue.position_desc, payload.position_desc))
        issue.position_desc = payload.position_desc

    for field, old_val, new_val in changes:
        db.add(IssueEditHistory(
            issue_id=issue_id,
            field_changed=field,
            old_value=old_val,
            new_value=new_val,
            changed_by=user.username,
        ))

    db.commit()
    db.refresh(issue)
    return issue.to_dict()


@router.delete("/{issue_id}")
def delete_issue(issue_id: str, db: Session = Depends(get_db), user: AppUser = Depends(get_current_user)):
    issue = db.query(InspectionIssue).filter(InspectionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    # Record deletion in history
    db.add(IssueEditHistory(
        issue_id=issue_id,
        field_changed="deleted",
        old_value=issue.issue_type,
        new_value=None,
        changed_by=user.username,
    ))
    db.delete(issue)
    db.commit()
    return {"ok": True}
