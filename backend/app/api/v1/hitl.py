# """Human-in-the-Loop (HITL) API endpoints"""

# from typing import List, Optional
# from datetime import datetime
# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.orm import Session
# from pydantic import BaseModel

# from app.core.database import get_db
# from app.core.security import get_current_user, TokenData
# from app.core.exceptions import NotFoundException, BadRequestException
# from app.models.hitl import HITLRecord
# from app.schemas.hitl import HITLRecordResponse, HITLApproval, HITLRejection

# router = APIRouter(prefix="/hitl", tags=["HITL"])


# @router.get("/pending", response_model=List[HITLRecordResponse])
# async def list_pending_hitl(
#     priority: Optional[str] = Query(None),
#     agent_id: Optional[int] = Query(None),
#     limit: int = Query(50, le=200),
#     offset: int = Query(0, ge=0),
#     db: Session = Depends(get_db),
#     current_user: TokenData = Depends(get_current_user)
# ):
#     """
#     List all pending HITL records
    
#     - **priority**: Filter by priority (low, normal, high, urgent)
#     - **agent_id**: Filter by agent
#     """
#     query = db.query(HITLRecord).filter(HITLRecord.status == 'pending')
    
#     if priority:
#         query = query.filter(HITLRecord.priority == priority)
    
#     if agent_id:
#         query = query.filter(HITLRecord.agent_id == agent_id)
    
#     # Order by priority and creation time
#     priority_order = {
#         'urgent': 1,
#         'high': 2,
#         'normal': 3,
#         'low': 4
#     }
    
#     records = query.offset(offset).limit(limit).all()
    
#     return [HITLRecordResponse(**record.to_dict()) for record in records]


# @router.get("/{record_id}", response_model=HITLRecordResponse)
# async def get_hitl_record(
#     record_id: int,
#     db: Session = Depends(get_db),
#     current_user: TokenData = Depends(get_current_user)
# ):
#     """Get HITL record by ID"""
#     record = db.query(HITLRecord).filter(HITLRecord.id == record_id).first()
    
#     if not record:
#         raise NotFoundException(f"HITL record with ID {record_id} not found")
    
#     return HITLRecordResponse(**record.to_dict())


# @router.post("/{record_id}/approve", response_model=HITLRecordResponse)
# async def approve_hitl_record(
#     record_id: int,
#     approval: HITLApproval,
#     db: Session = Depends(get_db),
#     current_user: TokenData = Depends(get_current_user)
# ):
#     """
#     Approve a HITL record
    
#     Updates status to 'approved' and records feedback
#     """
#     record = db.query(HITLRecord).filter(HITLRecord.id == record_id).first()
    
#     if not record:
#         raise NotFoundException(f"HITL record with ID {record_id} not found")
    
#     if record.status != 'pending':
#         raise BadRequestException(f"Cannot approve record with status '{record.status}'")
    
#     # Update record
#     record.status = 'approved'
#     record.reviewed_by = current_user.sub if hasattr(current_user, 'sub') else None
#     record.reviewed_at = datetime.utcnow()
#     record.feedback = approval.feedback
    
#     if approval.modified_output:
#         record.output_data = approval.modified_output
    
#     db.commit()
#     db.refresh(record)
    
#     return HITLRecordResponse(**record.to_dict())


# @router.post("/{record_id}/reject", response_model=HITLRecordResponse)
# async def reject_hitl_record(
#     record_id: int,
#     rejection: HITLRejection,
#     db: Session = Depends(get_db),
#     current_user: TokenData = Depends(get_current_user)
# ):
#     """
#     Reject a HITL record
    
#     Updates status to 'rejected' and records reason
#     """
#     record = db.query(HITLRecord).filter(HITLRecord.id == record_id).first()
    
#     if not record:
#         raise NotFoundException(f"HITL record with ID {record_id} not found")
    
#     if record.status != 'pending':
#         raise BadRequestException(f"Cannot reject record with status '{record.status}'")
    
#     # Update record
#     record.status = 'rejected'
#     record.reviewed_by = current_user.sub if hasattr(current_user, 'sub') else None
#     record.reviewed_at = datetime.utcnow()
#     record.feedback = {"reason": rejection.reason, "details": rejection.details}
    
#     db.commit()
#     db.refresh(record)
    
#     return HITLRecordResponse(**record.to_dict())


# @router.post("/{record_id}/assign")
# async def assign_hitl_record(
#     record_id: int,
#     user_id: int,
#     db: Session = Depends(get_db),
#     current_user: TokenData = Depends(get_current_user)
# ):
#     """Assign HITL record to a user"""
#     record = db.query(HITLRecord).filter(HITLRecord.id == record_id).first()
    
#     if not record:
#         raise NotFoundException(f"HITL record with ID {record_id} not found")
    
#     record.assigned_to = user_id
#     db.commit()
    
#     return {"message": f"Record {record_id} assigned to user {user_id}"}


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
