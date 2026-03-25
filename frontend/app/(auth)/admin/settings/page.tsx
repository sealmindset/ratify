"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet, apiPut } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime } from "@/lib/utils";
import type { AppSetting, AppSettingAuditLog } from "@/lib/types";
import {
  Settings,
  Save,
  Eye,
  EyeOff,
  RotateCcw,
  Loader2,
  AlertTriangle,
  CheckCircle,
  History,
} from "lucide-react";

type Tab = "settings" | "audit";

interface GroupedSettings {
  [group: string]: AppSetting[];
}

export default function SettingsPage() {
  const { hasPermission } = useAuth();
  const canEdit = hasPermission("admin.settings", "update");

  const [settings, setSettings] = useState<AppSetting[]>([]);
  const [auditLogs, setAuditLogs] = useState<AppSettingAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("settings");

  // Track edited values per key
  const [edits, setEdits] = useState<Record<string, string | null>>({});
  // Track which sensitive fields are revealed
  const [revealed, setRevealed] = useState<Record<string, string | null>>({});
  // Track saving state per group
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  // Flash success per group
  const [saved, setSaved] = useState<Record<string, boolean>>({});

  const fetchSettings = useCallback(async () => {
    try {
      const data = await apiGet<AppSetting[]>("/admin/settings");
      setSettings(data);
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAuditLogs = useCallback(async () => {
    try {
      const data = await apiGet<AppSettingAuditLog[]>(
        "/admin/settings/audit-log"
      );
      setAuditLogs(data);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  useEffect(() => {
    if (tab === "audit") fetchAuditLogs();
  }, [tab, fetchAuditLogs]);

  // Group settings by group_name
  const grouped: GroupedSettings = {};
  for (const s of settings) {
    if (!grouped[s.group_name]) grouped[s.group_name] = [];
    grouped[s.group_name].push(s);
  }
  const groupNames = Object.keys(grouped);

  // Get display value for a setting
  function displayValue(s: AppSetting): string {
    if (s.is_sensitive) {
      if (revealed[s.key] !== undefined) return revealed[s.key] ?? "";
      return "********";
    }
    return s.value ?? "";
  }

  // Get the current edit value or the display value
  function currentValue(s: AppSetting): string {
    if (edits[s.key] !== undefined) return edits[s.key] ?? "";
    return displayValue(s);
  }

  function handleChange(key: string, value: string) {
    setEdits((prev) => ({ ...prev, [key]: value }));
  }

  async function handleReveal(key: string) {
    if (revealed[key] !== undefined) {
      // Hide it again
      setRevealed((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      return;
    }
    try {
      const data = await apiGet<{ key: string; value: string | null }>(
        `/admin/settings/${encodeURIComponent(key)}/reveal`
      );
      setRevealed((prev) => ({ ...prev, [key]: data.value }));
    } catch (err) {
      console.error("Failed to reveal setting:", err);
    }
  }

  async function handleSaveGroup(groupName: string) {
    const groupSettings = grouped[groupName];
    const updates = groupSettings
      .filter((s) => edits[s.key] !== undefined)
      .map((s) => ({ key: s.key, value: edits[s.key] ?? null }));

    if (updates.length === 0) return;

    setSaving((prev) => ({ ...prev, [groupName]: true }));
    try {
      await apiPut("/admin/settings", { settings: updates });
      // Clear edits for this group
      setEdits((prev) => {
        const next = { ...prev };
        for (const u of updates) delete next[u.key];
        return next;
      });
      // Refresh data
      await fetchSettings();
      // Flash success
      setSaved((prev) => ({ ...prev, [groupName]: true }));
      setTimeout(
        () => setSaved((prev) => ({ ...prev, [groupName]: false })),
        2500
      );
    } catch (err) {
      console.error("Failed to save settings:", err);
    } finally {
      setSaving((prev) => ({ ...prev, [groupName]: false }));
    }
  }

  function groupHasEdits(groupName: string): boolean {
    return (grouped[groupName] || []).some((s) => edits[s.key] !== undefined);
  }

  function hasRestartRequired(groupName: string): boolean {
    return (grouped[groupName] || []).some(
      (s) => s.requires_restart && edits[s.key] !== undefined
    );
  }

  // Find display_name for a setting_id in the audit log
  function settingLabel(settingId: string): string {
    const s = settings.find((x) => x.id === settingId);
    return s ? `${s.display_name} (${s.key})` : settingId;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground">
            Manage application configuration
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        <button
          onClick={() => setTab("settings")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === "settings"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Settings className="inline h-4 w-4 mr-1.5 -mt-0.5" />
          Settings
        </button>
        <button
          onClick={() => setTab("audit")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === "audit"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <History className="inline h-4 w-4 mr-1.5 -mt-0.5" />
          Audit Log
        </button>
      </div>

      {/* Settings Tab */}
      {tab === "settings" && (
        <div className="space-y-6">
          {groupNames.length === 0 && (
            <p className="text-muted-foreground py-8 text-center">
              No settings configured.
            </p>
          )}
          {groupNames.map((groupName) => (
            <div
              key={groupName}
              className="rounded-lg border bg-card text-card-foreground"
            >
              {/* Group header */}
              <div className="flex items-center justify-between px-6 py-4 border-b">
                <h2 className="text-lg font-semibold">{groupName}</h2>
                <div className="flex items-center gap-2">
                  {saved[groupName] && (
                    <span className="flex items-center gap-1 text-sm text-green-600 dark:text-green-400">
                      <CheckCircle className="h-4 w-4" />
                      Saved
                      {hasRestartRequired(groupName) &&
                        " (restart required for some changes)"}
                    </span>
                  )}
                  {canEdit && (
                    <button
                      onClick={() => handleSaveGroup(groupName)}
                      disabled={
                        !groupHasEdits(groupName) || saving[groupName]
                      }
                      className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {saving[groupName] ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Save className="h-3.5 w-3.5" />
                      )}
                      Save
                    </button>
                  )}
                </div>
              </div>
              {/* Settings rows */}
              <div className="divide-y">
                {grouped[groupName].map((s) => (
                  <div
                    key={s.key}
                    className="px-6 py-4 flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-6"
                  >
                    {/* Label */}
                    <div className="sm:w-1/3 shrink-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">
                          {s.display_name}
                        </span>
                        {s.requires_restart && (
                          <span className="inline-flex items-center gap-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400">
                            <AlertTriangle className="h-3 w-3" />
                            Restart
                          </span>
                        )}
                        {s.is_sensitive && (
                          <span className="inline-flex items-center rounded-full bg-red-100 dark:bg-red-900/30 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">
                            Sensitive
                          </span>
                        )}
                      </div>
                      {s.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {s.description}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground/60 mt-0.5 font-mono">
                        {s.key}
                      </p>
                    </div>

                    {/* Value */}
                    <div className="flex-1 flex items-center gap-2">
                      {s.value_type === "bool" ? (
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={currentValue(s) === "true"}
                            disabled={!canEdit}
                            onChange={(e) =>
                              handleChange(
                                s.key,
                                e.target.checked ? "true" : "false"
                              )
                            }
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-muted rounded-full peer peer-checked:bg-primary transition-colors after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full" />
                          <span className="ml-2 text-sm text-muted-foreground">
                            {currentValue(s) === "true" ? "Enabled" : "Disabled"}
                          </span>
                        </label>
                      ) : (
                        <input
                          type={
                            s.is_sensitive && revealed[s.key] === undefined
                              ? "password"
                              : s.value_type === "int"
                                ? "number"
                                : "text"
                          }
                          value={currentValue(s)}
                          disabled={!canEdit}
                          onChange={(e) => handleChange(s.key, e.target.value)}
                          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                        />
                      )}

                      {/* Reveal button for sensitive settings */}
                      {s.is_sensitive && canEdit && (
                        <button
                          onClick={() => handleReveal(s.key)}
                          className="inline-flex items-center justify-center h-9 w-9 rounded-md border border-input bg-transparent hover:bg-accent transition-colors shrink-0"
                          title={
                            revealed[s.key] !== undefined
                              ? "Hide value"
                              : "Reveal value"
                          }
                        >
                          {revealed[s.key] !== undefined ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      )}

                      {/* Reset edit */}
                      {edits[s.key] !== undefined && (
                        <button
                          onClick={() =>
                            setEdits((prev) => {
                              const next = { ...prev };
                              delete next[s.key];
                              return next;
                            })
                          }
                          className="inline-flex items-center justify-center h-9 w-9 rounded-md border border-input bg-transparent hover:bg-accent transition-colors shrink-0"
                          title="Reset to original"
                        >
                          <RotateCcw className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Audit Log Tab */}
      {tab === "audit" && (
        <div className="rounded-lg border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Time</th>
                  <th className="px-4 py-3 text-left font-medium">Setting</th>
                  <th className="px-4 py-3 text-left font-medium">
                    Old Value
                  </th>
                  <th className="px-4 py-3 text-left font-medium">
                    New Value
                  </th>
                  <th className="px-4 py-3 text-left font-medium">
                    Changed By
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {auditLogs.length === 0 && (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-8 text-center text-muted-foreground"
                    >
                      No changes recorded yet.
                    </td>
                  </tr>
                )}
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-muted/30">
                    <td className="px-4 py-2.5 whitespace-nowrap text-muted-foreground">
                      {formatDateTime(log.created_at)}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {settingLabel(log.setting_id)}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                      {log.old_value ?? <span className="italic">empty</span>}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {log.new_value ?? <span className="italic">empty</span>}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {log.changed_by}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
