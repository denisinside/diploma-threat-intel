import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.config import settings
from database.mongo import init_mongodb
from database.elastic import init_elasticsearch, close_elasticsearch
from api.v1.vulns_router import router as vulns_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client, app.mongodb = init_mongodb(
        settings.MONGODB_URI,
        settings.MONGODB_DB_NAME,
    )
    app.elasticsearch = init_elasticsearch(settings.ELASTICSEARCH_HOSTS)
    yield
    app.mongodb_client.close()
    await close_elasticsearch(app.elasticsearch)

app = FastAPI(lifespan=lifespan)
app.include_router(vulns_router)


@app.get("/")
async def hello_world():
    return {"message": "Hello World"}