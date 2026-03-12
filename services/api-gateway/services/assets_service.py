import repositories.assets_repo as assets_repo
from models.requests.assets_requests import CreateAssetRequest, UpdateAssetRequest
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, UploadFile
from typing import List, Optional
from datetime import datetime, timezone
from models.enums import AssetType
from core.asset_import import detect_and_parse, SUPPORTED_EXTENSIONS


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


async def import_assets_from_file(
    db: AsyncIOMotorDatabase, company_id: str, file: UploadFile,
) -> dict:
    """
    Parse dependency file and create assets for libraries. Skips duplicates.
    Returns {created, skipped, skipped_duplicate, errors}.
    """
    filename = file.filename or "unknown"
    if not any(ext in filename.lower() for ext in SUPPORTED_EXTENSIONS):
        ext_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file. Supported: {ext_list}",
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    items = detect_and_parse(content, filename)
    if not items:
        raise HTTPException(status_code=400, detail="No packages found in file or format not recognized")
    created = 0
    skipped_duplicate = 0
    errors: list[str] = []
    now = datetime.now(timezone.utc)
    for item in items:
        name = (item.get("name") or "").strip()
        if not name or len(name) > 200:
            continue
        version = (item.get("version") or "").strip() or None
        source_file = (item.get("source_file") or filename).strip() or filename
        existing = await assets_repo.find_asset_by_company_name_type(
            db, company_id, name, AssetType.SOFTWARE_LIB.value,
        )
        if existing:
            skipped_duplicate += 1
            continue
        try:
            asset_data = {
                "company_id": company_id,
                "name": name,
                "version": version,
                "type": AssetType.SOFTWARE_LIB.value,
                "is_active": True,
                "source_file": source_file,
                "created_at": now,
                "updated_at": now,
            }
            await assets_repo.create_asset(db, asset_data)
            created += 1
        except Exception as e:
            errors.append(f"{name}: {e!s}")
    return {
        "created": created,
        "skipped_duplicate": skipped_duplicate,
        "errors": errors[:20],
        "total_parsed": len(items),
    }
