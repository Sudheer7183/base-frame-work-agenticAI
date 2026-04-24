


from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role, Role, TokenData,get_admin_user
from app.models.hitl import HITLRecord
from app.schemas.hitl import HITLRecordResponse
from app.core.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/hitl", tags=["HITL"])


@router.get("/pending", response_model=List[HITLRecordResponse])
async def list_pending_hitl(
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_admin_user),
):
    records = db.query(HITLRecord).filter_by(status="pending").all()
    return [HITLRecordResponse(**r.to_dict()) for r in records]
