import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  useCreateChannel,
  useCreateSubscription,
  useDeleteChannel,
  useDeleteSubscription,
  useNotificationChannels,
  useSubscriptions,
  useTestChannel,
  useUpdateChannel,
} from "@/features/subscriptions/hooks";
import { useAuth } from "@/hooks/useAuth";
import { useCanMutate } from "@/hooks/useRoleGuard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import type {
  ChannelType,
  NotificationChannel,
  NotificationChannelConfig,
  Subscription,
} from "@/types";

type Tab = "subscriptions" | "channels";

export function SubscriptionsPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const [tab, setTab] = useState<Tab>("subscriptions");
  const [keyword, setKeyword] = useState("");
  const [subType, setSubType] = useState<Subscription["sub_type"]>("vulnerability");
  const [minSeverity, setMinSeverity] = useState<Subscription["min_severity"]>("medium");
  const [channelName, setChannelName] = useState("");
  const [channelType, setChannelType] = useState<NotificationChannel["channel_type"]>("email");
  const [configEmail, setConfigEmail] = useState("");
  const [configTelegramBotToken, setConfigTelegramBotToken] = useState("");
  const [configTelegramChatId, setConfigTelegramChatId] = useState("");
  const [configSlackWebhook, setConfigSlackWebhook] = useState("");
  const [configDiscordWebhook, setConfigDiscordWebhook] = useState("");
  const [configGenericWebhook, setConfigGenericWebhook] = useState("");
  const [configSignalBaseUrl, setConfigSignalBaseUrl] = useState("http://signal-api:8080");
  const [configSignalNumber, setConfigSignalNumber] = useState("");
  const [configSignalRecipients, setConfigSignalRecipients] = useState("");
  const [uiError, setUiError] = useState("");
  const createSubscription = useCreateSubscription();
  const createChannel = useCreateChannel();
  const updateChannel = useUpdateChannel();
  const deleteChannel = useDeleteChannel();
  const deleteSubscription = useDeleteSubscription();
  const testChannel = useTestChannel();
  const canMutate = useCanMutate();
  const { data: subscriptions = [] } = useSubscriptions(companyId);
  const { data: channels = [] } = useNotificationChannels(companyId);

  const subColumns = useMemo<Array<ColumnDef<Subscription>>>(
    () => [
      { header: "Type", accessorKey: "sub_type" },
      { header: "Keyword", accessorKey: "keyword" },
      {
        header: "Min Severity",
        cell: ({ row }) => <SeverityBadge severity={row.original.min_severity} />,
      },
      ...(canMutate
        ? [
            {
              header: "Actions",
              cell: ({ row }: { row: { original: Subscription } }) => (
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm("Delete this subscription rule?")) {
                      deleteSubscription.mutate(row.original._id);
                    }
                  }}
                  className="text-xs text-red-300 hover:text-red-200"
                >
                  delete
                </button>
              ),
            } as ColumnDef<Subscription>,
          ]
        : []),
    ],
    [canMutate, deleteSubscription]
  );

  const channelColumns = useMemo<Array<ColumnDef<NotificationChannel>>>(
    () => [
      { header: "Name", accessorKey: "name" },
      { header: "Type", accessorKey: "channel_type" },
      {
        header: "Enabled",
        cell: ({ row }) =>
          canMutate ? (
            <button
              type="button"
              onClick={() =>
                updateChannel.mutate({
                  channelId: row.original._id,
                  payload: { is_enabled: !row.original.is_enabled },
                })
              }
              className={`text-xs ${row.original.is_enabled ? "text-emerald-300" : "text-slate-400"}`}
            >
              {row.original.is_enabled ? "enabled" : "disabled"}
            </button>
          ) : (
            <span className="text-slate-400">{row.original.is_enabled ? "enabled" : "disabled"}</span>
          ),
      },
      {
        header: "Config",
        cell: ({ row }) => renderMaskedConfig(row.original),
      },
      ...(canMutate
        ? [
            {
              header: "Actions",
              cell: ({ row }: { row: { original: NotificationChannel } }) => (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => testChannel.mutate(row.original._id)}
                    disabled={testChannel.isPending || !row.original.is_enabled}
                    className="text-xs text-tactical-sky hover:text-sky-200 disabled:opacity-50"
                  >
                    {testChannel.isPending ? "Sending..." : "test"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (window.confirm("Delete this channel?")) {
                        deleteChannel.mutate(row.original._id);
                      }
                    }}
                    className="text-xs text-red-300 hover:text-red-200"
                  >
                    delete
                  </button>
                </div>
              ),
            } as ColumnDef<NotificationChannel>,
          ]
        : []),
    ],
    [canMutate, updateChannel, deleteChannel, testChannel]
  );

  function renderMaskedConfig(channel: NotificationChannel): string {
    const config = channel.config as Record<string, unknown>;
    if (channel.channel_type === "telegram") {
      return JSON.stringify({
        chat_id: config.chat_id,
        bot_token: "***",
      });
    }
    if (channel.channel_type === "slack" || channel.channel_type === "discord" || channel.channel_type === "webhook") {
      const key = channel.channel_type === "webhook" ? "url" : "webhook_url";
      return JSON.stringify({ [key]: "***" });
    }
    if (channel.channel_type === "signal") {
      return JSON.stringify({
        base_url: config.base_url,
        number: config.number ? "***" : undefined,
        recipients: config.recipients,
      });
    }
    return JSON.stringify(config);
  }

  function buildChannelConfig(type: ChannelType): NotificationChannelConfig {
    if (type === "email") {
      if (!configEmail.trim()) throw new Error("Recipient email is required.");
      return { recipient_email: configEmail.trim() };
    }
    if (type === "telegram") {
      if (!configTelegramBotToken.trim() || !configTelegramChatId.trim()) {
        throw new Error("Telegram bot token and chat ID are required.");
      }
      return {
        bot_token: configTelegramBotToken.trim(),
        chat_id: configTelegramChatId.trim(),
      };
    }
    if (type === "slack") {
      if (!configSlackWebhook.trim()) throw new Error("Slack webhook URL is required.");
      return { webhook_url: configSlackWebhook.trim() };
    }
    if (type === "discord") {
      if (!configDiscordWebhook.trim()) throw new Error("Discord webhook URL is required.");
      return { webhook_url: configDiscordWebhook.trim() };
    }
    if (type === "webhook") {
      if (!configGenericWebhook.trim()) throw new Error("Webhook URL is required.");
      return { url: configGenericWebhook.trim() };
    }
    if (type === "signal") {
      const recipients = configSignalRecipients
        .split(",")
        .map((entry) => entry.trim())
        .filter(Boolean);
      if (!configSignalBaseUrl.trim() || !configSignalNumber.trim() || recipients.length === 0) {
        throw new Error("Signal base URL, number, and at least one recipient are required.");
      }
      return {
        base_url: configSignalBaseUrl.trim(),
        number: configSignalNumber.trim(),
        recipients,
      };
    }
    throw new Error("Unsupported channel type.");
  }

  function resetChannelInputs() {
    setChannelName("");
    setConfigEmail("");
    setConfigTelegramBotToken("");
    setConfigTelegramChatId("");
    setConfigSlackWebhook("");
    setConfigDiscordWebhook("");
    setConfigGenericWebhook("");
    setConfigSignalNumber("");
    setConfigSignalRecipients("");
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Subscriptions</h1>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setTab("subscriptions")}
          className={`px-3 py-1.5 rounded border text-sm ${
            tab === "subscriptions"
              ? "border-tactical-sky/50 text-tactical-sky bg-tactical-sky/15"
              : "border-slate-700/50 text-slate-300"
          }`}
        >
          Monitoring Rules
        </button>
        <button
          type="button"
          onClick={() => setTab("channels")}
          className={`px-3 py-1.5 rounded border text-sm ${
            tab === "channels"
              ? "border-tactical-sky/50 text-tactical-sky bg-tactical-sky/15"
              : "border-slate-700/50 text-slate-300"
          }`}
        >
          Notification Channels
        </button>
      </div>

      <SectionCard title={tab === "subscriptions" ? "Company Subscriptions" : "Notification Channels"}>
        {companyId && canMutate && tab === "subscriptions" ? (
          <form
            className="mb-4 grid grid-cols-1 md:grid-cols-4 gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setUiError("");
              if (!keyword.trim()) {
                setUiError("Keyword is required.");
                return;
              }
              createSubscription.mutate(
                {
                  company_id: companyId,
                  sub_type: subType,
                  keyword: keyword.trim(),
                  min_severity: minSeverity,
                },
                {
                  onSuccess: () => setKeyword(""),
                  onError: (mutationError) =>
                    setUiError(
                      mutationError instanceof Error ? mutationError.message : "Failed to create subscription."
                    ),
                }
              );
            }}
          >
            <select
              value={subType}
              onChange={(event) => setSubType(event.target.value as Subscription["sub_type"])}
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            >
              <option value="vulnerability">vulnerability</option>
              <option value="leak">leak</option>
            </select>
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Keyword (domain/package/CVE)"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <select
              value={minSeverity}
              onChange={(event) => setMinSeverity(event.target.value as Subscription["min_severity"])}
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            >
              <option value="critical">critical</option>
              <option value="high">high</option>
              <option value="medium">medium</option>
              <option value="low">low</option>
              <option value="unknown">unknown</option>
            </select>
            <button
              type="submit"
              className="rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm px-3 py-2"
            >
              {createSubscription.isPending ? "Creating..." : "Add rule"}
            </button>
          </form>
        ) : null}

        {companyId && canMutate && tab === "channels" ? (
          <form
            className="mb-4 grid grid-cols-1 md:grid-cols-4 gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setUiError("");
              if (!channelName.trim()) {
                setUiError("Channel name is required.");
                return;
              }
              let parsedConfig: NotificationChannelConfig;
              try {
                parsedConfig = buildChannelConfig(channelType);
              } catch (configError) {
                setUiError(configError instanceof Error ? configError.message : "Invalid channel config.");
                return;
              }
              createChannel.mutate(
                {
                  company_id: companyId,
                  name: channelName.trim(),
                  channel_type: channelType,
                  config: parsedConfig,
                },
                {
                  onSuccess: () => {
                    resetChannelInputs();
                  },
                  onError: (mutationError) =>
                    setUiError(mutationError instanceof Error ? mutationError.message : "Failed to create channel."),
                }
              );
            }}
          >
            <input
              value={channelName}
              onChange={(event) => setChannelName(event.target.value)}
              placeholder="Channel name"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <select
              value={channelType}
              onChange={(event) => setChannelType(event.target.value as NotificationChannel["channel_type"])}
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            >
              <option value="email">email</option>
              <option value="telegram">telegram</option>
              <option value="slack">slack</option>
              <option value="discord">discord</option>
              <option value="webhook">webhook</option>
              <option value="signal">signal</option>
            </select>
            {channelType === "email" ? (
              <input
                value={configEmail}
                onChange={(event) => setConfigEmail(event.target.value)}
                placeholder="recipient@example.com"
                className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
              />
            ) : null}
            {channelType === "telegram" ? (
              <div className="grid grid-cols-1 gap-2">
                <input
                  type="password"
                  value={configTelegramBotToken}
                  onChange={(event) => setConfigTelegramBotToken(event.target.value)}
                  placeholder="Telegram bot token"
                  className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
                />
                <input
                  value={configTelegramChatId}
                  onChange={(event) => setConfigTelegramChatId(event.target.value)}
                  placeholder="Telegram chat ID"
                  className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
                />
              </div>
            ) : null}
            {channelType === "slack" ? (
              <input
                type="password"
                value={configSlackWebhook}
                onChange={(event) => setConfigSlackWebhook(event.target.value)}
                placeholder="Slack webhook URL"
                className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
              />
            ) : null}
            {channelType === "discord" ? (
              <input
                type="password"
                value={configDiscordWebhook}
                onChange={(event) => setConfigDiscordWebhook(event.target.value)}
                placeholder="Discord webhook URL"
                className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
              />
            ) : null}
            {channelType === "webhook" ? (
              <input
                type="password"
                value={configGenericWebhook}
                onChange={(event) => setConfigGenericWebhook(event.target.value)}
                placeholder="Webhook URL"
                className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
              />
            ) : null}
            {channelType === "signal" ? (
              <div className="grid grid-cols-1 gap-2">
                <input
                  value={configSignalBaseUrl}
                  onChange={(event) => setConfigSignalBaseUrl(event.target.value)}
                  placeholder="Signal API base URL"
                  className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
                />
                <input
                  value={configSignalNumber}
                  onChange={(event) => setConfigSignalNumber(event.target.value)}
                  placeholder="Signal sender number"
                  className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
                />
                <input
                  value={configSignalRecipients}
                  onChange={(event) => setConfigSignalRecipients(event.target.value)}
                  placeholder="Recipients, comma-separated"
                  className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
                />
              </div>
            ) : null}
            <button
              type="submit"
              className="rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm px-3 py-2"
            >
              {createChannel.isPending ? "Creating..." : "Add channel"}
            </button>
          </form>
        ) : null}

        {uiError ? <p className="mb-2 text-sm text-red-300">{uiError}</p> : null}
        {!canMutate && companyId ? (
          <p className="mb-2 text-sm text-slate-400">Viewer role: you cannot create, edit, or delete.</p>
        ) : null}
        {tab === "subscriptions" ? (
          <DataTable data={subscriptions} columns={subColumns} emptyText="No subscription rules." />
        ) : (
          <DataTable data={channels} columns={channelColumns} emptyText="No channels configured." />
        )}
      </SectionCard>

      {!companyId ? (
        <p className="text-sm text-amber-300">
          Your account has no `company_id`, so company-scoped subscriptions are unavailable.
        </p>
      ) : null}
    </div>
  );
}
