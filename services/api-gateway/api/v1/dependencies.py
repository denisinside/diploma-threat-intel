from fastapi import Query, Depends, HTTPException, Request


async def get_current_user(request: Request) -> dict:
    """Extract and validate JWT, return user payload from token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ")[1]
    from core.security import decode_token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


async def require_super_admin(request: Request) -> dict:
    """Require super_admin role."""
    user = await get_current_user(request)
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    return user


async def require_company_admin(request: Request) -> dict:
    """Require admin role with company_id."""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Company admin required")
    if not user.get("company_id"):
        raise HTTPException(status_code=403, detail="Company admin required")
    return user


async def require_admin_or_analyst(request: Request) -> dict:
    """Require admin or analyst role."""
    user = await get_current_user(request)
    if user.get("role") not in ("admin", "analyst", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin or analyst required")
    return user


class PaginationParams:
    """Reusable pagination query params for list endpoints"""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(0, ge=0, le=1000, description="Max items to return (0 = no limit)"),
    ):
        self.skip = skip
        self.limit = limit
