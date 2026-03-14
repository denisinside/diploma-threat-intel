from fastapi import APIRouter, Request, Depends, Query
from api.v1.dependencies import require_company_admin, PaginationParams
from models.requests.auth_requests import RegisterAnalystRequest
import services.team_service as team_service

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/users")
async def list_company_users(
    request: Request,
    user=Depends(require_company_admin),
    pg: PaginationParams = Depends(PaginationParams),
):
    """List users in the caller's company (company admin only)"""
    db = request.app.mongodb
    company_id = user["company_id"]
    return await team_service.get_company_users(db, company_id, skip=pg.skip, limit=pg.limit or 100)


@router.post("/analysts")
async def register_analyst(
    body: RegisterAnalystRequest,
    request: Request,
    user=Depends(require_company_admin),
):
    """Register a new analyst in the caller's company (company admin only)"""
    db = request.app.mongodb
    company_id = user["company_id"]
    return await team_service.register_analyst(db, company_id, body.model_dump())


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    user=Depends(require_company_admin),
):
    """Delete an analyst in the caller's company (company admin only)"""
    db = request.app.mongodb
    await team_service.delete_company_user(db, user_id, user["company_id"])
    return {"message": "User deleted"}
