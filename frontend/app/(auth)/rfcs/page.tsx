"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { DataTable } from "@/components/data-table";
import { DataTableColumnHeader } from "@/components/data-table-column-header";
import { formatDate, formatRelative } from "@/lib/utils";
import type { RFCListItem } from "@/lib/types";
import { Plus, FileText, MessageSquare, Users } from "lucide-react";

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  draft: { bg: "color-mix(in oklch, var(--muted-foreground) 15%, transparent)", text: "var(--muted-foreground)" },
  in_review: { bg: "color-mix(in oklch, var(--warning) 15%, transparent)", text: "var(--warning)" },
  approved: { bg: "color-mix(in oklch, var(--success) 15%, transparent)", text: "var(--success)" },
  rejected: { bg: "color-mix(in oklch, var(--destructive) 15%, transparent)", text: "var(--destructive)" },
  implemented: { bg: "color-mix(in oklch, var(--primary) 15%, transparent)", text: "var(--primary)" },
  archived: { bg: "color-mix(in oklch, var(--muted-foreground) 10%, transparent)", text: "var(--muted-foreground)" },
};

const TYPE_LABELS: Record<string, string> = {
  infrastructure: "Infrastructure",
  security: "Security",
  process: "Process",
  architecture: "Architecture",
  integration: "Integration",
  data: "Data",
  other: "Other",
};

export default function RFCsPage() {
  const { hasPermission } = useAuth();
  const router = useRouter();
  const [rfcs, setRfcs] = useState<RFCListItem[]>([]);
  const [loading, setLoading] = useState(true);

  const canCreate = hasPermission("rfcs", "create");

  const fetchRfcs = useCallback(async () => {
    try {
      const data = await apiGet<RFCListItem[]>("/rfcs");
      setRfcs(data);
    } catch (err) {
      console.error("Failed to load RFCs:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRfcs();
  }, [fetchRfcs]);

  const columns: ColumnDef<RFCListItem, unknown>[] = [
    {
      accessorKey: "rfc_number",
      header: ({ column }) => <DataTableColumnHeader column={column} title="#" />,
      cell: ({ row }) => (
        <span className="font-mono text-sm" style={{ color: "var(--muted-foreground)" }}>
          RFC-{row.original.rfc_number}
        </span>
      ),
      size: 80,
    },
    {
      accessorKey: "title",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Title" />,
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 shrink-0" style={{ color: "var(--muted-foreground)" }} />
          <span className="font-medium">{row.original.title}</span>
        </div>
      ),
    },
    {
      accessorKey: "rfc_type",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Type" />,
      cell: ({ row }) => TYPE_LABELS[row.original.rfc_type] || row.original.rfc_type,
      filterFn: (row, id, value: string[]) => value.includes(String(row.getValue(id))),
    },
    {
      accessorKey: "status",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
      cell: ({ row }) => {
        const status = row.original.status;
        const colors = STATUS_COLORS[status] || STATUS_COLORS.draft;
        return (
          <span
            className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize"
            style={{ backgroundColor: colors.bg, color: colors.text }}
          >
            {status.replace("_", " ")}
          </span>
        );
      },
      filterFn: (row, id, value: string[]) => value.includes(String(row.getValue(id))),
    },
    {
      accessorKey: "author_name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Author" />,
    },
    {
      accessorKey: "comment_count",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Comments" />,
      cell: ({ row }) => (
        <div className="flex items-center gap-1" style={{ color: "var(--muted-foreground)" }}>
          <MessageSquare className="h-3 w-3" />
          <span>{row.original.comment_count}</span>
        </div>
      ),
      size: 100,
    },
    {
      accessorKey: "review_count",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Reviews" />,
      cell: ({ row }) => (
        <div className="flex items-center gap-1" style={{ color: "var(--muted-foreground)" }}>
          <Users className="h-3 w-3" />
          <span>{row.original.review_count}</span>
        </div>
      ),
      size: 100,
    },
    {
      accessorKey: "updated_at",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Updated" />,
      cell: ({ row }) => (
        <span style={{ color: "var(--muted-foreground)" }}>{formatRelative(row.original.updated_at)}</span>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded" style={{ backgroundColor: "var(--muted)" }} />
        <div className="h-64 animate-pulse rounded-xl border" style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">RFC Registry</h1>
          <p style={{ color: "var(--muted-foreground)" }}>
            All Requests for Comment across the organization.
          </p>
        </div>
        {canCreate && (
          <button
            onClick={() => router.push("/rfcs/new")}
            className="inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium shadow-sm transition-colors"
            style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
            onMouseEnter={(e) => { e.currentTarget.style.opacity = "0.9"; }}
            onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
          >
            <Plus className="h-4 w-4" />
            New RFC
          </button>
        )}
      </div>

      <DataTable
        columns={columns}
        data={rfcs}
        storageKey="rfcs-table"
        searchKey="title"
        searchPlaceholder="Search RFCs..."
        filterableColumns={[
          {
            id: "status",
            title: "Status",
            options: [
              { label: "Draft", value: "draft" },
              { label: "In Review", value: "in_review" },
              { label: "Approved", value: "approved" },
              { label: "Rejected", value: "rejected" },
              { label: "Implemented", value: "implemented" },
              { label: "Archived", value: "archived" },
            ],
          },
          {
            id: "rfc_type",
            title: "Type",
            options: Object.entries(TYPE_LABELS).map(([value, label]) => ({ label, value })),
          },
        ]}
        onRowClick={(rfc) => router.push(`/rfcs/${rfc.id}`)}
      />
    </div>
  );
}
