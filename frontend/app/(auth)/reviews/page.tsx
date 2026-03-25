"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { DataTable } from "@/components/data-table";
import { DataTableColumnHeader } from "@/components/data-table-column-header";
import { formatDate, daysUntil } from "@/lib/utils";
import type { ReviewAssignment } from "@/lib/types";
import { Clock, AlertCircle } from "lucide-react";

export default function MyReviewsPage() {
  const { hasPermission } = useAuth();
  const router = useRouter();
  const [reviews, setReviews] = useState<ReviewAssignment[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReviews = useCallback(async () => {
    try {
      const data = await apiGet<ReviewAssignment[]>("/my-reviews");
      setReviews(data);
    } catch (err) {
      console.error("Failed to load reviews:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const columns: ColumnDef<ReviewAssignment, unknown>[] = [
    {
      accessorKey: "rfc_id",
      header: ({ column }) => <DataTableColumnHeader column={column} title="RFC" />,
      cell: ({ row }) => (
        <button
          className="text-sm font-medium underline"
          style={{ color: "var(--primary)" }}
          onClick={() => router.push(`/rfcs/${row.original.rfc_id}`)}
        >
          View RFC
        </button>
      ),
    },
    {
      accessorKey: "team",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Team" />,
      filterFn: (row, id, value: string[]) => value.includes(String(row.getValue(id))),
    },
    {
      accessorKey: "status",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
      cell: ({ row }) => {
        const status = row.original.status;
        const color =
          status === "completed" ? "var(--success)" :
          status === "in_progress" ? "var(--warning)" :
          "var(--muted-foreground)";
        return (
          <span
            className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize"
            style={{
              backgroundColor: `color-mix(in oklch, ${color} 15%, transparent)`,
              color,
            }}
          >
            {status.replace("_", " ")}
          </span>
        );
      },
      filterFn: (row, id, value: string[]) => value.includes(String(row.getValue(id))),
    },
    {
      accessorKey: "deadline",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Deadline" />,
      cell: ({ row }) => {
        const deadline = row.original.deadline;
        if (!deadline) return <span style={{ color: "var(--muted-foreground)" }}>-</span>;
        const days = daysUntil(deadline);
        const overdue = days < 0;
        return (
          <div className="flex items-center gap-1">
            {overdue ? (
              <AlertCircle className="h-3 w-3" style={{ color: "var(--destructive)" }} />
            ) : (
              <Clock className="h-3 w-3" style={{ color: "var(--muted-foreground)" }} />
            )}
            <span style={{ color: overdue ? "var(--destructive)" : "var(--foreground)" }}>
              {formatDate(deadline)}
            </span>
            {overdue && (
              <span className="text-xs" style={{ color: "var(--destructive)" }}>
                ({Math.abs(days)}d overdue)
              </span>
            )}
          </div>
        );
      },
    },
    {
      accessorKey: "jira_task_key",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Jira" />,
      cell: ({ row }) => row.original.jira_task_key || "-",
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Assigned" />,
      cell: ({ row }) => formatDate(row.original.created_at),
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
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Reviews</h1>
        <p style={{ color: "var(--muted-foreground)" }}>
          Your assigned RFC review tasks.
        </p>
      </div>

      <DataTable
        columns={columns}
        data={reviews}
        storageKey="my-reviews-table"
        filterableColumns={[
          {
            id: "status",
            title: "Status",
            options: [
              { label: "Pending", value: "pending" },
              { label: "In Progress", value: "in_progress" },
              { label: "Completed", value: "completed" },
            ],
          },
        ]}
      />
    </div>
  );
}
