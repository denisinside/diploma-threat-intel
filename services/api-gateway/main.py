from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.config import settings
from database.mongo import init_mongodb
from database.elastic import init_elasticsearch, close_elasticsearch

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

@app.get("/")
async def hello_world():
    return {"message": "Hello World"}