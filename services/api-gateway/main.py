import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from database.mongo import init_mongodb, ensure_indexes
from core.config import settings
from core.security import hash_password
from database.elastic import init_elasticsearch, close_elasticsearch
from messaging.rabbitmq import RabbitMQPublisher
from api.v1.vulns_router import router as vulns_router
from api.v1.assets_router import router as assets_router
from api.v1.subscriptions_router import router as subscriptions_router
from api.v1.tickets_router import router as tickets_router
from api.v1.auth_router import router as auth_router
from api.v1.leaks_router import router as leaks_router
from api.v1.tasks_router import router as tasks_router
from api.v1.admin_router import router as admin_router
from api.v1.team_router import router as team_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client, app.mongodb = init_mongodb(
        settings.MONGODB_URI,
        settings.MONGODB_DB_NAME,
    )
    app.elasticsearch = init_elasticsearch(settings.ELASTICSEARCH_HOSTS)
    app.rabbitmq = RabbitMQPublisher(
        settings.RABBITMQ_URL,
        exchange_name=settings.RABBITMQ_NOTIFICATIONS_EXCHANGE,
    )
    await app.rabbitmq.connect()
    await ensure_indexes(app.mongodb)
    if settings.SUPER_ADMIN_EMAIL and settings.SUPER_ADMIN_PASSWORD:
        from datetime import datetime, timezone
        existing = await app.mongodb["users"].find_one({"email": settings.SUPER_ADMIN_EMAIL})
        if not existing:
            await app.mongodb["users"].insert_one({
                "email": settings.SUPER_ADMIN_EMAIL,
                "full_name": "Super Administrator",
                "password_hash": hash_password(settings.SUPER_ADMIN_PASSWORD),
                "company_id": None,
                "role": "super_admin",
                "last_login": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
    yield
    app.mongodb_client.close()
    await close_elasticsearch(app.elasticsearch)
    await app.rabbitmq.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(vulns_router)
app.include_router(leaks_router)
app.include_router(assets_router)
app.include_router(subscriptions_router)
app.include_router(tickets_router)
app.include_router(tasks_router)
app.include_router(admin_router)
app.include_router(team_router)


@app.get("/")
async def hello_world():
    return {"message": "Hello World"}