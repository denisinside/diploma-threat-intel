from __future__ import annotations

from typing import Any, Iterable

from elasticsearch import AsyncElasticsearch


def parse_hosts(hosts: str) -> list[str]:
    """Parse and normalize Elasticsearch hosts, adding http:// if scheme is missing."""
    raw = [h.strip() for h in hosts.split(",") if h.strip()]
    result = []
    for h in raw:
        if not h.startswith(("http://", "https://")):
            h = f"http://{h}"
        result.append(h)
    return result


def init_elasticsearch(hosts: str) -> AsyncElasticsearch:
    return AsyncElasticsearch(hosts=parse_hosts(hosts))


async def close_elasticsearch(client: AsyncElasticsearch) -> None:
    await client.close()


async def index_document(
    client: AsyncElasticsearch,
    index_name: str,
    document: dict[str, Any],
    document_id: str | None = None,
) -> dict[str, Any]:
    response = await client.index(index=index_name, id=document_id, document=document)
    return response


async def get_document(
    client: AsyncElasticsearch,
    index_name: str,
    document_id: str,
) -> dict[str, Any]:
    response = await client.get(index=index_name, id=document_id)
    return response


async def search_documents(
    client: AsyncElasticsearch,
    index_name: str,
    query: dict[str, Any],
    size: int = 10,
    from_: int = 0,
) -> Iterable[dict[str, Any]]:
    """Search documents, returns raw ES hits (with _id, _source, etc.)"""
    response = await client.search(index=index_name, query=query, size=size, from_=from_)
    return response.get("hits", {}).get("hits", [])


async def search_sources(
    client: AsyncElasticsearch,
    index_name: str,
    query: dict[str, Any],
    size: int = 10,
    from_: int = 0,
) -> list[dict[str, Any]]:
    """Search documents and return only the _source of each hit"""
    hits = await search_documents(client, index_name, query, size, from_)
    return [hit["_source"] for hit in hits]


async def search_with_total(
    client: AsyncElasticsearch,
    index_name: str,
    query: dict[str, Any],
    size: int = 10,
    from_: int = 0,
    sort: list[dict[str, Any]] | None = None,
    track_total_hits: bool | int = True,
) -> tuple[list[dict[str, Any]], int]:
    """Search and return (sources, total_count). track_total_hits=True for accurate count beyond 10k."""
    body: dict[str, Any] = {"query": query, "size": size, "from": from_, "track_total_hits": track_total_hits}
    if sort:
        body["sort"] = sort
    response = await client.search(index=index_name, body=body)
    hits = response.get("hits", {})
    total = hits.get("total", 0)
    if isinstance(total, dict):
        total = total.get("value", 0)
    sources = [h["_source"] for h in hits.get("hits", [])]
    return sources, total


async def search_with_aggregations(
    client: AsyncElasticsearch,
    index_name: str,
    query: dict[str, Any],
    aggregations: dict[str, Any],
    size: int = 0,
) -> dict[str, Any]:
    """Run search with aggregations, return aggregation results"""
    body: dict[str, Any] = {"query": query, "size": size, "aggs": aggregations}
    response = await client.search(index=index_name, body=body)
    return response.get("aggregations", {})


async def multi_match_search(
    client: AsyncElasticsearch,
    index_name: str,
    query_text: str,
    fields: list[str],
    size: int = 50,
    from_: int = 0,
    fuzziness: str = "AUTO",
) -> list[dict[str, Any]]:
    """Full-text search across multiple fields with fuzziness"""
    query = {
        "multi_match": {
            "query": query_text,
            "fields": fields,
            "type": "best_fields",
            "fuzziness": fuzziness,
        }
    }
    return await search_sources(client, index_name, query, size, from_)


async def term_search(
    client: AsyncElasticsearch,
    index_name: str,
    field: str,
    value: str,
    size: int = 50,
    from_: int = 0,
) -> list[dict[str, Any]]:
    """Exact match search on a keyword field"""
    query = {"term": {field: value}}
    return await search_sources(client, index_name, query, size, from_)


async def wildcard_search(
    client: AsyncElasticsearch,
    index_name: str,
    field: str,
    pattern: str,
    size: int = 50,
    from_: int = 0,
) -> list[dict[str, Any]]:
    """Wildcard pattern search (e.g. *@company.com)"""
    query = {"wildcard": {field: {"value": pattern, "case_insensitive": True}}}
    return await search_sources(client, index_name, query, size, from_)
