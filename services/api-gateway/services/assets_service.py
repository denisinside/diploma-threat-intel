import repositories.assets_repo as assets_repo
from models.requests.assets_requests import CreateAssetRequest, UpdateAssetRequest
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime, timezone


async def create_asset(db: AsyncIOMotorDatabase, request: CreateAssetRequest) -> dict:
    asset_data = request.model_dump()
    asset_data["is_active"] = True
    asset_data["created_at"] = datetime.now(timezone.utc)
    asset_data["updated_at"] = datetime.now(timezone.utc)
    return await assets_repo.create_asset(db, asset_data)


async def get_asset(db: AsyncIOMotorDatabase, asset_id: str) -> dict:
    asset = await assets_repo.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


async def get_company_assets(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await assets_repo.get_assets_by_company(db, company_id, skip=skip, limit=limit)


async def update_asset(
    db: AsyncIOMotorDatabase, asset_id: str, request: UpdateAssetRequest,
) -> dict:
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc)
    asset = await assets_repo.update_asset(db, asset_id, update_data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


async def delete_asset(db: AsyncIOMotorDatabase, asset_id: str) -> bool:
    deleted = await assets_repo.delete_asset(db, asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    return True
