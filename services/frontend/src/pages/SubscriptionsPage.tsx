import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  useCreateChannel,
  useCreateSubscription,
  useNotificationChannels,
  useSubscriptions,
  useUpdateChannel,
} from "@/features/subscriptions/hooks";
import { useAuth } from "@/hooks/useAuth";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import type { NotificationChannel, Subscription } from "@/types";

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
  const [channelConfig, setChannelConfig] = useState("");
  const [uiError, setUiError] = useState("");
  const createSubscription = useCreateSubscription();
  const createChannel = useCreateChannel();
  const updateChannel = useUpdateChannel();
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
    ],
    []
  );

  const channelColumns = useMemo<Array<ColumnDef<NotificationChannel>>>(
    () => [
      { header: "Name", accessorKey: "name" },
      { header: "Type", accessorKey: "channel_type" },
      {
        header: "Enabled",
        cell: ({ row }) => (
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
        ),
      },
      {
        header: "Config",
        cell: ({ row }) => JSON.stringify(row.original.config),
      },
    ],
    []
  );

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
        {companyId && tab === "subscriptions" ? (
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

        {companyId && tab === "channels" ? (
          <form
            className="mb-4 grid grid-cols-1 md:grid-cols-4 gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setUiError("");
              if (!channelName.trim()) {
                setUiError("Channel name is required.");
                return;
              }
              let parsedConfig: Record<string, unknown> = {};
              if (channelConfig.trim()) {
                try {
                  parsedConfig = JSON.parse(channelConfig);
                } catch {
                  setUiError("Config must be valid JSON.");
                  return;
                }
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
                    setChannelName("");
                    setChannelConfig("");
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
            </select>
            <input
              value={channelConfig}
              onChange={(event) => setChannelConfig(event.target.value)}
              placeholder='Config JSON, e.g. {"url":"..."}'
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm px-3 py-2"
            >
              {createChannel.isPending ? "Creating..." : "Add channel"}
            </button>
          </form>
        ) : null}

        {uiError ? <p className="mb-2 text-sm text-red-300">{uiError}</p> : null}
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
