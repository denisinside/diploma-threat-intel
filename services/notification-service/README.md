# notification-service

Event-driven service that consumes security events from RabbitMQ and delivers notifications to configured channels.

## Supported channels (MVP)

- Slack (`webhook_url`)
- Discord (`webhook_url`)
- Telegram (`bot_token`, `chat_id`)
- Email (`recipient_email`)
- Signal (`base_url`, `number`, `recipients[]`)

## Event exchange contract

- Exchange: `notifications.events` (type: `topic`)
- Routing keys:
  - `leak.source.registered`
  - `vuln.detected`
  - `auth.password_reset_requested`
- Payload schema: `shared/models/notification_event.py` (`NotificationEvent`, version `v1`)

## Environment variables

- `RABBITMQ_URL`
- `RABBITMQ_EXCHANGE` (default: `notifications.events`)
- `RABBITMQ_QUEUE` (default: `notification_events`)
- `RABBITMQ_DLQ` (default: `notification_events.dlq`)
- `RABBITMQ_MAX_RETRIES` (default: `5`)
- `MONGODB_URI`
- `MONGODB_DB_NAME`
- `SMTP_HOST`
- `SMTP_PORT` (default: `587`)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_USE_TLS` (default: `true`)
- `REQUEST_TIMEOUT_SECONDS` (default: `15`)

## Run locally

```bash
pip install -r services/notification-service/requirements.txt
python services/notification-service/main.py
```
