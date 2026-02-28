"""
Static mapping for the leaks Elasticsearch index.
Explicit types reduce CPU during indexing (no dynamic mapping inference).
"""
from elasticsearch import Elasticsearch
from loguru import logger

LEAKS_MAPPING = {
    "mappings": {
        "dynamic": "false",
        "properties": {
            "email": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 512}},
            },
            "username": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 512}},
            },
            "password": {"type": "keyword", "ignore_above": 1024},
            "domain": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "url": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 2048}},
            },
            "leaktype": {"type": "keyword"},
            "leak_source_ids": {"type": "keyword"},
            "phone": {"type": "keyword", "ignore_above": 32},
            "tags": {"type": "keyword"},
        },
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "1s",
    },
}


def ensure_leaks_index_exists(es: Elasticsearch, index_name: str) -> None:
    """Create leaks index with static mapping if it does not exist."""
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=LEAKS_MAPPING)
        logger.info(f"Created index {index_name} with static mapping")
    else:
        logger.debug(f"Index {index_name} already exists")
