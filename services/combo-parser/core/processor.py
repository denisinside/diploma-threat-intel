"""
Main processing logic: read file/archive, parse combo lines, index to ES.
Handles: .txt, .csv, .zip, .7z, .rar
"""
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, List
from loguru import logger
from pymongo import MongoClient
from elasticsearch import Elasticsearch

from .parser import parse_text, parse_lines
from .archive import iter_zip_text_files, iter_7z_rar_text_files
from .indexer import bulk_index


def _parse_text_parallel(text: str, source_id: str, num_workers: int) -> List[dict]:
    """Parse text in parallel using ThreadPoolExecutor. Returns list of records."""
    lines = text.splitlines()
    if not lines:
        return []
    n = len(lines)
    chunk_size = max(1, math.ceil(n / num_workers))
    chunks = [
        lines[i : i + chunk_size]
        for i in range(0, n, chunk_size)
    ]
    records = []
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(parse_lines, chunk, source_id): i
            for i, chunk in enumerate(chunks)
        }
        for future in as_completed(futures):
            records.extend(future.result())
    return records


def _read_text_file(file_path: str) -> Optional[str]:
    """Read a plain text file with UTF-8 (replace errors)."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Cannot read {file_path}: {e}")
        return None


def process_source(
    source_id: str,
    local_path: str,
    password: Optional[str],
    es: Elasticsearch,
    es_index: str,
    mongo_db,
    safe_exts: set,
    dangerous_exts: set,
    max_archive_bytes: int,
    max_file_count: int,
    es_bulk_size: int,
    parse_workers: int = 0,
) -> int:
    """
    Process a single leak source file. Returns total indexed records.
    Updates status in MongoDB.
    """
    path = Path(local_path)
    if not path.exists():
        logger.error(f"File not found: {local_path}")
        _update_status(mongo_db, source_id, "error")
        return 0

    _update_status(mongo_db, source_id, "processing")
    ext = path.suffix.lstrip(".").lower()
    total_indexed = 0
    file_size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(f"Source {source_id}: starting {path.name} ({file_size_mb:.1f} MB)")

    try:
        if ext in ("txt", "csv", "log", "json"):
            logger.info(f"Source {source_id}: reading file...")
            text = _read_text_file(local_path)
            if text:
                logger.info(f"Source {source_id}: parsing {len(text):,} chars...")
                if parse_workers > 0:
                    logger.info(f"Source {source_id}: parallel parsing ({parse_workers} workers)")
                    records = _parse_text_parallel(text, source_id, parse_workers)
                else:
                    records = []
                    for i, record in enumerate(parse_text(text, source_id)):
                        records.append(record)
                        if (i + 1) % 1_000_000 == 0:
                            logger.info(f"Source {source_id}: parsed {len(records):,} records...")
                logger.info(f"Source {source_id}: parsed {len(records):,} records, indexing to ES...")
                if records:
                    total_indexed += bulk_index(es, es_index, records, es_bulk_size)

        elif ext == "zip":
            for filename, text in iter_zip_text_files(
                local_path, password=password,
                max_total_bytes=max_archive_bytes,
                max_file_count=max_file_count,
                safe_exts=safe_exts,
                dangerous_exts=dangerous_exts,
            ):
                records = (
                    _parse_text_parallel(text, source_id, parse_workers)
                    if parse_workers > 0
                    else list(parse_text(text, source_id))
                )
                if records:
                    logger.info(f"Source {source_id}: {filename} -> {len(records):,} records")
                    total_indexed += bulk_index(es, es_index, records, es_bulk_size)

        elif ext in ("7z", "rar"):
            for filename, text in iter_7z_rar_text_files(
                local_path, password=password,
                max_total_bytes=max_archive_bytes,
                max_file_count=max_file_count,
                safe_exts=safe_exts,
                dangerous_exts=dangerous_exts,
            ):
                records = (
                    _parse_text_parallel(text, source_id, parse_workers)
                    if parse_workers > 0
                    else list(parse_text(text, source_id))
                )
                if records:
                    logger.info(f"Source {source_id}: {filename} -> {len(records):,} records")
                    total_indexed += bulk_index(es, es_index, records, es_bulk_size)

        else:
            logger.warning(f"Unsupported file type: {ext}")
            _update_status(mongo_db, source_id, "error")
            return 0

        _update_status(mongo_db, source_id, "done", records_count=total_indexed)
        logger.info(f"Source {source_id}: indexed {total_indexed} records from {path.name}")

        try:
            path.unlink()
            logger.info(f"Deleted file after parsing: {local_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file {local_path}: {e}")

    except Exception as e:
        logger.error(f"Processing failed for {source_id}: {e}")
        _update_status(mongo_db, source_id, "error")
        raise  # Re-raise so consumer can nack+requeue (e.g. ES connection timeout)
    return total_indexed


def _update_status(mongo_db, source_id: str, status: str, records_count: int = None):
    """Update leak_source status in MongoDB."""
    from bson import ObjectId
    from datetime import datetime, timezone
    update = {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}}
    if records_count is not None:
        update["$set"]["records_count"] = records_count
    try:
        mongo_db["leak_sources"].update_one({"_id": ObjectId(source_id)}, update)
    except Exception as e:
        logger.warning(f"Failed to update status for {source_id}: {e}")
