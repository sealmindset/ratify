"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiGet, apiPut, apiPost, apiDelete } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { RFC, RFCSection, AIResponse } from "@/lib/types";
import {
  Save, Sparkles, Plus, Trash2, GripVertical,
  ChevronUp, ChevronDown, Loader2, ArrowLeft,
} from "lucide-react";

export default function RFCEditPage() {
  const params = useParams();
  const router = useRouter();
  const { hasPermission } = useAuth();
  const rfcId = params.id as string;

  const [rfc, setRfc] = useState<RFC | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [sectionContent, setSectionContent] = useState("");
  const [refineInstruction, setRefineInstruction] = useState("");
  const [refining, setRefining] = useState(false);

  const canUpdate = hasPermission("rfcs", "update");
  const canRefine = hasPermission("ai", "refine");

  const fetchRfc = useCallback(async () => {
    try {
      const data = await apiGet<RFC>(`/rfcs/${rfcId}`);
      setRfc(data);
    } catch (err) {
      console.error("Failed to load RFC:", err);
    } finally {
      setLoading(false);
    }
  }, [rfcId]);

  useEffect(() => {
    fetchRfc();
  }, [fetchRfc]);

  const handleSaveSection = async (sectionId: string) => {
    setSaving(true);
    try {
      await apiPut(`/rfcs/${rfcId}/sections/${sectionId}`, {
        content: sectionContent,
      });
      setEditingSection(null);
      fetchRfc();
    } catch (err) {
      console.error("Failed to save section:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleRefineSection = async (sectionId: string) => {
    if (!refineInstruction.trim()) return;
    setRefining(true);
    try {
      const resp = await apiPost<AIResponse>("/ai/refine", {
        section_id: sectionId,
        instruction: refineInstruction.trim(),
      });
      setSectionContent(resp.message);
      setRefineInstruction("");
      fetchRfc();
    } catch (err) {
      console.error("Failed to refine section:", err);
    } finally {
      setRefining(false);
    }
  };

  const handleAddSection = async () => {
    try {
      const nextOrder = (rfc?.sections.length || 0) + 1;
      await apiPost(`/rfcs/${rfcId}/sections`, {
        title: "New Section",
        content: "",
        section_type: "body",
        order: nextOrder,
      });
      fetchRfc();
    } catch (err) {
      console.error("Failed to add section:", err);
    }
  };

  const handleDeleteSection = async (sectionId: string) => {
    if (!confirm("Delete this section?")) return;
    try {
      await apiDelete(`/rfcs/${rfcId}/sections/${sectionId}`);
      fetchRfc();
    } catch (err) {
      console.error("Failed to delete section:", err);
    }
  };

  const handleUpdateTitle = async (sectionId: string, title: string) => {
    try {
      await apiPut(`/rfcs/${rfcId}/sections/${sectionId}`, { title });
      fetchRfc();
    } catch (err) {
      console.error("Failed to update title:", err);
    }
  };

  const handleUpdateRfc = async (field: string, value: string) => {
    try {
      await apiPut(`/rfcs/${rfcId}`, { [field]: value });
      fetchRfc();
    } catch (err) {
      console.error("Failed to update RFC:", err);
    }
  };

  if (loading || !rfc) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-64 animate-pulse rounded" style={{ backgroundColor: "var(--muted)" }} />
        <div className="h-96 animate-pulse rounded-xl border" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push(`/rfcs/${rfcId}`)}
            className="rounded-md p-1"
            style={{ color: "var(--muted-foreground)" }}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <span className="font-mono text-sm" style={{ color: "var(--muted-foreground)" }}>
              RFC-{rfc.rfc_number}
            </span>
            <h1 className="text-xl font-bold tracking-tight">{rfc.title}</h1>
          </div>
        </div>
        <div className="flex gap-2">
          {canUpdate && (
            <button
              onClick={handleAddSection}
              className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm"
              style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
            >
              <Plus className="h-4 w-4" /> Add Section
            </button>
          )}
        </div>
      </div>

      {/* RFC meta */}
      <div
        className="grid grid-cols-2 gap-4 rounded-lg border p-4"
        style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
      >
        <div>
          <label className="text-xs font-medium" style={{ color: "var(--muted-foreground)" }}>Title</label>
          <input
            type="text"
            defaultValue={rfc.title}
            onBlur={(e) => handleUpdateRfc("title", e.target.value)}
            disabled={!canUpdate}
            className="mt-1 w-full rounded-md border px-3 py-1.5 text-sm"
            style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
          />
        </div>
        <div>
          <label className="text-xs font-medium" style={{ color: "var(--muted-foreground)" }}>Status</label>
          <select
            value={rfc.status}
            onChange={(e) => handleUpdateRfc("status", e.target.value)}
            disabled={!canUpdate}
            className="mt-1 w-full rounded-md border px-3 py-1.5 text-sm"
            style={{ borderColor: "var(--input)", backgroundColor: "var(--background)", color: "var(--foreground)" }}
          >
            {["draft", "in_review", "approved", "rejected", "implemented", "archived"].map((s) => (
              <option key={s} value={s}>{s.replace("_", " ")}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Sections */}
      <div className="space-y-4">
        {rfc.sections.map((section) => (
          <div
            key={section.id}
            className="rounded-lg border"
            style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center justify-between border-b p-3" style={{ borderColor: "var(--border)" }}>
              <div className="flex items-center gap-2">
                <GripVertical className="h-4 w-4" style={{ color: "var(--muted-foreground)" }} />
                {editingSection === section.id ? (
                  <input
                    type="text"
                    defaultValue={section.title}
                    onBlur={(e) => handleUpdateTitle(section.id, e.target.value)}
                    className="rounded border px-2 py-1 text-sm font-medium"
                    style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                    autoFocus
                  />
                ) : (
                  <h3
                    className="text-sm font-semibold cursor-pointer"
                    onClick={() => {
                      setEditingSection(section.id);
                      setSectionContent(section.content || "");
                    }}
                  >
                    {section.title}
                  </h3>
                )}
                <span
                  className="rounded px-1.5 py-0.5 text-xs"
                  style={{ backgroundColor: "var(--muted)", color: "var(--muted-foreground)" }}
                >
                  {section.section_type}
                </span>
              </div>
              <div className="flex items-center gap-1">
                {canUpdate && (
                  <button
                    onClick={() => handleDeleteSection(section.id)}
                    className="rounded p-1"
                    style={{ color: "var(--muted-foreground)" }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>

            {editingSection === section.id ? (
              <div className="p-4 space-y-3">
                <textarea
                  value={sectionContent}
                  onChange={(e) => setSectionContent(e.target.value)}
                  rows={12}
                  className="w-full rounded-md border px-3 py-2 text-sm font-mono"
                  style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                />

                {canRefine && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={refineInstruction}
                      onChange={(e) => setRefineInstruction(e.target.value)}
                      placeholder="Ask AI to refine... (e.g., 'Add more detail about security')"
                      className="flex-1 rounded-md border px-3 py-1.5 text-sm"
                      style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                    />
                    <button
                      onClick={() => handleRefineSection(section.id)}
                      disabled={refining || !refineInstruction.trim()}
                      className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm disabled:opacity-50"
                      style={{ backgroundColor: "color-mix(in oklch, var(--primary) 15%, transparent)", color: "var(--primary)" }}
                    >
                      {refining ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                      Refine
                    </button>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => handleSaveSection(section.id)}
                    disabled={saving}
                    className="inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50"
                    style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
                  >
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    Save
                  </button>
                  <button
                    onClick={() => setEditingSection(null)}
                    className="rounded-md border px-4 py-2 text-sm"
                    style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div
                className="cursor-pointer p-4 text-sm whitespace-pre-wrap"
                style={{ color: section.content ? "var(--foreground)" : "var(--muted-foreground)" }}
                onClick={() => {
                  if (canUpdate) {
                    setEditingSection(section.id);
                    setSectionContent(section.content || "");
                  }
                }}
              >
                {section.content || "Click to edit..."}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
