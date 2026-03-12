from fastapi import APIRouter, Request, HTTPException, Query, Depends, UploadFile, File
from models.requests.assets_requests import CreateAssetRequest, UpdateAssetRequest
from models.responses.common import MessageResponse
import services.assets_service as assets_service
from api.v1.dependencies import PaginationParams
from typing import List

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/")
async def create_asset(body: CreateAssetRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await assets_service.create_asset(db, body)


@router.post("/import")
async def import_assets(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    file: UploadFile = File(..., description="Dependency file (package-lock, requirements.txt, etc.)"),
) -> dict:
    db = request.app.mongodb
    return await assets_service.import_assets_from_file(db, company_id, file)


@router.get("/")
async def get_company_assets(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await assets_service.get_company_assets(db, company_id, skip=pg.skip, limit=pg.limit)


@router.get("/{asset_id}")
async def get_asset(asset_id: str, request: Request) -> dict:
    db = request.app.mongodb
    return await assets_service.get_asset(db, asset_id)


@router.put("/{asset_id}")
async def update_asset(asset_id: str, body: UpdateAssetRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await assets_service.update_asset(db, asset_id, body)


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, request: Request) -> MessageResponse:
    db = request.app.mongodb
    await assets_service.delete_asset(db, asset_id)
    return MessageResponse(message="Asset deleted successfully")
