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
) -> Iterable[dict[str, Any]]:
    response = await client.search(index=index_name, query=query, size=size)
    return response.get("hits", {}).get("hits", [])
