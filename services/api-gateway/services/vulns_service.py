import repositories.vulns_repo as vulns_repo
import repositories.assets_repo as assets_repo
import repositories.tickets_repo as tickets_repo
import database.elastic as elastic
from shared.models.OSVVulnerability import OSVVulnerability
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException
from typing import List, Optional, Any
from collections import defaultdict
from datetime import datetime, timezone
from copy import deepcopy
from core.config import settings

_STATS_CACHE_TTL_SECONDS = 45
_stats_cache: dict[str, tuple[datetime, dict[str, Any]]] = {}


def _cache_get(key: str) -> Optional[dict[str, Any]]:
    cached = _stats_cache.get(key)
    if not cached:
        return None
    created_at, payload = cached
    age = (datetime.now(timezone.utc) - created_at).total_seconds()
    if age > _STATS_CACHE_TTL_SECONDS:
        _stats_cache.pop(key, None)
        return None
    return deepcopy(payload)


def _cache_set(key: str, payload: dict[str, Any]) -> None:
    _stats_cache[key] = (datetime.now(timezone.utc), deepcopy(payload))


def _build_vuln_query(
    query_text: Optional[str] = None,
    ecosystem: Optional[str] = None,
    package: Optional[str] = None,
    cvss_min: Optional[float] = None,
    cvss_max: Optional[float] = None,
    published_from: Optional[str] = None,
    published_to: Optional[str] = None,
    cwe_id: Optional[str] = None,
    severity: Optional[str] = None,
) -> dict[str, Any]:
    """Build ES bool query from search filters"""
    must = []
    if query_text and query_text.strip():
        must.append({
            "multi_match": {
                "query": query_text.strip(),
                "fields": ["summary^3", "details", "id^2", "aliases^2"],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        })
    if ecosystem:
        must.append({
            "nested": {
                "path": "affected",
                "query": {"match": {"affected.package.ecosystem": ecosystem}},
            }
        })
    if package:
        must.append({
            "nested": {
                "path": "affected",
                "query": {"match": {"affected.package.name": package}},
            }
        })
    if cwe_id:
        must.append({
            "nested": {
                "path": "database_specific.cwe_ids",
                "query": {"term": {"database_specific.cwe_ids.id": cwe_id}},
            }
        })
    if severity:
        must.append({"term": {"database_specific.severity": severity.upper()}})

    # CVSS range (cvvs_3 typo from OSV model)
    cvss_range = {}
    if cvss_min is not None:
        cvss_range["gte"] = cvss_min
    if cvss_max is not None:
        cvss_range["lte"] = cvss_max
    if cvss_range:
        must.append({
            "range": {
                "database_specific.cvss_severities.cvvs_3.score": cvss_range
            }
        })

    # Published date range
    pub_range = {}
    if published_from:
        pub_range["gte"] = published_from
    if published_to:
        pub_range["lte"] = published_to
    if pub_range:
        must.append({"range": {"published": pub_range}})

    if not must:
        return {"match_all": {}}
    return {"bool": {"must": must}}


def _build_sort(sort_by: Optional[str], sort_order: str = "desc") -> Optional[list[dict]]:
    """Build ES sort clause"""
    if not sort_by:
        return None
    order = "desc" if sort_order.lower() == "desc" else "asc"
    field_map = {
        "published": "published",
        "modified": "modified",
        "cvss": "database_specific.cvss_severities.cvvs_3.score",
        "id": "id",
    }
    field = field_map.get(sort_by)
    if not field:
        return None
    return [{field: {"order": order, "missing": "_last"}}]


async def search_vulnerabilities_v2(
    es: AsyncElasticsearch,
    query_text: Optional[str] = None,
    ecosystem: Optional[str] = None,
    package: Optional[str] = None,
    cvss_min: Optional[float] = None,
    cvss_max: Optional[float] = None,
    published_from: Optional[str] = None,
    published_to: Optional[str] = None,
    cwe_id: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> dict[str, Any]:
    """Search vulnerabilities with filters, pagination, sorting. Returns {items, total}"""
    query = _build_vuln_query(
        query_text=query_text,
        ecosystem=ecosystem,
        package=package,
        cvss_min=cvss_min,
        cvss_max=cvss_max,
        published_from=published_from,
        published_to=published_to,
        cwe_id=cwe_id,
        severity=severity,
    )
    sort = _build_sort(sort_by, sort_order)
    # When no filters: use match_all to browse all vulnerabilities with pagination
    items, total = await elastic.search_with_total(
        es,
        settings.ELASTICSEARCH_INDEX_NAME_VULNERABILITIES,
        query,
        size=limit if limit > 0 else 100,
        from_=skip,
        sort=sort,
    )
    # #region agent log
    if items and total > 0:
        try:
            import json
            first = items[0]
            ds = first.get("database_specific", {})
            with open("debug-6e8087.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({"hypothesisId": "D", "location": "vulns_service.py:search_vulnerabilities_v2", "message": "ES search first item", "data": {"item_id": first.get("id"), "ds_keys": list(ds.keys()) if ds else [], "has_cvss": "cvss_severities" in (ds or {})}, "timestamp": __import__("time").time() * 1000}) + "\n")
        except Exception:
            pass
    # #endregion
    return {"items": items, "total": total}


def _extract_cve_id(vuln: dict[str, Any]) -> str:
    aliases = vuln.get("aliases") or []
    for alias in aliases:
        if isinstance(alias, str) and alias.upper().startswith("CVE-"):
            return alias
    return str(vuln.get("id", ""))


def _extract_cvss_score(vuln: dict[str, Any]) -> Optional[float]:
    dbs = vuln.get("database_specific") or {}
    cvss = dbs.get("cvss_severities") or {}
    score = (
        ((cvss.get("cvvs_3") or {}).get("score"))
        or ((cvss.get("cvvs_4") or {}).get("score"))
    )
    if isinstance(score, (int, float)):
        return float(score)

    severities = vuln.get("severity") or []
    for sev in severities:
        if not isinstance(sev, dict):
            continue
        if sev.get("type") in {"CVSS_V3", "CVSS_V4"}:
            raw_score = sev.get("score")
            if isinstance(raw_score, (int, float)):
                return float(raw_score)
            if isinstance(raw_score, str):
                try:
                    return float(raw_score.split("/")[0])
                except Exception:
                    return None
    return None


def _extract_epss(vuln: dict[str, Any]) -> Optional[float]:
    dbs = vuln.get("database_specific") or {}
    epss = (dbs.get("epss") or {}).get("percentage")
    if isinstance(epss, (int, float)):
        return float(epss)
    return None


def _extract_severity(vuln: dict[str, Any]) -> str:
    raw = (vuln.get("database_specific") or {}).get("severity")
    if not isinstance(raw, str):
        return "UNKNOWN"
    return raw.upper()


def _to_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            return None
    return None


def _age_bucket(days: int) -> str:
    if days <= 7:
        return "0-7"
    if days <= 30:
        return "8-30"
    if days <= 90:
        return "31-90"
    return "90+"


async def _build_company_vuln_dashboard(db: Any, company_id: Optional[str]) -> dict[str, Any]:
    empty = {
        "kpis": {
            "open_cves": 0,
            "critical_actionable": 0,
            "mttr_days": None,
            "mttr_delta_prev_month_days": None,
        },
        "charts": {
            "top_assets_open_cves": [],
            "aging_by_severity": [
                {"bucket": "0-7", "critical": 0, "high": 0, "moderate": 0, "low": 0},
                {"bucket": "8-30", "critical": 0, "high": 0, "moderate": 0, "low": 0},
                {"bucket": "31-90", "critical": 0, "high": 0, "moderate": 0, "low": 0},
                {"bucket": "90+", "critical": 0, "high": 0, "moderate": 0, "low": 0},
            ],
            "criticality_vs_exploitability": [],
        },
    }
    if not company_id:
        return empty
    cache_key = f"vuln_dashboard::{company_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    open_statuses = ["open", "in_progress"]
    resolved_statuses = ["resolved"]
    open_tickets = await tickets_repo.get_tickets_by_company_statuses(db, company_id, open_statuses)
    resolved_tickets = await tickets_repo.get_tickets_by_company_statuses(db, company_id, resolved_statuses)
    all_tickets = [*open_tickets, *resolved_tickets]
    if not all_tickets:
        return empty

    vulnerability_ids = sorted(
        {
            str(t.get("vulnerability_id"))
            for t in all_tickets
            if t.get("vulnerability_id")
        }
    )
    vulnerabilities = await vulns_repo.get_vulnerabilities_by_ticket_ids(db, vulnerability_ids)
    vuln_by_cve_id: dict[str, dict[str, Any]] = {}
    for vuln in vulnerabilities:
        cve_id = _extract_cve_id(vuln)
        if cve_id:
            vuln_by_cve_id[cve_id] = vuln
        raw_id = vuln.get("id")
        if isinstance(raw_id, str) and raw_id:
            vuln_by_cve_id[raw_id] = vuln

    company_assets = await assets_repo.get_assets_for_vuln_stats(db, company_id)
    asset_name_by_id: dict[str, str] = {}
    asset_version_by_id: dict[str, str] = {}
    for asset in company_assets:
        asset_id = asset.get("_id")
        if not asset_id:
            continue
        asset_id = str(asset_id)
        name = asset.get("name")
        if isinstance(name, str) and name:
            asset_name_by_id[asset_id] = name
        version = asset.get("version")
        if isinstance(version, str) and version:
            asset_version_by_id[asset_id] = version

    open_vuln_ids = {
        str(t.get("vulnerability_id"))
        for t in open_tickets
        if t.get("vulnerability_id")
    }
    open_cves = len(open_vuln_ids)

    critical_actionable = 0
    for vuln_id in open_vuln_ids:
        vuln = vuln_by_cve_id.get(vuln_id)
        if not vuln:
            continue
        score = _extract_cvss_score(vuln)
        if score is not None and score > 9.0:
            critical_actionable += 1

    now = datetime.now(timezone.utc)
    aging_map = {
        "0-7": {"critical": 0, "high": 0, "moderate": 0, "low": 0},
        "8-30": {"critical": 0, "high": 0, "moderate": 0, "low": 0},
        "31-90": {"critical": 0, "high": 0, "moderate": 0, "low": 0},
        "90+": {"critical": 0, "high": 0, "moderate": 0, "low": 0},
    }
    open_vuln_oldest_detected: dict[str, datetime] = {}
    for ticket in open_tickets:
        vuln_id_raw = ticket.get("vulnerability_id")
        if not vuln_id_raw:
            continue
        vuln_id = str(vuln_id_raw)
        detected_at = _to_datetime(ticket.get("detected_at")) or now
        prev = open_vuln_oldest_detected.get(vuln_id)
        if prev is None or detected_at < prev:
            open_vuln_oldest_detected[vuln_id] = detected_at

    for vuln_id, detected_at in open_vuln_oldest_detected.items():
        vuln = vuln_by_cve_id.get(vuln_id)
        if not vuln:
            continue
        sev = _extract_severity(vuln).lower()
        sev_key = sev if sev in {"critical", "high", "moderate", "low"} else "low"
        days_open = max(0, int((now - detected_at).total_seconds() // 86400))
        bucket = _age_bucket(days_open)
        aging_map[bucket][sev_key] += 1

    asset_vuln_sets: dict[str, set[str]] = defaultdict(set)
    for ticket in open_tickets:
        asset_id_raw = ticket.get("asset_id")
        vuln_id_raw = ticket.get("vulnerability_id")
        if not asset_id_raw or not vuln_id_raw:
            continue
        asset_id = str(asset_id_raw)
        vuln_id = str(vuln_id_raw)
        asset_name = asset_name_by_id.get(asset_id)
        vuln = vuln_by_cve_id.get(vuln_id)
        if not asset_name or not vuln:
            continue
        affected = vuln.get("affected") or []
        package_names = {
            ((a.get("package") or {}).get("name"))
            for a in affected
            if isinstance(a, dict)
        }
        normalized_asset_name = asset_name.strip().lower()
        normalized_packages = {
            p.strip().lower() for p in package_names if isinstance(p, str) and p
        }
        if normalized_asset_name in normalized_packages:
            label = asset_name
            version = asset_version_by_id.get(asset_id)
            if version:
                label = f"{asset_name} {version}"
            asset_vuln_sets[label].add(vuln_id)

    top_assets_open_cves = sorted(
        (
            {"asset": asset_label, "count": len(vuln_ids)}
            for asset_label, vuln_ids in asset_vuln_sets.items()
        ),
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    scatter_points = []
    for vuln_id in open_vuln_ids:
        vuln = vuln_by_cve_id.get(vuln_id)
        if not vuln:
            continue
        cvss = _extract_cvss_score(vuln)
        epss = _extract_epss(vuln)
        if cvss is None or epss is None:
            continue
        scatter_points.append({
            "id": vuln_id,
            "cvss": round(cvss, 2),
            "epss": round(epss, 6),
            "severity": _extract_severity(vuln),
        })

    mttr_values_current: list[float] = []
    mttr_values_prev: list[float] = []
    current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 1:
        prev_month_start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
    else:
        prev_month_start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)

    for ticket in resolved_tickets:
        detected = _to_datetime(ticket.get("detected_at"))
        resolved = _to_datetime(ticket.get("resolved_at"))
        if not detected or not resolved or resolved < detected:
            continue
        diff_days = (resolved - detected).total_seconds() / 86400
        if resolved >= current_month_start:
            mttr_values_current.append(diff_days)
        elif prev_month_start <= resolved < current_month_start:
            mttr_values_prev.append(diff_days)

    mttr_days: Optional[float] = None
    mttr_prev: Optional[float] = None
    if mttr_values_current:
        mttr_days = round(sum(mttr_values_current) / len(mttr_values_current), 1)
    if mttr_values_prev:
        mttr_prev = round(sum(mttr_values_prev) / len(mttr_values_prev), 1)

    mttr_delta: Optional[float] = None
    if mttr_days is not None and mttr_prev is not None:
        mttr_delta = round(mttr_days - mttr_prev, 1)

    payload = {
        "kpis": {
            "open_cves": open_cves,
            "critical_actionable": critical_actionable,
            "mttr_days": mttr_days,
            "mttr_delta_prev_month_days": mttr_delta,
        },
        "charts": {
            "top_assets_open_cves": top_assets_open_cves,
            "aging_by_severity": [
                {"bucket": "0-7", **aging_map["0-7"]},
                {"bucket": "8-30", **aging_map["8-30"]},
                {"bucket": "31-90", **aging_map["31-90"]},
                {"bucket": "90+", **aging_map["90+"]},
            ],
            "criticality_vs_exploitability": sorted(
                scatter_points, key=lambda x: (x["cvss"], x["epss"]), reverse=True
            )[:300],
        },
    }
    _cache_set(cache_key, payload)
    return payload


async def get_vuln_stats_from_mongo(
    db: Any, company_id: Optional[str] = None,
) -> dict[str, Any]:
    """Get stats from MongoDB (all vulnerabilities)"""
    cache_key = f"vuln_stats_mongo::{company_id or 'none'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    result = await vulns_repo.get_stats_aggregation(db)
    dashboard = await _build_company_vuln_dashboard(db, company_id)
    payload = {
        **result,
        "mongo_total": result.get("total"),
        "kpis": {
            "total_vulnerabilities": result.get("total", 0),
            **dashboard["kpis"],
        },
        "charts": dashboard["charts"],
    }
    _cache_set(cache_key, payload)
    return payload


async def get_vuln_stats(
    es: AsyncElasticsearch,
    db: Optional[Any] = None,
    company_id: Optional[str] = None,
    query_text: Optional[str] = None,
    ecosystem: Optional[str] = None,
    package: Optional[str] = None,
    cvss_min: Optional[float] = None,
    cvss_max: Optional[float] = None,
    published_from: Optional[str] = None,
    published_to: Optional[str] = None,
    cwe_id: Optional[str] = None,
    severity: Optional[str] = None,
) -> dict[str, Any]:
    """Get aggregated stats for vulnerabilities matching filters"""
    cache_key = (
        "vuln_stats_es::"
        f"{company_id or 'none'}::{query_text or ''}::{ecosystem or ''}::{package or ''}::"
        f"{cvss_min if cvss_min is not None else ''}::{cvss_max if cvss_max is not None else ''}::"
        f"{published_from or ''}::{published_to or ''}::{cwe_id or ''}::{severity or ''}"
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    query = _build_vuln_query(
        query_text=query_text,
        ecosystem=ecosystem,
        package=package,
        cvss_min=cvss_min,
        cvss_max=cvss_max,
        published_from=published_from,
        published_to=published_to,
        cwe_id=cwe_id,
        severity=severity,
    )

    aggs = {
        "severity_distribution": {
            "terms": {"field": "database_specific.severity", "size": 20}
        },
        "cvss_ranges": {
            "histogram": {
                "field": "database_specific.cvss_severities.cvvs_3.score",
                "interval": 1,
                "min_doc_count": 1,
            }
        },
        "by_year": {
            "date_histogram": {
                "field": "published",
                "calendar_interval": "year",
                "min_doc_count": 1,
            }
        },
        "total": {"value_count": {"field": "id"}},
    }

    agg_result = await elastic.search_with_aggregations(
        es,
        settings.ELASTICSEARCH_INDEX_NAME_VULNERABILITIES,
        query,
        aggs,
        size=0,
    )

    # Normalize severity, order: CRITICAL > HIGH > MODERATE > LOW (highest first)
    severity_order = ["CRITICAL", "HIGH", "MODERATE", "LOW"]
    severity_buckets = agg_result.get("severity_distribution", {}).get("buckets", [])
    severity_map = {b["key"]: b["doc_count"] for b in severity_buckets}
    severity_distribution = [
        {"name": s, "value": severity_map.get(s, 0)}
        for s in severity_order
        if severity_map.get(s, 0) > 0
    ]
    # Append any other severities not in our order
    for b in severity_buckets:
        if b["key"] not in severity_order:
            severity_distribution.append({"name": b["key"], "value": b["doc_count"]})

    # CVSS histogram to range buckets (0-1, 1-2, ..., 9+)
    cvss_buckets = agg_result.get("cvss_ranges", {}).get("buckets", [])
    cvss_map = {int(b["key"]): b["doc_count"] for b in cvss_buckets}
    cvss_distribution = [
        {"range": f"{i}-{i+1}", "value": cvss_map.get(i, 0)}
        for i in range(9)
    ] + [{"range": "9+", "value": sum(cvss_map.get(k, 0) for k in range(9, 20))}]

    # By year
    by_year_buckets = agg_result.get("by_year", {}).get("buckets", [])
    by_year = [{"year": b["key_as_string"][:4], "value": b["doc_count"]} for b in by_year_buckets]

    total_val = agg_result.get("total", {}).get("value", 0)

    mongo_total: Optional[int] = None
    if db is not None:
        mongo_total = await vulns_repo.count_all(db)

    dashboard = await _build_company_vuln_dashboard(db, company_id) if db is not None else {
        "kpis": {
            "open_cves": 0,
            "critical_actionable": 0,
            "mttr_days": None,
            "mttr_delta_prev_month_days": None,
        },
        "charts": {
            "top_assets_open_cves": [],
            "aging_by_severity": [],
            "criticality_vs_exploitability": [],
        },
    }

    payload = {
        "severity_distribution": severity_distribution,
        "cvss_distribution": cvss_distribution,
        "by_year": by_year,
        "total": total_val,
        "mongo_total": mongo_total,
        "kpis": {
            "total_vulnerabilities": mongo_total if mongo_total is not None else total_val,
            **dashboard["kpis"],
        },
        "charts": dashboard["charts"],
    }
    _cache_set(cache_key, payload)
    return payload


async def get_vuln_by_id(db: AsyncIOMotorDatabase, vuln_id: str) -> Optional[dict]:
    if vuln_id.upper().startswith("CVE-"):
        vuln = await vulns_repo.get_vulnerability_by_cve_id(db, vuln_id)
    elif vuln_id.upper().startswith("GHSA-"):
        vuln = await vulns_repo.get_vulnerability_by_ghsa_id(db, vuln_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid vulnerability ID (must start with CVE- or GHSA-)")
    # #region agent log
    if vuln:
        try:
            import json
            ds = vuln.get("database_specific") if isinstance(vuln, dict) else getattr(vuln, "database_specific", None)
            cvss_keys = list((ds or {}).keys()) if ds else []
            has_cvss = bool(ds and (ds.get("cvss_severities") or (isinstance(ds, dict) and ("cvvs_3" in str(ds) or "cvss" in str(ds)))))
            with open("debug-6e8087.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({"hypothesisId": "B", "location": "vulns_service.py:get_vuln_by_id", "message": "Vuln database_specific", "data": {"vuln_id": vuln_id, "ds_keys": cvss_keys, "has_cvss_severities": has_cvss, "cvss_severities_sample": str((ds or {}).get("cvss_severities", ""))[:200]}, "timestamp": __import__("time").time() * 1000}) + "\n")
        except Exception:
            pass
    # #endregion
    return vuln


async def get_ecosystems(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[str]:
    raw = await vulns_repo.get_ecosystems(db)
    filtered = [x for x in (raw or []) if x is not None]
    if limit > 0:
        return filtered[skip : skip + limit]
    return filtered[skip:] if skip > 0 else filtered


async def get_vulns_by_ecosystem(
    db: AsyncIOMotorDatabase, ecosystem: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await vulns_repo.get_vulnerabilities_by_ecosystem(db, ecosystem, skip=skip, limit=limit)


async def search_packages(
    db: AsyncIOMotorDatabase, prefix: str, limit: int = 20,
) -> List[dict]:
    """Search packages by prefix, sorted by vuln count"""
    return await vulns_repo.search_packages_by_prefix(db, prefix, limit)


async def get_ecosystem_packages(
    db: AsyncIOMotorDatabase, ecosystem: str, skip: int = 0, limit: int = 0,
) -> List[str]:
    raw = await vulns_repo.get_ecosystem_packages(db, ecosystem)
    filtered = [x for x in (raw or []) if x is not None]
    if limit > 0:
        return filtered[skip : skip + limit]
    return filtered[skip:] if skip > 0 else filtered


async def get_vulnerabilities_by_package(
    db: AsyncIOMotorDatabase, package: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await vulns_repo.get_vulnerabilities_by_package(db, package, skip=skip, limit=limit)


# --- Elasticsearch-based search (full-text, fuzzy matching) ---

async def search_vulnerabilities(
    es: AsyncElasticsearch, query_text: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Full-text search across vulnerability summary, details, aliases, id"""
    es_size = size if size > 0 else 10000
    return await elastic.multi_match_search(
        es,
        settings.ELASTICSEARCH_INDEX_NAME_VULNERABILITIES,
        query_text,
        fields=["summary^3", "details", "id^2", "aliases^2"],
        size=es_size,
        from_=skip,
    )
