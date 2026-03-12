/**
 * Shared types aligned with API models.
 */

export type AssetType = "domain" | "ip_address" | "repository" | "library";
export type TicketStatus = "open" | "in_progress" | "resolved" | "ignored" | "false_positive";
export type Severity = "critical" | "high" | "medium" | "low" | "unknown";
export type ChannelType = "email" | "telegram" | "slack" | "discord" | "webhook" | "signal";
export type SubscriptionType = "vulnerability" | "leak";

export interface Asset {
  _id: string;
  company_id: string;
  name: string;
  version?: string;
  type: AssetType;
  is_active: boolean;
  source_file?: string;
}

export interface LeakSource {
  _id: string;
  name: string;
  source_type: string;
  origin_url?: string;
  sha256?: string;
  status?: string;
  metadata?: Record<string, unknown>;
}

export interface LeakRecord {
  leak_source_ids?: string[];
  url?: string;
  domain?: string;
  email?: string;
  password?: string;
  leaktype?: string;
  country_code?: string;
  ref_file?: string;
  date?: string;
  tags?: string[];
}

export interface LeakSearchResponse {
  items: LeakRecord[];
  total: number;
  skip: number;
  limit: number;
}

export interface LeakKpis {
  total_compromised_records: number;
  new_leaks_24h: number;
  new_leaks_7d: number;
  monitored_sources: number;
  critical_alerts: number;
}

export interface LeakSourceDistributionItem {
  source_id: string;
  label: string;
  count: number;
  percentage: number;
}

export interface LeakTrendItem {
  date: string;
  total: number;
  company: number;
}

export interface LeakPasswordHistogramItem {
  bucket: string;
  count: number;
}

export interface LeakTopDomainItem {
  domain: string;
  count: number;
}

export interface LeakHeatmapItem {
  weekday: number;
  hour: number;
  count: number;
}

export interface LeakAnalytics {
  kpis: LeakKpis;
  charts: {
    source_distribution: LeakSourceDistributionItem[];
    trend: LeakTrendItem[];
    password_histogram: LeakPasswordHistogramItem[];
    top_domains: LeakTopDomainItem[];
    heatmap: LeakHeatmapItem[];
  };
  meta: {
    filtered: boolean;
    company_domain?: string | null;
  };
}

export interface Ticket {
  _id: string;
  company_id: string;
  asset_id: string;
  vulnerability_id: string;
  status: TicketStatus;
  priority: Severity;
  notes?: string;
  detected_at: string;
  resolved_at?: string;
}

export interface Subscription {
  _id: string;
  company_id: string;
  sub_type: SubscriptionType;
  keyword: string;
  min_severity: Severity;
}

export type EmailChannelConfig = { recipient_email: string };
export type TelegramChannelConfig = { bot_token: string; chat_id: string };
export type SlackChannelConfig = { webhook_url: string };
export type DiscordChannelConfig = { webhook_url: string };
export type WebhookChannelConfig = { url: string };
export type SignalChannelConfig = { base_url: string; number: string; recipients: string[] };

export type NotificationChannelConfig =
  | EmailChannelConfig
  | TelegramChannelConfig
  | SlackChannelConfig
  | DiscordChannelConfig
  | WebhookChannelConfig
  | SignalChannelConfig;

export interface NotificationChannel {
  _id: string;
  company_id: string;
  name: string;
  channel_type: ChannelType;
  config: NotificationChannelConfig;
  is_enabled: boolean;
}

export interface UserSession {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "analyst" | "viewer";
  company_id?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserSession;
}

export interface Vulnerability {
  id: string;
  summary?: string;
  details?: string;
  aliases?: string[];
  modified?: string;
  published?: string;
  withdrawn?: string;
  related?: string[];
  severity?: Array<{ type?: string; score?: string }>;
  affected?: Array<{
    package?: {
      ecosystem?: string;
      name?: string;
      purl?: string;
    };
    severity?: Array<{ type?: string; score?: string }>;
    ranges?: unknown[];
    versions?: string[];
  }>;
  references?: Array<{ type?: string; url?: string }>;
  credits?: Array<{ name?: string; type?: string }>;
  database_specific?: {
    severity?: string;
    cwe_ids?: Array<{ id?: string; name?: string }>;
    epss?: { percentage?: number; percentile?: number };
    cvss_severities?: {
      cvvs_3?: { score?: number; vector_string?: string };
      cvvs_4?: { score?: number; vector_string?: string };
    };
    github_reviewed?: boolean;
    nvd_published_at?: string;
  };
}
