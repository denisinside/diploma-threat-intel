from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class AssetType(str, Enum):
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    REPOSITORY = "repository"
    SOFTWARE_LIB = "library"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    FALSE_POSITIVE = "false_positive"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class ChannelType(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"

class SubscriptionType(str, Enum):
    VULNERABILITY = "vulnerability"
    LEAK = "leak"