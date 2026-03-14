from fastapi import APIRouter, Request, Depends
from api.v1.dependencies import require_super_admin, PaginationParams
import services.company_registration_service as reg_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/company-requests")
async def list_company_requests(
    request: Request,
    _user=Depends(require_super_admin),
    pg: PaginationParams = Depends(PaginationParams),
):
    """List pending company registration requests (super_admin only)"""
    db = request.app.mongodb
    return await reg_service.get_pending_requests(db, skip=pg.skip, limit=pg.limit or 100)


@router.post("/company-requests/{request_id}/approve")
async def approve_company_request(
    request_id: str,
    request: Request,
    _user=Depends(require_super_admin),
):
    """Approve a company registration request (super_admin only)"""
    db = request.app.mongodb
    return await reg_service.approve_request(db, request_id)


@router.post("/company-requests/{request_id}/reject")
async def reject_company_request(
    request_id: str,
    request: Request,
    _user=Depends(require_super_admin),
):
    """Reject a company registration request (super_admin only)"""
    db = request.app.mongodb
    return await reg_service.reject_request(db, request_id)
