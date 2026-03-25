"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet, apiPut, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatRelative } from "@/lib/utils";
import {
  Bot, Save, RotateCcw, TestTube, X, ChevronDown, ChevronRight,
  Loader2, Clock, Pencil,
} from "lucide-react";

interface PromptVersion {
  id: string;
  version: number;
  content: string;
  change_summary: string;
  changed_by_name: string | null;
  created_at: string;
}

interface Prompt {
  id: string;
  slug: string;
  name: string;
  content: string;
  category: string;
  model_key: string;
  version: number;
  is_active: boolean;
  updated_by_name: string | null;
  created_at: string;
  updated_at: string;
}

interface PromptDetail extends Prompt {
  versions: PromptVersion[];
}

const CATEGORY_LABELS: Record<string, string> = {
  interview: "Interview Prompts",
  generation: "Generation",
  refinement: "Refinement",
  assistance: "Assistance",
  general: "General",
};

const MODEL_LABELS: Record<string, string> = {
  heavy: "Heavy (Opus)",
  standard: "Standard (Sonnet)",
  light: "Light (Haiku)",
};

export default function PromptsPage() {
  const { hasPermission } = useAuth();
  const canEdit = hasPermission("admin.prompts", "update");

  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [detail, setDetail] = useState<PromptDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Editor state
  const [editContent, setEditContent] = useState("");
  const [changeSummary, setChangeSummary] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  // Test state
  const [showTest, setShowTest] = useState(false);
  const [testInput, setTestInput] = useState("Tell me about a new authentication system for our microservices.");
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  // Version history
  const [showVersions, setShowVersions] = useState(false);

  const fetchPrompts = useCallback(async () => {
    try {
      const data = await apiGet<Prompt[]>("/admin/prompts");
      setPrompts(data);
    } catch (err) {
      console.error("Failed to load prompts:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDetail = useCallback(async (slug: string) => {
    try {
      const data = await apiGet<PromptDetail>(`/admin/prompts/${slug}`);
      setDetail(data);
      setEditContent(data.content);
      setIsDirty(false);
      setChangeSummary("");
      setTestResult(null);
    } catch (err) {
      console.error("Failed to load prompt:", err);
    }
  }, []);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  useEffect(() => {
    if (selectedSlug) fetchDetail(selectedSlug);
  }, [selectedSlug, fetchDetail]);

  const handleSave = async () => {
    if (!detail || !changeSummary.trim()) return;
    setSaving(true);
    try {
      await apiPut(`/admin/prompts/${detail.slug}`, {
        content: editContent,
        change_summary: changeSummary.trim(),
      });
      await fetchDetail(detail.slug);
      await fetchPrompts();
    } catch (err) {
      console.error("Failed to save prompt:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = async (versionId: string) => {
    if (!detail) return;
    setSaving(true);
    try {
      await apiPost(`/admin/prompts/${detail.slug}/restore/${versionId}`);
      await fetchDetail(detail.slug);
      await fetchPrompts();
    } catch (err) {
      console.error("Failed to restore:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!detail) return;
    setTesting(true);
    try {
      const result = await apiPost<{ preview: string; token_estimate: number }>(
        `/admin/prompts/${detail.slug}/test`,
        { content: editContent, sample_input: testInput },
      );
      setTestResult(result.preview);
    } catch (err) {
      console.error("Failed to test:", err);
    } finally {
      setTesting(false);
    }
  };

  // Group prompts by category
  const grouped = prompts.reduce<Record<string, Prompt[]>>((acc, p) => {
    (acc[p.category] ??= []).push(p);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-64 animate-pulse rounded" style={{ backgroundColor: "var(--muted)" }} />
        <div className="h-96 animate-pulse rounded-xl border" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Prompt Management</h1>
        <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
          Edit the prompts that power Ratify&apos;s AI features. Changes take effect immediately.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Prompt list */}
        <div className="space-y-3">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category}>
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-1.5" style={{ color: "var(--muted-foreground)" }}>
                {CATEGORY_LABELS[category] || category}
              </h3>
              <div className="space-y-1">
                {items.map((p) => (
                  <button
                    key={p.slug}
                    onClick={() => setSelectedSlug(p.slug)}
                    className={`w-full text-left rounded-lg border p-3 transition-all text-sm ${
                      selectedSlug === p.slug ? "ring-2 ring-yellow-500" : ""
                    }`}
                    style={{
                      backgroundColor: selectedSlug === p.slug
                        ? "color-mix(in oklch, var(--primary) 8%, var(--card))"
                        : "var(--card)",
                      borderColor: selectedSlug === p.slug ? "var(--primary)" : "var(--border)",
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 shrink-0" style={{ color: "var(--primary)" }} />
                      <span className="font-medium truncate">{p.name}</span>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs" style={{ color: "var(--muted-foreground)" }}>
                      <span>{MODEL_LABELS[p.model_key] || p.model_key}</span>
                      <span>&middot;</span>
                      <span>v{p.version}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Editor panel */}
        <div className="lg:col-span-2">
          {!detail ? (
            <div className="flex h-96 items-center justify-center rounded-lg border" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}>
              <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
                Select a prompt to view and edit
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Header */}
              <div className="rounded-lg border p-4" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">{detail.name}</h2>
                    <div className="flex items-center gap-3 mt-1 text-xs" style={{ color: "var(--muted-foreground)" }}>
                      <span className="font-mono">{detail.slug}</span>
                      <span>&middot;</span>
                      <span>{MODEL_LABELS[detail.model_key] || detail.model_key}</span>
                      <span>&middot;</span>
                      <span>Version {detail.version}</span>
                      {detail.updated_by_name && (
                        <>
                          <span>&middot;</span>
                          <span>Updated by {detail.updated_by_name} {formatRelative(detail.updated_at)}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowTest(!showTest)}
                      className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs"
                      style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                    >
                      <TestTube className="h-3 w-3" /> Test
                    </button>
                    <button
                      onClick={() => setShowVersions(!showVersions)}
                      className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs"
                      style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                    >
                      <Clock className="h-3 w-3" /> History
                    </button>
                  </div>
                </div>
              </div>

              {/* Editor */}
              <div className="rounded-lg border p-4 space-y-3" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}>
                <div className="flex items-center gap-2">
                  <Pencil className="h-4 w-4" style={{ color: "var(--primary)" }} />
                  <h3 className="text-sm font-medium">Prompt Content</h3>
                  {isDirty && (
                    <span className="rounded-full px-2 py-0.5 text-xs" style={{ backgroundColor: "color-mix(in oklch, var(--warning) 15%, transparent)", color: "var(--warning)" }}>
                      Unsaved changes
                    </span>
                  )}
                </div>
                <textarea
                  value={editContent}
                  onChange={(e) => {
                    setEditContent(e.target.value);
                    setIsDirty(e.target.value !== detail.content);
                  }}
                  rows={10}
                  disabled={!canEdit}
                  className="w-full rounded-md border px-3 py-2 text-sm font-mono leading-relaxed"
                  style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                />

                {canEdit && isDirty && (
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={changeSummary}
                      onChange={(e) => setChangeSummary(e.target.value)}
                      placeholder="Describe what you changed (required)..."
                      className="w-full rounded-md border px-3 py-2 text-sm"
                      style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleSave}
                        disabled={!changeSummary.trim() || saving}
                        className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50"
                        style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
                      >
                        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditContent(detail.content);
                          setIsDirty(false);
                          setChangeSummary("");
                        }}
                        className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm"
                        style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                      >
                        <X className="h-4 w-4" /> Discard
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Test panel */}
              {showTest && (
                <div className="rounded-lg border p-4 space-y-3" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}>
                  <h3 className="text-sm font-medium flex items-center gap-2">
                    <TestTube className="h-4 w-4" style={{ color: "var(--primary)" }} />
                    Test Prompt
                  </h3>
                  <textarea
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    rows={3}
                    placeholder="Sample user input to test with..."
                    className="w-full rounded-md border px-3 py-2 text-sm"
                    style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                  />
                  <button
                    onClick={handleTest}
                    disabled={testing}
                    className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50"
                    style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
                  >
                    {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube className="h-4 w-4" />}
                    Run Test
                  </button>
                  {testResult && (
                    <pre className="rounded-md border p-3 text-xs overflow-auto whitespace-pre-wrap font-mono"
                      style={{ backgroundColor: "var(--background)", borderColor: "var(--border)", maxHeight: "300px" }}>
                      {testResult}
                    </pre>
                  )}
                </div>
              )}

              {/* Version history */}
              {showVersions && (
                <div className="rounded-lg border p-4 space-y-3" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}>
                  <h3 className="text-sm font-medium flex items-center gap-2">
                    <Clock className="h-4 w-4" style={{ color: "var(--primary)" }} />
                    Version History
                  </h3>
                  {detail.versions.length === 0 ? (
                    <p className="text-xs" style={{ color: "var(--muted-foreground)" }}>No version history yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {detail.versions.map((v) => (
                        <VersionRow
                          key={v.id}
                          version={v}
                          isCurrent={v.version === detail.version}
                          currentContent={detail.content}
                          canRestore={canEdit && v.version !== detail.version}
                          onRestore={() => handleRestore(v.id)}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function VersionRow({
  version,
  isCurrent,
  currentContent,
  canRestore,
  onRestore,
}: {
  version: PromptVersion;
  isCurrent: boolean;
  currentContent: string;
  canRestore: boolean;
  onRestore: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="rounded-md border p-3"
      style={{
        backgroundColor: isCurrent
          ? "color-mix(in oklch, var(--primary) 5%, var(--card))"
          : "var(--card)",
        borderColor: "var(--border)",
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={() => setExpanded(!expanded)} className="shrink-0">
            {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          </button>
          <span className="text-sm font-medium">v{version.version}</span>
          {isCurrent && (
            <span className="rounded-full px-2 py-0.5 text-xs"
              style={{ backgroundColor: "color-mix(in oklch, var(--success) 15%, transparent)", color: "var(--success)" }}>
              current
            </span>
          )}
          <span className="text-xs" style={{ color: "var(--muted-foreground)" }}>
            {version.change_summary}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: "var(--muted-foreground)" }}>
            {version.changed_by_name && `${version.changed_by_name} · `}
            {formatRelative(version.created_at)}
          </span>
          {canRestore && (
            <button
              onClick={onRestore}
              className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs"
              style={{ color: "var(--primary)" }}
            >
              <RotateCcw className="h-3 w-3" /> Restore
            </button>
          )}
        </div>
      </div>
      {expanded && (
        <pre className="mt-2 rounded-md border p-2 text-xs overflow-auto whitespace-pre-wrap font-mono"
          style={{ backgroundColor: "var(--background)", borderColor: "var(--border)", maxHeight: "200px" }}>
          {version.content}
        </pre>
      )}
    </div>
  );
}
