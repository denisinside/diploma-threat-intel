import repositories.assets_repo as assets_repo
import repositories.subscriptions_repo as subscriptions_repo
from models.requests.assets_requests import CreateAssetRequest, UpdateAssetRequest
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, UploadFile
from typing import List, Optional
from datetime import datetime, timezone
from models.enums import AssetType, SubscriptionType
from core.asset_import import detect_and_parse, SUPPORTED_EXTENSIONS


async def _ensure_asset_subscription(db: AsyncIOMotorDatabase, asset: dict) -> None:
    """Create subscription for asset: vuln for library/repo, leak for domain/ip."""
    asset_id = str(asset.get("_id", ""))
    company_id = asset.get("company_id")
    name = (asset.get("name") or "").strip()
    asset_type = asset.get("type")
    if not company_id or not name or len(name) < 2:
        return
    sub_type = (
        SubscriptionType.LEAK.value
        if asset_type in ("domain", "ip_address")
        else SubscriptionType.VULNERABILITY.value
    )
    min_severity = "low"
    sub_data = {
        "company_id": company_id,
        "sub_type": sub_type,
        "keyword": name,
        "min_severity": min_severity,
        "asset_id": asset_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await subscriptions_repo.create_subscription(db, sub_data)


async def create_asset(db: AsyncIOMotorDatabase, request: CreateAssetRequest) -> dict:
    asset_data = request.model_dump()
    asset_data["is_active"] = True
    asset_data["created_at"] = datetime.now(timezone.utc)
    asset_data["updated_at"] = datetime.now(timezone.utc)
    asset = await assets_repo.create_asset(db, asset_data)
    await _ensure_asset_subscription(db, asset)
    return asset


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
    if update_data.get("is_active") is False:
        await subscriptions_repo.delete_subscriptions_by_asset_id(db, asset_id)
    update_data["updated_at"] = datetime.now(timezone.utc)
    asset = await assets_repo.update_asset(db, asset_id, update_data)
    if asset and update_data.get("is_active") is True:
        await subscriptions_repo.delete_subscriptions_by_asset_id(db, asset_id)
        await _ensure_asset_subscription(db, asset)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


async def delete_asset(db: AsyncIOMotorDatabase, asset_id: str) -> bool:
    await subscriptions_repo.delete_subscriptions_by_asset_id(db, asset_id)
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
            asset = await assets_repo.create_asset(db, asset_data)
            await _ensure_asset_subscription(db, asset)
            created += 1
        except Exception as e:
            errors.append(f"{name}: {e!s}")
    return {
        "created": created,
        "skipped_duplicate": skipped_duplicate,
        "errors": errors[:20],
        "total_parsed": len(items),
    }
