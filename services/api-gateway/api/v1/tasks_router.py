from fastapi import APIRouter, Request, HTTPException
from models.responses.common import MessageResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/scan/trigger")
async def trigger_scan(request: Request) -> MessageResponse:
    """Trigger a manual CVE scan (via RabbitMQ message queue)"""
    # TODO: publish scan message to RabbitMQ when integration is ready
    # rabbitmq = request.app.rabbitmq
    # await rabbitmq.publish("cve_scan", {"mode": "watcher"})
    return MessageResponse(message="Scan triggered (stub - RabbitMQ integration pending)")


@router.get("/scan/status")
async def get_scan_status(request: Request) -> dict:
    """Get last scan status"""
    # TODO: read scan status from Redis when integration is ready
    # redis = request.app.redis
    # last_commit = await redis.get("last_processed_commit")
    return {
        "status": "unknown",
        "message": "Scan status tracking not yet integrated",
        "last_processed_commit": None,
    }
