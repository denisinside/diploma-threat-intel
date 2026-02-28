"""
Combo Parser - RabbitMQ consumer that processes leak files and indexes into Elasticsearch.
Consumes events from leak-scraper: {source_id, local_path, password?}
"""
import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

import pika
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from loguru import logger

from config.config import settings
from core.processor import process_source
from core.es_mapping import ensure_leaks_index_exists

QUEUE_NAME = "leak_sources_pending"


def _init_mongo():
    client = MongoClient(settings.MONGODB_URI)
    return client, client[settings.MONGODB_DB_NAME]


def _init_elasticsearch():
    hosts = [h.strip() for h in settings.ELASTICSEARCH_HOSTS.split(",") if h.strip()]
    hosts = [h if h.startswith("http") else f"http://{h}" for h in hosts]
    return Elasticsearch(
        hosts=hosts,
        request_timeout=settings.ES_REQUEST_TIMEOUT,
        retry_on_timeout=True,
    )


def _callback(ch, method, properties, body, es, mongo_db):
    """Process a single message from the queue."""
    try:
        message = json.loads(body)
        source_id = message.get("source_id")
        local_path = message.get("local_path")
        password = message.get("password")

        if not source_id or not local_path:
            logger.warning(f"Invalid message: {message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(f"Processing source {source_id}: {local_path}")

        process_source(
            source_id=source_id,
            local_path=local_path,
            password=password,
            es=es,
            es_index=settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
            mongo_db=mongo_db,
            safe_exts=settings.safe_text_extensions_set,
            dangerous_exts=settings.dangerous_extensions_set,
            max_archive_bytes=settings.MAX_ARCHIVE_SIZE_BYTES,
            max_file_count=settings.MAX_FILE_COUNT_IN_ARCHIVE,
            es_bulk_size=settings.ES_BULK_SIZE,
            parse_workers=settings.PARSE_WORKERS,
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    logger.info("Starting combo-parser consumer...")

    mongo_client, mongo_db = _init_mongo()
    es = _init_elasticsearch()

    try:
        es.info(request_timeout=30)
        logger.info(f"Elasticsearch connected: {settings.ELASTICSEARCH_HOSTS}")
        ensure_leaks_index_exists(es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS)
    except Exception as e:
        logger.error(f"Elasticsearch unreachable: {e}. Check ELASTICSEARCH_HOSTS and that ES is running.")
        raise

    params = pika.URLParameters(settings.RABBITMQ_URL)
    # Long heartbeat: processing 8M records can take 30-60+ min; default 60s would close the connection
    params.heartbeat = 10000
    params.blocked_connection_timeout = 10000
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    def on_message(ch, method, properties, body):
        _callback(ch, method, properties, body, es, mongo_db)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)

    logger.info("Waiting for messages. Press Ctrl+C to stop.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
        channel.stop_consuming()
    finally:
        try:
            connection.close()
        except Exception as e:
            logger.debug(f"Connection already closed: {e}")
        mongo_client.close()
        es.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal: {e}")
        sys.exit(1)
