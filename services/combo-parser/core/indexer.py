"""
Elasticsearch bulk indexing for leak records.
Bottleneck is ES itself (disk/CPU) — client-side changes have little effect.
"""
from typing import List
from elasticsearch import Elasticsearch
from loguru import logger

from .parser import _record_digest

LOG_PROGRESS_EVERY_BATCHES = 20


def bulk_index(
    es: Elasticsearch,
    index_name: str,
    records: List[dict],
    batch_size: int = 5000,
) -> int:
    """
    Bulk index leak records. Uses upsert: if record exists (same digest),
    appends source_id to leak_source_ids; otherwise creates new doc.
    """
    total = 0
    num_batches = (len(records) + batch_size - 1) // batch_size
    logger.info(f"ES bulk: {len(records):,} records in {num_batches} batches")

    try:
        if es.indices.exists(index=index_name):
            es.indices.put_settings(index=index_name, body={"index": {"refresh_interval": "-1"}})
    except Exception as e:
        logger.debug(f"Could not disable refresh_interval: {e}")

    try:
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            body = []
            for record in batch:
                doc_id = _record_digest(record)
                source_ids = record.get("leak_source_ids", [])
                if not source_ids:
                    continue
                source_id = source_ids[0]
                update_op = {"update": {"_index": index_name, "_id": doc_id}}
                script = {
                    "source": """
                        if (ctx._source.leak_source_ids.contains(params.source_id)) {
                            ctx.op = 'none';
                        } else {
                            ctx._source.leak_source_ids.add(params.source_id);
                        }
                    """,
                    "lang": "painless",
                    "params": {"source_id": source_id},
                }
                upsert = {k: v for k, v in record.items() if k != "leak_source_ids"}
                upsert["leak_source_ids"] = [source_id]
                body.append(update_op)
                body.append({"script": script, "upsert": upsert})

            if not body:
                continue

            resp = es.bulk(body=body, refresh=False)
            errors = resp.get("errors", False)
            if errors:
                for item in resp.get("items", []):
                    err = item.get("update", {}).get("error")
                    if err:
                        logger.warning(f"ES bulk error: {err}")
            total += len(batch)

            batch_num = (i // batch_size) + 1
            if batch_num % LOG_PROGRESS_EVERY_BATCHES == 0 or batch_num == num_batches:
                logger.info(f"ES bulk progress: {total:,} / {len(records):,} ({100 * total / len(records):.1f}%)")
    except Exception as e:
        logger.error(f"ES bulk index failed: {e}")
        raise
    finally:
        try:
            if es.indices.exists(index=index_name):
                es.indices.put_settings(index=index_name, body={"index": {"refresh_interval": "1s"}})
        except Exception as e:
            logger.debug(f"Could not restore refresh_interval: {e}")
    return total
