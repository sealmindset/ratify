"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiGet, apiPost, apiPatch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate, formatRelative } from "@/lib/utils";
import type { RFC, Comment as CommentType, ReviewAssignment, SignOff } from "@/lib/types";
import {
  FileText, Edit, MessageSquare, Users, CheckCircle, CheckCircle2,
  Clock, ExternalLink, Send, Link2, Loader2, Reply, X, RotateCcw,
  ChevronDown, ChevronRight,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* Inline-commentable section renderer                                 */
/* ------------------------------------------------------------------ */

function SectionContent({
  section,
  comments,
  onSelectText,
  onClickComment,
  activeCommentId,
}: {
  section: { id: string; content: string | null };
  comments: CommentType[];
  onSelectText: (sectionId: string, quoted: string, offset: number, length: number) => void;
  onClickComment: (commentId: string) => void;
  activeCommentId: string | null;
}) {
  const contentRef = useRef<HTMLDivElement>(null);

  const handleMouseUp = () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !contentRef.current) return;

    const range = sel.getRangeAt(0);
    if (!contentRef.current.contains(range.commonAncestorContainer)) return;

    const text = sel.toString().trim();
    if (!text) return;

    // Calculate offset relative to the full text content
    const preRange = document.createRange();
    preRange.selectNodeContents(contentRef.current);
    preRange.setEnd(range.startContainer, range.startOffset);
    const offset = preRange.toString().length;

    onSelectText(section.id, text, offset, text.length);
    sel.removeAllRanges();
  };

  // Build highlighted content with inline comment markers
  const rawContent = section.content || "No content yet.";
  const inlineComments = comments
    .filter((c) => c.quoted_text && c.anchor_offset !== null && c.anchor_length !== null)
    .sort((a, b) => (a.anchor_offset ?? 0) - (b.anchor_offset ?? 0));

  const renderContent = () => {
    if (inlineComments.length === 0) {
      return <span>{rawContent}</span>;
    }

    const parts: React.ReactNode[] = [];
    let lastEnd = 0;

    for (const comment of inlineComments) {
      const start = comment.anchor_offset!;
      const end = start + comment.anchor_length!;

      // Clamp to valid range
      if (start > rawContent.length || end > rawContent.length) continue;
      if (start < lastEnd) continue; // overlapping -- skip

      // Text before this highlight
      if (start > lastEnd) {
        parts.push(<span key={`t-${lastEnd}`}>{rawContent.slice(lastEnd, start)}</span>);
      }

      // Highlighted span
      const isActive = activeCommentId === comment.id;
      parts.push(
        <span
          key={`h-${comment.id}`}
          onClick={(e) => { e.stopPropagation(); onClickComment(comment.id); }}
          className="cursor-pointer border-b-2 transition-colors"
          style={{
            backgroundColor: comment.is_resolved
              ? "color-mix(in oklch, var(--muted) 40%, transparent)"
              : isActive
                ? "color-mix(in oklch, var(--warning) 30%, transparent)"
                : "color-mix(in oklch, var(--warning) 15%, transparent)",
            borderColor: comment.is_resolved ? "var(--muted-foreground)" : "var(--warning)",
            textDecoration: comment.is_resolved ? "line-through" : "none",
            opacity: comment.is_resolved ? 0.6 : 1,
          }}
          title={`${comment.author_name}: ${comment.content.slice(0, 80)}${comment.content.length > 80 ? "..." : ""}`}
        >
          {rawContent.slice(start, end)}
        </span>,
      );
      lastEnd = end;
    }

    // Remaining text
    if (lastEnd < rawContent.length) {
      parts.push(<span key={`t-${lastEnd}`}>{rawContent.slice(lastEnd)}</span>);
    }

    return <>{parts}</>;
  };

  return (
    <div
      ref={contentRef}
      onMouseUp={handleMouseUp}
      className="mt-2 whitespace-pre-wrap text-sm leading-relaxed select-text"
      style={{ color: "var(--muted-foreground)", cursor: "text" }}
    >
      {renderContent()}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Comment thread component (recursive)                                */
/* ------------------------------------------------------------------ */

function CommentThread({
  comment,
  rfcId,
  currentUserId,
  canComment,
  depth,
  onRefresh,
  isActive,
  onActivate,
}: {
  comment: CommentType;
  rfcId: string;
  currentUserId: string;
  canComment: boolean;
  depth: number;
  onRefresh: () => void;
  isActive: boolean;
  onActivate: (id: string) => void;
}) {
  const [replying, setReplying] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [collapsed, setCollapsed] = useState(comment.is_resolved);

  const handleReply = async () => {
    if (!replyText.trim()) return;
    setSubmitting(true);
    try {
      await apiPost(`/rfcs/${rfcId}/comments`, {
        section_id: comment.section_id,
        content: replyText.trim(),
        parent_id: comment.id,
      });
      setReplyText("");
      setReplying(false);
      onRefresh();
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolve = async () => {
    await apiPatch(`/rfcs/${rfcId}/comments/${comment.id}/resolve`);
    onRefresh();
  };

  const handleUnresolve = async () => {
    await apiPatch(`/rfcs/${rfcId}/comments/${comment.id}/unresolve`);
    onRefresh();
  };

  return (
    <div
      className={`rounded-lg border p-3 transition-all ${isActive ? "ring-2 ring-yellow-500" : ""}`}
      style={{
        backgroundColor: comment.is_resolved
          ? "color-mix(in oklch, var(--muted) 30%, var(--card))"
          : "var(--card)",
        borderColor: isActive ? "var(--warning)" : "var(--border)",
        marginLeft: depth > 0 ? `${depth * 16}px` : undefined,
        opacity: comment.is_resolved ? 0.75 : 1,
      }}
      onClick={() => onActivate(comment.id)}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {comment.replies.length > 0 && (
            <button onClick={(e) => { e.stopPropagation(); setCollapsed(!collapsed); }} className="shrink-0">
              {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
          )}
          <span className="text-sm font-medium truncate">{comment.author_name}</span>
          <span className="text-xs shrink-0" style={{ color: "var(--muted-foreground)" }}>
            {formatRelative(comment.created_at)}
          </span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {comment.is_resolved ? (
            <button
              onClick={(e) => { e.stopPropagation(); handleUnresolve(); }}
              className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs"
              style={{ color: "var(--success)" }}
              title={`Resolved by ${comment.resolved_by_name}`}
            >
              <CheckCircle2 className="h-3 w-3" /> Resolved
            </button>
          ) : (
            canComment && !comment.parent_id && (
              <button
                onClick={(e) => { e.stopPropagation(); handleResolve(); }}
                className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs hover:bg-[var(--muted)]"
                style={{ color: "var(--muted-foreground)" }}
              >
                <CheckCircle className="h-3 w-3" /> Resolve
              </button>
            )
          )}
        </div>
      </div>

      {/* Quoted text */}
      {comment.quoted_text && !comment.parent_id && (
        <div
          className="mt-1.5 rounded border-l-2 px-2 py-1 text-xs italic"
          style={{
            borderColor: "var(--warning)",
            backgroundColor: "color-mix(in oklch, var(--warning) 8%, transparent)",
            color: "var(--muted-foreground)",
          }}
        >
          &ldquo;{comment.quoted_text.length > 120 ? comment.quoted_text.slice(0, 120) + "..." : comment.quoted_text}&rdquo;
        </div>
      )}

      {/* Comment body */}
      <div className="mt-1.5 whitespace-pre-wrap text-sm">{comment.content}</div>

      {/* References */}
      {comment.references.length > 0 && (
        <div className="mt-1.5 space-y-0.5">
          {comment.references.map((ref) => (
            <a
              key={ref.id}
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs underline"
              style={{ color: "var(--primary)" }}
            >
              <Link2 className="h-3 w-3" /> {ref.title}
            </a>
          ))}
        </div>
      )}

      {/* Reply button */}
      {canComment && !comment.is_resolved && (
        <div className="mt-2">
          {!replying ? (
            <button
              onClick={(e) => { e.stopPropagation(); setReplying(true); }}
              className="inline-flex items-center gap-1 text-xs"
              style={{ color: "var(--primary)" }}
            >
              <Reply className="h-3 w-3" /> Reply
            </button>
          ) : (
            <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Write a reply..."
                rows={2}
                autoFocus
                className="w-full rounded-md border px-2 py-1.5 text-sm"
                style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleReply();
                }}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleReply}
                  disabled={!replyText.trim() || submitting}
                  className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium disabled:opacity-50"
                  style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
                >
                  {submitting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                  Reply
                </button>
                <button
                  onClick={() => { setReplying(false); setReplyText(""); }}
                  className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs"
                  style={{ color: "var(--muted-foreground)" }}
                >
                  <X className="h-3 w-3" /> Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Nested replies */}
      {!collapsed && comment.replies.length > 0 && (
        <div className="mt-2 space-y-2">
          {comment.replies.map((reply) => (
            <CommentThread
              key={reply.id}
              comment={reply}
              rfcId={rfcId}
              currentUserId={currentUserId}
              canComment={canComment}
              depth={0}
              onRefresh={onRefresh}
              isActive={false}
              onActivate={onActivate}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main page                                                           */
/* ------------------------------------------------------------------ */

export default function RFCDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { authMe, hasPermission } = useAuth();
  const rfcId = params.id as string;

  const [rfc, setRfc] = useState<RFC | null>(null);
  const [comments, setComments] = useState<CommentType[]>([]);
  const [reviews, setReviews] = useState<ReviewAssignment[]>([]);
  const [signoffs, setSignoffs] = useState<SignOff[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"sections" | "comments" | "reviews">("sections");

  // Inline comment state
  const [activeCommentId, setActiveCommentId] = useState<string | null>(null);
  const [showResolved, setShowResolved] = useState(false);
  const [inlineSelection, setInlineSelection] = useState<{
    sectionId: string;
    quotedText: string;
    offset: number;
    length: number;
  } | null>(null);
  const [newComment, setNewComment] = useState("");
  const [commentSectionId, setCommentSectionId] = useState<string | null>(null);
  const [refUrl, setRefUrl] = useState("");
  const [refTitle, setRefTitle] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  const canEdit = hasPermission("rfcs", "update");
  const canComment = hasPermission("comments", "create");

  const fetchData = useCallback(async () => {
    try {
      const [rfcData, commentsData, reviewsData, signoffsData] = await Promise.all([
        apiGet<RFC>(`/rfcs/${rfcId}`),
        apiGet<CommentType[]>(`/rfcs/${rfcId}/comments`),
        apiGet<ReviewAssignment[]>(`/rfcs/${rfcId}/reviews`),
        apiGet<SignOff[]>(`/rfcs/${rfcId}/reviews/signoffs`),
      ]);
      setRfc(rfcData);
      setComments(commentsData);
      setReviews(reviewsData);
      setSignoffs(signoffsData);
    } catch (err) {
      console.error("Failed to load RFC:", err);
    } finally {
      setLoading(false);
    }
  }, [rfcId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSelectText = (sectionId: string, quoted: string, offset: number, length: number) => {
    if (!canComment) return;
    setInlineSelection({ sectionId, quotedText: quoted, offset, length });
    setCommentSectionId(sectionId);
    setNewComment("");
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    setSubmittingComment(true);
    try {
      const refs = refUrl.trim()
        ? [{ url: refUrl.trim(), title: refTitle.trim() || refUrl.trim(), ref_type: "link" }]
        : [];
      await apiPost(`/rfcs/${rfcId}/comments`, {
        section_id: commentSectionId || inlineSelection?.sectionId || null,
        content: newComment.trim(),
        quoted_text: inlineSelection?.quotedText || null,
        anchor_offset: inlineSelection?.offset ?? null,
        anchor_length: inlineSelection?.length ?? null,
        references: refs,
      });
      setNewComment("");
      setRefUrl("");
      setRefTitle("");
      setCommentSectionId(null);
      setInlineSelection(null);
      fetchData();
    } catch (err) {
      console.error("Failed to add comment:", err);
    } finally {
      setSubmittingComment(false);
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

  const statusColor = {
    draft: "var(--muted-foreground)",
    in_review: "var(--warning)",
    approved: "var(--success)",
    rejected: "var(--destructive)",
    implemented: "var(--primary)",
    archived: "var(--muted-foreground)",
  }[rfc.status] || "var(--muted-foreground)";

  // Flatten all comments (including nested) for inline highlighting
  const flattenComments = (cs: CommentType[]): CommentType[] => {
    const result: CommentType[] = [];
    for (const c of cs) {
      result.push(c);
      if (c.replies?.length) result.push(...flattenComments(c.replies));
    }
    return result;
  };
  const allComments = flattenComments(comments);

  // Get comment count including replies
  const totalCommentCount = allComments.length;

  // Filter visible comments for the sidebar
  const visibleComments = showResolved ? comments : comments.filter((c) => !c.is_resolved);

  // Get section-specific comments for inline display
  const sectionComments = (sectionId: string) =>
    allComments.filter((c) => c.section_id === sectionId && !c.parent_id);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm" style={{ color: "var(--muted-foreground)" }}>
              RFC-{rfc.rfc_number}
            </span>
            <span
              className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize"
              style={{
                backgroundColor: `color-mix(in oklch, ${statusColor} 15%, transparent)`,
                color: statusColor,
              }}
            >
              {rfc.status.replace("_", " ")}
            </span>
            <span className="text-xs" style={{ color: "var(--muted-foreground)" }}>
              {rfc.rfc_type}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">{rfc.title}</h1>
          <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>
            By {rfc.author_name} &middot; Created {formatDate(rfc.created_at)} &middot; Updated {formatRelative(rfc.updated_at)}
          </p>
          {rfc.jira_epic_key && (
            <div className="flex items-center gap-1 text-xs" style={{ color: "var(--primary)" }}>
              <ExternalLink className="h-3 w-3" />
              Jira: {rfc.jira_epic_key}
            </div>
          )}
        </div>
        <div className="flex gap-2">
          {canEdit && (
            <button
              onClick={() => router.push(`/rfcs/${rfcId}/edit`)}
              className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm"
              style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
            >
              <Edit className="h-4 w-4" /> Edit
            </button>
          )}
          {hasPermission("jira", "sync") && (
            <button
              onClick={async () => {
                await apiPost(`/rfcs/${rfcId}/jira/sync`);
                fetchData();
              }}
              className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm"
              style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
            >
              Sync to Jira
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      {rfc.summary && (
        <div
          className="rounded-lg border p-4"
          style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
        >
          <p className="text-sm">{rfc.summary}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b" style={{ borderColor: "var(--border)" }}>
        {[
          { key: "sections", label: "Sections", icon: FileText, count: rfc.sections.length },
          { key: "comments", label: "Comments", icon: MessageSquare, count: totalCommentCount },
          { key: "reviews", label: "Reviews & Sign-offs", icon: Users, count: reviews.length + signoffs.length },
        ].map(({ key, label, icon: Icon, count }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as typeof activeTab)}
            className="inline-flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors"
            style={{
              borderColor: activeTab === key ? "var(--primary)" : "transparent",
              color: activeTab === key ? "var(--primary)" : "var(--muted-foreground)",
            }}
          >
            <Icon className="h-4 w-4" />
            {label}
            <span
              className="rounded-full px-1.5 py-0.5 text-xs"
              style={{ backgroundColor: "var(--muted)", color: "var(--muted-foreground)" }}
            >
              {count}
            </span>
          </button>
        ))}
      </div>

      {/* ============================================================ */}
      {/* Sections tab -- with inline comments                          */}
      {/* ============================================================ */}
      {activeTab === "sections" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Sections column */}
          <div className="lg:col-span-2 space-y-4">
            {canComment && (
              <div className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs"
                style={{ backgroundColor: "color-mix(in oklch, var(--primary) 5%, var(--card))", borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
                <MessageSquare className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--primary)" }} />
                Select text in any section to leave an inline comment
              </div>
            )}

            {rfc.sections.map((section) => {
              const secComments = sectionComments(section.id);
              const unresolvedCount = secComments.filter((c) => !c.is_resolved).length;

              return (
                <div
                  key={section.id}
                  className="rounded-lg border p-4"
                  style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{section.title}</h3>
                    <div className="flex items-center gap-2">
                      {unresolvedCount > 0 && (
                        <span
                          className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
                          style={{ backgroundColor: "color-mix(in oklch, var(--warning) 15%, transparent)", color: "var(--warning)" }}
                        >
                          <MessageSquare className="h-3 w-3" /> {unresolvedCount}
                        </span>
                      )}
                      <span
                        className="rounded px-2 py-0.5 text-xs"
                        style={{ backgroundColor: "var(--muted)", color: "var(--muted-foreground)" }}
                      >
                        {section.section_type}
                      </span>
                    </div>
                  </div>

                  <SectionContent
                    section={section}
                    comments={secComments}
                    onSelectText={handleSelectText}
                    onClickComment={(id) => setActiveCommentId(id === activeCommentId ? null : id)}
                    activeCommentId={activeCommentId}
                  />

                  {canComment && (
                    <button
                      onClick={() => {
                        setCommentSectionId(section.id);
                        setInlineSelection(null);
                        setActiveTab("comments");
                      }}
                      className="mt-2 inline-flex items-center gap-1 text-xs"
                      style={{ color: "var(--primary)" }}
                    >
                      <MessageSquare className="h-3 w-3" /> Comment on this section
                    </button>
                  )}
                </div>
              );
            })}

            {rfc.sections.length === 0 && (
              <p className="py-8 text-center text-sm" style={{ color: "var(--muted-foreground)" }}>
                No sections yet. Start an AI interview or add sections manually.
              </p>
            )}
          </div>

          {/* Comment sidebar */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Comments</h3>
              <button
                onClick={() => setShowResolved(!showResolved)}
                className="inline-flex items-center gap-1 text-xs"
                style={{ color: "var(--muted-foreground)" }}
              >
                {showResolved ? "Hide resolved" : "Show resolved"}
              </button>
            </div>

            {/* Inline comment creation popover */}
            {inlineSelection && canComment && (
              <div
                className="rounded-lg border p-3 space-y-2"
                style={{ backgroundColor: "var(--card)", borderColor: "var(--warning)" }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium" style={{ color: "var(--warning)" }}>
                    New inline comment
                  </span>
                  <button onClick={() => setInlineSelection(null)}>
                    <X className="h-3.5 w-3.5" style={{ color: "var(--muted-foreground)" }} />
                  </button>
                </div>
                <div
                  className="rounded border-l-2 px-2 py-1 text-xs italic"
                  style={{
                    borderColor: "var(--warning)",
                    backgroundColor: "color-mix(in oklch, var(--warning) 8%, transparent)",
                    color: "var(--muted-foreground)",
                  }}
                >
                  &ldquo;{inlineSelection.quotedText.length > 100
                    ? inlineSelection.quotedText.slice(0, 100) + "..."
                    : inlineSelection.quotedText}&rdquo;
                </div>
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add your comment..."
                  rows={3}
                  autoFocus
                  className="w-full rounded-md border px-2 py-1.5 text-sm"
                  style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleAddComment();
                  }}
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddComment}
                    disabled={!newComment.trim() || submittingComment}
                    className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium disabled:opacity-50"
                    style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
                  >
                    {submittingComment ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                    Post
                  </button>
                  <button
                    onClick={() => setInlineSelection(null)}
                    className="text-xs"
                    style={{ color: "var(--muted-foreground)" }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Comment threads */}
            {visibleComments.length === 0 ? (
              <p className="py-4 text-center text-xs" style={{ color: "var(--muted-foreground)" }}>
                No comments yet. Select text in a section to start.
              </p>
            ) : (
              <div className="space-y-2">
                {visibleComments.map((comment) => (
                  <CommentThread
                    key={comment.id}
                    comment={comment}
                    rfcId={rfcId}
                    currentUserId={authMe?.user_id || ""}
                    canComment={canComment}
                    depth={0}
                    onRefresh={fetchData}
                    isActive={activeCommentId === comment.id}
                    onActivate={(id) => setActiveCommentId(id === activeCommentId ? null : id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* Comments tab -- full list with threading                      */}
      {/* ============================================================ */}
      {activeTab === "comments" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowResolved(!showResolved)}
                className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs"
                style={{ borderColor: "var(--input)", backgroundColor: "var(--background)", color: "var(--muted-foreground)" }}
              >
                {showResolved ? <CheckCircle2 className="h-3 w-3" /> : <RotateCcw className="h-3 w-3" />}
                {showResolved ? "Hide resolved" : "Show resolved"}
              </button>
            </div>
          </div>

          {visibleComments.map((comment) => (
            <CommentThread
              key={comment.id}
              comment={comment}
              rfcId={rfcId}
              currentUserId={authMe?.user_id || ""}
              canComment={canComment}
              depth={0}
              onRefresh={fetchData}
              isActive={activeCommentId === comment.id}
              onActivate={(id) => setActiveCommentId(id === activeCommentId ? null : id)}
            />
          ))}

          {canComment && (
            <div
              className="rounded-lg border p-4 space-y-3"
              style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
            >
              <h4 className="text-sm font-medium">Add Comment</h4>
              {commentSectionId && (
                <div className="flex items-center gap-2 text-xs" style={{ color: "var(--primary)" }}>
                  <FileText className="h-3 w-3" />
                  Commenting on: {rfc.sections.find((s) => s.id === commentSectionId)?.title}
                  <button onClick={() => setCommentSectionId(null)} className="underline">Clear</button>
                </div>
              )}
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write your comment..."
                rows={3}
                className="w-full rounded-md border px-3 py-2 text-sm"
                style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleAddComment();
                }}
              />
              <div className="flex gap-2">
                <input
                  type="text"
                  value={refUrl}
                  onChange={(e) => setRefUrl(e.target.value)}
                  placeholder="Reference URL (optional)"
                  className="flex-1 rounded-md border px-3 py-1.5 text-xs"
                  style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                />
                <input
                  type="text"
                  value={refTitle}
                  onChange={(e) => setRefTitle(e.target.value)}
                  placeholder="Reference title"
                  className="flex-1 rounded-md border px-3 py-1.5 text-xs"
                  style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
                />
              </div>
              <button
                onClick={handleAddComment}
                disabled={!newComment.trim() || submittingComment}
                className="inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50"
                style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
              >
                {submittingComment ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Post Comment
              </button>
            </div>
          )}
        </div>
      )}

      {/* ============================================================ */}
      {/* Reviews tab                                                   */}
      {/* ============================================================ */}
      {activeTab === "reviews" && (
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-semibold mb-3">Review Assignments</h3>
            {reviews.length === 0 ? (
              <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>No review assignments yet.</p>
            ) : (
              <div className="space-y-2">
                {reviews.map((r) => (
                  <div
                    key={r.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                    style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
                  >
                    <div>
                      <span className="text-sm font-medium">{r.reviewer_name}</span>
                      <span className="ml-2 text-xs" style={{ color: "var(--muted-foreground)" }}>
                        {r.team}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      {r.deadline && (
                        <span className="flex items-center gap-1 text-xs" style={{ color: "var(--muted-foreground)" }}>
                          <Clock className="h-3 w-3" /> {formatDate(r.deadline)}
                        </span>
                      )}
                      <span
                        className="rounded-full px-2 py-0.5 text-xs font-medium capitalize"
                        style={{
                          backgroundColor:
                            r.status === "completed"
                              ? "color-mix(in oklch, var(--success) 15%, transparent)"
                              : "color-mix(in oklch, var(--warning) 15%, transparent)",
                          color: r.status === "completed" ? "var(--success)" : "var(--warning)",
                        }}
                      >
                        {r.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-3">Sign-offs</h3>
            {signoffs.length === 0 ? (
              <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>No sign-offs requested yet.</p>
            ) : (
              <div className="space-y-2">
                {signoffs.map((s) => (
                  <div
                    key={s.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                    style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
                  >
                    <div>
                      <span className="text-sm font-medium">{s.signer_name}</span>
                      <span className="ml-2 text-xs" style={{ color: "var(--muted-foreground)" }}>
                        {s.team}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {s.status === "approved" && <CheckCircle className="h-4 w-4" style={{ color: "var(--success)" }} />}
                      <span
                        className="rounded-full px-2 py-0.5 text-xs font-medium capitalize"
                        style={{
                          backgroundColor:
                            s.status === "approved"
                              ? "color-mix(in oklch, var(--success) 15%, transparent)"
                              : s.status === "rejected"
                              ? "color-mix(in oklch, var(--destructive) 15%, transparent)"
                              : "color-mix(in oklch, var(--warning) 15%, transparent)",
                          color:
                            s.status === "approved"
                              ? "var(--success)"
                              : s.status === "rejected"
                              ? "var(--destructive)"
                              : "var(--warning)",
                        }}
                      >
                        {s.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
