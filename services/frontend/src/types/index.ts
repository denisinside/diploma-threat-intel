/**
 * Shared types aligned with API models.
 */

export type AssetType = "domain" | "ip_address" | "repository" | "library";
export type TicketStatus = "open" | "in_progress" | "resolved" | "ignored" | "false_positive";
export type Severity = "critical" | "high" | "medium" | "low" | "unknown";
export type ChannelType = "email" | "telegram" | "slack" | "discord" | "webhook";
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
  email?: string;
  username?: string;
  domain?: string;
  leaktype?: string;
  tags?: string[];
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

export interface NotificationChannel {
  _id: string;
  company_id: string;
  name: string;
  channel_type: ChannelType;
  config: Record<string, unknown>;
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
  affected?: Array<{
    package?: {
      ecosystem?: string;
      name?: string;
    };
  }>;
  database_specific?: {
    severity?: string;
  };
}
