"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatRelative } from "@/lib/utils";
import type { RFCListItem, ReviewAssignment } from "@/lib/types";
import {
  FileText, Clock, CheckCircle, AlertCircle,
  MessageSquare, Users, Plus, ArrowRight,
} from "lucide-react";

interface DashboardData {
  rfcs: RFCListItem[];
  myReviews: ReviewAssignment[];
}

export default function DashboardPage() {
  const { authMe, hasPermission } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [rfcs, myReviews] = await Promise.all([
        apiGet<RFCListItem[]>("/rfcs"),
        apiGet<ReviewAssignment[]>("/my-reviews").catch(() => []),
      ]);
      setData({ rfcs, myReviews });
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p style={{ color: "var(--muted-foreground)" }}>Loading...</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-28 animate-pulse rounded-xl border"
              style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
            />
          ))}
        </div>
      </div>
    );
  }

  const rfcs = data?.rfcs || [];
  const myReviews = data?.myReviews || [];

  const totalRfcs = rfcs.length;
  const drafts = rfcs.filter((r) => r.status === "draft").length;
  const inReview = rfcs.filter((r) => r.status === "in_review").length;
  const approved = rfcs.filter((r) => r.status === "approved").length;
  const pendingReviews = myReviews.filter((r) => r.status === "pending").length;
  const recentRfcs = rfcs.slice(0, 5);

  const stats = [
    { label: "Total RFCs", value: totalRfcs, icon: FileText, color: "var(--primary)" },
    { label: "In Review", value: inReview, icon: Clock, color: "var(--warning)" },
    { label: "Approved", value: approved, icon: CheckCircle, color: "var(--success)" },
    { label: "My Pending Reviews", value: pendingReviews, icon: AlertCircle, color: "var(--destructive)" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p style={{ color: "var(--muted-foreground)" }}>
            Welcome to Ratify{authMe?.name ? `, ${authMe.name}` : ""}.
          </p>
        </div>
        {hasPermission("rfcs", "create") && (
          <button
            onClick={() => router.push("/rfcs/new")}
            className="inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium shadow-sm"
            style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
          >
            <Plus className="h-4 w-4" />
            New RFC
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="rounded-xl border p-6"
            style={{ backgroundColor: "var(--card)", borderColor: "var(--border)", color: "var(--card-foreground)" }}
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium" style={{ color: "var(--muted-foreground)" }}>
                {label}
              </p>
              <Icon className="h-4 w-4" style={{ color }} />
            </div>
            <p className="mt-2 text-3xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent RFCs */}
        <div
          className="rounded-xl border"
          style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
        >
          <div className="flex items-center justify-between border-b p-4" style={{ borderColor: "var(--border)" }}>
            <h2 className="text-sm font-semibold">Recent RFCs</h2>
            <button
              onClick={() => router.push("/rfcs")}
              className="inline-flex items-center gap-1 text-xs"
              style={{ color: "var(--primary)" }}
            >
              View all <ArrowRight className="h-3 w-3" />
            </button>
          </div>
          <div className="divide-y" style={{ borderColor: "var(--border)" }}>
            {recentRfcs.length === 0 ? (
              <p className="p-4 text-sm" style={{ color: "var(--muted-foreground)" }}>
                No RFCs yet. Create your first one!
              </p>
            ) : (
              recentRfcs.map((rfc) => (
                <button
                  key={rfc.id}
                  onClick={() => router.push(`/rfcs/${rfc.id}`)}
                  className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-muted/50"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs" style={{ color: "var(--muted-foreground)" }}>
                        RFC-{rfc.rfc_number}
                      </span>
                      <span className="truncate text-sm font-medium">{rfc.title}</span>
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-xs" style={{ color: "var(--muted-foreground)" }}>
                      <span>{rfc.author_name}</span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" /> {rfc.comment_count}
                      </span>
                      <span className="flex items-center gap-1">
                        <Users className="h-3 w-3" /> {rfc.review_count}
                      </span>
                    </div>
                  </div>
                  <span
                    className="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize"
                    style={{
                      backgroundColor:
                        rfc.status === "approved"
                          ? "color-mix(in oklch, var(--success) 15%, transparent)"
                          : rfc.status === "in_review"
                          ? "color-mix(in oklch, var(--warning) 15%, transparent)"
                          : "color-mix(in oklch, var(--muted-foreground) 15%, transparent)",
                      color:
                        rfc.status === "approved"
                          ? "var(--success)"
                          : rfc.status === "in_review"
                          ? "var(--warning)"
                          : "var(--muted-foreground)",
                    }}
                  >
                    {rfc.status.replace("_", " ")}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* My Reviews */}
        <div
          className="rounded-xl border"
          style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
        >
          <div className="flex items-center justify-between border-b p-4" style={{ borderColor: "var(--border)" }}>
            <h2 className="text-sm font-semibold">My Pending Reviews</h2>
            <button
              onClick={() => router.push("/reviews")}
              className="inline-flex items-center gap-1 text-xs"
              style={{ color: "var(--primary)" }}
            >
              View all <ArrowRight className="h-3 w-3" />
            </button>
          </div>
          <div className="divide-y" style={{ borderColor: "var(--border)" }}>
            {myReviews.filter((r) => r.status === "pending").length === 0 ? (
              <p className="p-4 text-sm" style={{ color: "var(--muted-foreground)" }}>
                No pending reviews. You're all caught up!
              </p>
            ) : (
              myReviews
                .filter((r) => r.status === "pending")
                .slice(0, 5)
                .map((review) => (
                  <button
                    key={review.id}
                    onClick={() => router.push(`/rfcs/${review.rfc_id}`)}
                    className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-muted/50"
                  >
                    <div>
                      <span className="text-sm font-medium">{review.team}</span>
                      {review.deadline && (
                        <div className="mt-1 flex items-center gap-1 text-xs" style={{ color: "var(--muted-foreground)" }}>
                          <Clock className="h-3 w-3" />
                          Due {formatRelative(review.deadline)}
                        </div>
                      )}
                    </div>
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: "color-mix(in oklch, var(--warning) 15%, transparent)",
                        color: "var(--warning)",
                      }}
                    >
                      Pending
                    </span>
                  </button>
                ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
