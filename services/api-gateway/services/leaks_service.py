import repositories.leaks_repo as leaks_repo
import repositories.companies_repo as companies_repo
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException
from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone
from elastic_transport import ConnectionTimeout
from urllib.parse import urlparse
from pathlib import Path
import re
from typing import TYPE_CHECKING
from loguru import logger

from shared.models.notification_event import (
    NotificationEvent,
    NotificationEventType,
    NotificationSeverity,
)

if TYPE_CHECKING:
    from messaging.rabbitmq import RabbitMQPublisher


# --- Leak Sources (MongoDB) ---

async def create_source(db: AsyncIOMotorDatabase, source_data: dict) -> dict:
    source_data["created_at"] = datetime.now(timezone.utc)
    source_data["updated_at"] = datetime.now(timezone.utc)
    return await leaks_repo.create_source(db, source_data)


async def create_telegram_source(
    db: AsyncIOMotorDatabase,
    data: dict,
    rabbitmq_publisher: "RabbitMQPublisher | None" = None,
) -> dict:
    """
    Create leak source from Telegram scraper. Checks sha256 for deduplication.
    Raises HTTPException 409 if duplicate.
    """
    sha256 = data.get("sha256")
    if not sha256:
        raise HTTPException(status_code=400, detail="sha256 is required")

    existing = await leaks_repo.find_source_by_sha256(db, sha256)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Duplicate: leak source with this sha256 already exists",
            headers={"X-Existing-Source-Id": str(existing.get("_id", ""))},
        )

    name = data.get("name") or f"combo_{data.get('channel_id', '')}_{data.get('message_id', '')}"
    origin_url = f"tg://channel/{data.get('channel_id', '').lstrip('-')}?msg={data.get('message_id', '')}"

    source_data = {
        "name": name,
        "source_type": "telegram",
        "origin_url": origin_url,
        "size_bytes": data.get("size_bytes"),
        "sha256": sha256,
        "status": "pending",
        "metadata": {
            "channel_id": data.get("channel_id"),
            "message_id": data.get("message_id"),
            "filename": data.get("filename"),
            "downloaded_at": data.get("downloaded_at"),
            "source": data.get("source", "attachment"),
            "original_url": data.get("original_url"),
            "password": data.get("password"),
            "local_path": data.get("local_path"),
        },
    }
    created = await create_source(db, source_data)

    if rabbitmq_publisher:
        event = NotificationEvent(
            event_type=NotificationEventType.LEAK_SOURCE_REGISTERED,
            source="api-gateway",
            severity=NotificationSeverity.MEDIUM,
            data={
                "source_id": created.get("_id"),
                "name": created.get("name"),
                "origin_url": created.get("origin_url"),
                "source_type": created.get("source_type"),
                "sha256": created.get("sha256"),
                "metadata": created.get("metadata", {}),
            },
        )
        try:
            await rabbitmq_publisher.publish_event(event)
        except Exception as exc:
            # Source creation should not fail if event publishing is temporarily unavailable.
            logger.warning(f"Failed to publish leak.source.registered event: {exc}")

    return created


async def get_source(db: AsyncIOMotorDatabase, source_id: str) -> dict:
    source = await leaks_repo.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Leak source not found")
    return source


async def get_source_by_sha256(db: AsyncIOMotorDatabase, sha256: str) -> Optional[dict]:
    """Get leak source by SHA-256 hash (for deduplication check)"""
    return await leaks_repo.find_source_by_sha256(db, sha256)


