from pydantic import AnyUrl, BaseModel, Field, ValidationError, TypeAdapter, model_validator
from typing import Optional
from models.enums import SubscriptionType, Severity, ChannelType


class CreateSubscriptionRequest(BaseModel):
    company_id: str
    sub_type: SubscriptionType
    keyword: str = Field(..., min_length=2)
    min_severity: Severity = Severity.LOW


class UpdateSubscriptionRequest(BaseModel):
    keyword: Optional[str] = Field(None, min_length=2)
    min_severity: Optional[Severity] = None


class CreateChannelRequest(BaseModel):
    company_id: str
    name: str = Field(..., min_length=1, max_length=200, description="Friendly name, e.g. 'Security Team Slack'")
    channel_type: ChannelType
    config: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_config_by_type(self):
        validate_channel_config(self.channel_type, self.config)
        return self


class UpdateChannelRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    channel_type: Optional[ChannelType] = None
    config: Optional[dict] = None
    is_enabled: Optional[bool] = None


def validate_channel_config(channel_type: ChannelType, config: dict) -> None:
    if not isinstance(config, dict):
        raise ValueError("config must be an object")

    if channel_type == ChannelType.SLACK:
        _require_url(config, "webhook_url")
        return

    if channel_type == ChannelType.DISCORD:
        _require_url(config, "webhook_url")
        return

    if channel_type == ChannelType.WEBHOOK:
        _require_url(config, "url")
        return

    if channel_type == ChannelType.TELEGRAM:
        _require_non_empty_str(config, "bot_token")
        if "chat_id" not in config:
            raise ValueError("telegram config requires chat_id")
        _validate_chat_id(config["chat_id"])
        return

    if channel_type == ChannelType.EMAIL:
        _require_email(config, "recipient_email")
        return

    if channel_type == ChannelType.SIGNAL:
        _require_url(config, "base_url")
        _require_non_empty_str(config, "number")
        recipients = config.get("recipients")
        if not isinstance(recipients, list) or not recipients:
            raise ValueError("signal config requires recipients[]")
        for recipient in recipients:
            if not isinstance(recipient, str) or not recipient.strip():
                raise ValueError("signal recipients must contain non-empty strings")
        return


def _require_non_empty_str(config: dict, key: str) -> None:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")


def _require_url(config: dict, key: str) -> None:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    try:
        TypeAdapter(AnyUrl).validate_python(value)
    except ValidationError as exc:
        raise ValueError(f"{key} must be a valid URL") from exc


def _require_email(config: dict, key: str) -> None:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    if "@" not in value:
        raise ValueError(f"{key} must be a valid email")


def _validate_chat_id(value) -> None:
    if isinstance(value, int):
        return
    if isinstance(value, str) and value.strip():
        return
    raise ValueError("telegram chat_id must be string or integer")
