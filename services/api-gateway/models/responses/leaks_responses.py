from pydantic import BaseModel


class LeakKpisResponse(BaseModel):
    total_compromised_records: int
    new_leaks_24h: int
    new_leaks_7d: int
    monitored_sources: int
    critical_alerts: int


class LeakSourceDistributionItem(BaseModel):
    source_id: str
    label: str
    count: int
    percentage: float


class LeakTrendItem(BaseModel):
    date: str
    total: int
    company: int


class LeakPasswordHistogramItem(BaseModel):
    bucket: str
    count: int


class LeakTopDomainItem(BaseModel):
    domain: str
    count: int


class LeakHeatmapItem(BaseModel):
    weekday: int
    hour: int
    count: int


class LeakChartsResponse(BaseModel):
    source_distribution: list[LeakSourceDistributionItem]
    trend: list[LeakTrendItem]
    password_histogram: list[LeakPasswordHistogramItem]
    top_domains: list[LeakTopDomainItem]
    heatmap: list[LeakHeatmapItem]


class LeakAnalyticsMetaResponse(BaseModel):
    filtered: bool
    company_domain: str | None = None


class LeakAnalyticsResponse(BaseModel):
    kpis: LeakKpisResponse
    charts: LeakChartsResponse
    meta: LeakAnalyticsMetaResponse


class LeakSearchItemResponse(BaseModel):
    leak_source_ids: list[str] = []
    url: str | None = None
    domain: str | None = None
    email: str | None = None
    password: str | None = None
    leaktype: str | None = None
    country_code: str | None = None
    ref_file: str | None = None
    date: str | None = None
    tags: list[str] = []


class LeakSearchResponse(BaseModel):
    items: list[LeakSearchItemResponse]
    total: int
    skip: int
    limit: int