async def get_all_sources(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await leaks_repo.get_all_sources(db, skip=skip, limit=limit)


async def delete_source(db: AsyncIOMotorDatabase, source_id: str) -> bool:
    deleted = await leaks_repo.delete_source(db, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Leak source not found")
    return True


# --- Leak Records search (Elasticsearch) ---

async def search_by_domain(
    es: AsyncElasticsearch, domain: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Find all leaked credentials for a specific domain"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_by_domain(es, domain, size=es_size, from_=skip)


async def search_by_email(
    es: AsyncElasticsearch, email: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Check if a specific email was found in leaks"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_by_email(es, email, size=es_size, from_=skip)


async def search_fulltext(
    es: AsyncElasticsearch, query_text: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """General full-text search across leak records"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_fulltext(es, query_text, size=es_size, from_=skip)


async def search_by_email_pattern(
    es: AsyncElasticsearch, pattern: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Wildcard search for emails (e.g. '*@company.com')"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_by_email_pattern(es, pattern, size=es_size, from_=skip)


def _mask_password(password: Optional[str]) -> Optional[str]:
    if not password:
        return password
    if len(password) <= 2:
        return "*" * len(password)
    return f"{password[0]}{'*' * (len(password) - 2)}{password[-1]}"


def _load_country_codes() -> set[str]:
    file_path = Path(__file__).resolve().parent.parent / "core" / "country_codes.txt"
    if not file_path.exists():
        return set()
    values = set()
    for line in file_path.read_text(encoding="utf-8").splitlines():
        code = line.strip().upper()
        if code and len(code) == 2 and code.isalpha():
            values.add(code)
    return values


COUNTRY_CODES = _load_country_codes()
PATH_COUNTRY_RE = re.compile(r"^/[a-zA-Z]{2}(/|$)")


def _extract_country_from_host(host: str) -> Optional[str]:
    """Extract country code from hostname (TLD or subdomain)."""
    if not host or not COUNTRY_CODES:
        return None
    labels = [label for label in host.strip().lower().split(".") if label]
    if not labels:
        return None
    # ccTLD at the end, e.g. gov.ua, autoklad.ua, domain.com.ua
    tld = labels[-1].upper()
    if tld in COUNTRY_CODES:
        return tld
    # Two-part TLD like co.uk, com.ua
    if len(labels) >= 2:
        second_tld = labels[-2].upper()
        if second_tld in COUNTRY_CODES:
            return second_tld
    # Subdomain/localization, e.g. ua.example.com
    for label in labels[:-1]:
        if label.upper() in COUNTRY_CODES:
            return label.upper()
    return None


def _extract_country_code(domain: Optional[str], url: Optional[str]) -> Optional[str]:
    parsed_url = None
    if url:
        try:
            parsed_url = urlparse(url if "://" in url else f"https://{url}")
        except Exception:
            parsed_url = None

    # Prefer URL hostname (actual site) over domain (often email provider like ukr.net)
    url_host = (parsed_url.hostname or "").strip().lower() if parsed_url else ""
    domain_host = (domain or "").strip().lower()

    for host in (url_host, domain_host):
        if host:
            code = _extract_country_from_host(host)
            if code:
                return code

    # URL path localization, e.g. domain.com/ua or domain.com/en/ua
    if parsed_url and parsed_url.path:
        path = parsed_url.path.strip()
        if PATH_COUNTRY_RE.match(path):
            code = path[1:3].upper()
            if code in COUNTRY_CODES:
                return code
        for segment in path.split("/")[:4]:
            if segment and segment.upper() in COUNTRY_CODES:
                return segment.upper()
    return None


def _iso_or_none(value: Any) -> Optional[str]:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


async def search_records_paged(
    db: AsyncIOMotorDatabase,
    es: AsyncElasticsearch,
    q: Optional[str] = None,
    domain: Optional[str] = None,
    email: Optional[str] = None,
    email_pattern: Optional[str] = None,
    size: int = 25,
    skip: int = 0,
) -> dict[str, Any]:
    query = leaks_repo.build_search_query(
        q=q,
        domain=domain,
        email=email,
        email_pattern=email_pattern,
    )
    records, total = await leaks_repo.search_records_with_total(es, query=query, size=size, from_=skip)

    source_ids: list[str] = []
    for record in records:
        for source_id in record.get("leak_source_ids", []):
            if isinstance(source_id, str) and source_id not in source_ids:
                source_ids.append(source_id)
    sources = await leaks_repo.get_sources_by_ids(db, source_ids)
    source_map = {source.get("_id"): source for source in sources}

    enriched_items: list[dict[str, Any]] = []
    for record in records:
        leak_source_ids = record.get("leak_source_ids") or []
        primary_source = source_map.get(leak_source_ids[0]) if leak_source_ids else None
        ref_file = None
        date = None
        if primary_source:
            ref_file = primary_source.get("name")
            date = _iso_or_none(primary_source.get("created_at"))

        enriched_items.append({
            **record,
            "password": _mask_password(record.get("password")),
            "country_code": _extract_country_code(record.get("domain"), record.get("url")),
            "ref_file": ref_file,
            "date": date,
        })

    return {
        "items": enriched_items,
        "total": total,
        "skip": skip,
        "limit": size,
    }


def _to_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _source_display_name(source: dict[str, Any]) -> str:
    metadata = source.get("metadata") or {}
    channel_id = metadata.get("channel_id")
    if channel_id:
        return f"Telegram {channel_id}"
    return source.get("name") or source.get("origin_url") or source.get("_id") or "unknown"


async def get_analytics(
    db: AsyncIOMotorDatabase,
    es: AsyncElasticsearch,
    q: Optional[str] = None,
    domain: Optional[str] = None,
    email: Optional[str] = None,
    email_pattern: Optional[str] = None,
    company_id: Optional[str] = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)
    since_30d = now - timedelta(days=30)

    filtered_query = leaks_repo.build_search_query(q=q, domain=domain, email=email, email_pattern=email_pattern)
    global_query = {"match_all": {}}
    has_filters = bool(q or domain or email or email_pattern)

    all_sources = await leaks_repo.get_all_sources(db, skip=0, limit=0)
    fallback_total_records = sum(_to_int(source.get("records_count")) for source in all_sources)

    try:
        total_records = await leaks_repo.count_records(es, global_query)
    except ConnectionTimeout:
        total_records = fallback_total_records
    new_leaks_24h = await leaks_repo.count_recent_sources(db, since_24h)
    new_leaks_7d = await leaks_repo.count_recent_sources(db, since_7d)
    monitored_sources = await leaks_repo.count_sources(db)
    try:
        critical_alerts = await leaks_repo.count_critical_alerts(
            es,
            global_query,
            include_weak_passwords=False,
        )
    except ConnectionTimeout:
        critical_alerts = 0

    source_distribution = []
    if has_filters:
        try:
            source_counts = await leaks_repo.aggregate_source_counts(es, filtered_query, size=500)
        except ConnectionTimeout:
            source_counts = []
        source_ids = [bucket.get("key") for bucket in source_counts if isinstance(bucket.get("key"), str)]
        sources = await leaks_repo.get_sources_by_ids(db, source_ids)
        source_map = {source["_id"]: source for source in sources}
        total_filtered_records = sum(int(bucket.get("doc_count", 0)) for bucket in source_counts)
        total_for_percentage = total_filtered_records if total_filtered_records > 0 else 1

        for bucket in source_counts[:10]:
            source_id = bucket.get("key")
            count = int(bucket.get("doc_count", 0))
            source_doc = source_map.get(source_id, {})
            source_distribution.append({
                "source_id": source_id,
                "label": _source_display_name(source_doc),
                "count": count,
                "percentage": round((count / total_for_percentage) * 100, 2),
            })
    else:
        sorted_sources = sorted(
            all_sources,
            key=lambda source: _to_int(source.get("records_count")),
            reverse=True,
        )
        total_global = sum(_to_int(source.get("records_count")) for source in sorted_sources)
        total_for_percentage = total_global if total_global > 0 else 1
        for source in sorted_sources[:10]:
            count = _to_int(source.get("records_count"))
            source_distribution.append({
                "source_id": source.get("_id", "unknown"),
                "label": _source_display_name(source),
                "count": count,
                "percentage": round((count / total_for_percentage) * 100, 2),
            })

    period_sources = await leaks_repo.get_sources_created_since(db, since_30d)
    period_source_ids = [source["_id"] for source in period_sources if source.get("_id")]
    daily_total_map: dict[str, int] = {}
    hourly_map: dict[tuple[int, int], int] = {}

    if has_filters and period_source_ids:
        filtered_source_buckets = await leaks_repo.aggregate_source_counts(es, filtered_query, size=5000)
        filtered_source_map = {bucket.get("key"): int(bucket.get("doc_count", 0)) for bucket in filtered_source_buckets}
        for source in period_sources:
            created_at = source.get("created_at")
            source_id = source.get("_id")
            if not isinstance(created_at, datetime) or not source_id:
                continue
            count = filtered_source_map.get(source_id, 0)
            day_key = created_at.date().isoformat()
            daily_total_map[day_key] = daily_total_map.get(day_key, 0) + count
            heat_key = (created_at.weekday(), created_at.hour)
            hourly_map[heat_key] = hourly_map.get(heat_key, 0) + count
    else:
        for source in period_sources:
            created_at = source.get("created_at")
            if not isinstance(created_at, datetime):
                continue
            count = _to_int(source.get("records_count"))
            day_key = created_at.date().isoformat()
            daily_total_map[day_key] = daily_total_map.get(day_key, 0) + count
            heat_key = (created_at.weekday(), created_at.hour)
            hourly_map[heat_key] = hourly_map.get(heat_key, 0) + count

    company_domain: Optional[str] = None
    if company_id:
        company = await companies_repo.get_company_by_id(db, company_id)
        if company:
            company_domain = company.get("domain")

    daily_company_map: dict[str, int] = {}
    if company_domain and period_source_ids:
        company_query = {
            "bool": {
                "must": [
                    filtered_query,
                    {"term": {"domain.keyword": company_domain}},
                ]
            }
        }
        company_source_buckets = await leaks_repo.aggregate_source_counts(es, company_query, size=5000)
        company_source_map = {bucket.get("key"): int(bucket.get("doc_count", 0)) for bucket in company_source_buckets}
        for source in period_sources:
            created_at = source.get("created_at")
            source_id = source.get("_id")
            if not isinstance(created_at, datetime) or not source_id:
                continue
            day_key = created_at.date().isoformat()
            daily_company_map[day_key] = daily_company_map.get(day_key, 0) + company_source_map.get(source_id, 0)

    trend = []
    for idx in range(30):
        day = (since_30d + timedelta(days=idx)).date().isoformat()
        trend.append({
            "date": day,
            "total": daily_total_map.get(day, 0),
            "company": daily_company_map.get(day, 0),
        })

    try:
        top_domain_buckets = await leaks_repo.aggregate_top_domains(es, filtered_query, size=10)
    except ConnectionTimeout:
        top_domain_buckets = []
    top_domains = [
        {"domain": bucket.get("key"), "count": int(bucket.get("doc_count", 0))}
        for bucket in top_domain_buckets
        if bucket.get("key")
    ]

    try:
        password_histogram_map = await leaks_repo.aggregate_password_histogram(es, filtered_query)
    except ConnectionTimeout:
        password_histogram_map = {"1-6": 0, "7-8": 0, "9-10": 0, "11-12": 0, "13-16": 0, "17+": 0}
    password_histogram = [
        {"bucket": bucket, "count": count}
        for bucket, count in password_histogram_map.items()
    ]

    heatmap = []
    for weekday in range(7):
        for hour in range(24):
            heatmap.append({
                "weekday": weekday,
                "hour": hour,
                "count": hourly_map.get((weekday, hour), 0),
            })

    return {
        "kpis": {
            "total_compromised_records": total_records,
            "new_leaks_24h": new_leaks_24h,
            "new_leaks_7d": new_leaks_7d,
            "monitored_sources": monitored_sources,
            "critical_alerts": critical_alerts,
        },
        "charts": {
            "source_distribution": source_distribution,
            "trend": trend,
            "password_histogram": password_histogram,
            "top_domains": top_domains,
            "heatmap": heatmap,
        },
        "meta": {
            "filtered": has_filters,
            "company_domain": company_domain,
        },
    }
