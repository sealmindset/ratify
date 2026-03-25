"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AIResponse } from "@/lib/types";
import {
  Bot, Send, Loader2, FileText, Sparkles, CheckCircle2, Circle,
  MessageSquare, Clock,
} from "lucide-react";

const RFC_TYPES = [
  { value: "infrastructure", label: "Infrastructure", description: "Network, compute, storage, DR/failover" },
  { value: "security", label: "Security", description: "Auth, encryption, compliance, threat model" },
  { value: "architecture", label: "Architecture", description: "System design, API contracts, data model" },
  { value: "process", label: "Process", description: "Workflows, procedures, team processes" },
  { value: "integration", label: "Integration", description: "System connections, data flows, APIs" },
  { value: "data", label: "Data", description: "Schemas, pipelines, governance, analytics" },
  { value: "other", label: "Other", description: "Anything that doesn't fit above" },
];

// Topic names per RFC type (matches backend _TOPICS keys)
const TOPIC_NAMES: Record<string, string[]> = {
  infrastructure: ["Current State", "Motivation", "Architecture", "Availability & DR", "Monitoring & SLAs", "Rollback Strategy", "Cost Impact", "Stakeholders"],
  security: ["Security Concern", "Threat Model", "Authentication", "Authorization", "Data Protection", "Compliance", "Audit & Monitoring", "Rollout Plan"],
  architecture: ["Current State & Vision", "Problem Statement", "Proposed Architecture", "API Contracts", "Data Model", "Scalability", "Technology Choices", "Risks & Trade-offs"],
  process: ["Process Overview", "Current Participants", "Pain Points", "Proposed Process", "Success Metrics", "Change Management", "Rollout Plan", "Rollback & Contingency"],
  integration: ["Systems & Business Need", "Data Specification", "Current State", "Integration Pattern", "Error Handling", "SLAs & Performance", "Monitoring", "Security"],
  data: ["Data Domain", "Data Sources", "Schema & Data Model", "Data Pipeline", "Data Quality", "Governance & Ownership", "Analytics & Reporting", "Risks"],
  other: ["Problem Statement", "Current State", "Proposed Solution", "Alternatives", "Risks", "Timeline & People", "Success Criteria", "Dependencies"],
};

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
        style={{ backgroundColor: "color-mix(in oklch, var(--primary) 15%, transparent)" }}
      >
        <Bot className="h-4 w-4" style={{ color: "var(--primary)" }} />
      </div>
      <div
        className="rounded-lg border px-4 py-3"
        style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full animate-bounce" style={{ backgroundColor: "var(--muted-foreground)", animationDelay: "0ms" }} />
          <span className="inline-block h-2 w-2 rounded-full animate-bounce" style={{ backgroundColor: "var(--muted-foreground)", animationDelay: "150ms" }} />
          <span className="inline-block h-2 w-2 rounded-full animate-bounce" style={{ backgroundColor: "var(--muted-foreground)", animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}

function TopicProgress({
  rfcType,
  topicsCovered,
}: {
  rfcType: string;
  topicsCovered: string[];
}) {
  const allTopics = TOPIC_NAMES[rfcType] || TOPIC_NAMES.other;
  const coveredCount = topicsCovered.length;
  const totalCount = allTopics.length;
  const pct = Math.round((coveredCount / totalCount) * 100);

  return (
    <div
      className="rounded-lg border p-3 space-y-2"
      style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium" style={{ color: "var(--muted-foreground)" }}>
          Interview Progress
        </span>
        <span className="text-xs font-semibold" style={{ color: "var(--primary)" }}>
          {coveredCount} / {totalCount} topics
        </span>
      </div>
      {/* Progress bar */}
      <div className="h-1.5 w-full rounded-full" style={{ backgroundColor: "var(--muted)" }}>
        <div
          className="h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: "var(--primary)" }}
        />
      </div>
      {/* Topic pills */}
      <div className="flex flex-wrap gap-1.5">
        {allTopics.map((topic) => {
          const isCovered = topicsCovered.includes(topic);
          return (
            <span
              key={topic}
              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium transition-all"
              style={{
                backgroundColor: isCovered
                  ? "color-mix(in oklch, var(--primary) 15%, transparent)"
                  : "var(--muted)",
                color: isCovered ? "var(--primary)" : "var(--muted-foreground)",
              }}
            >
              {isCovered ? (
                <CheckCircle2 className="h-2.5 w-2.5" />
              ) : (
                <Circle className="h-2.5 w-2.5" />
              )}
              {topic}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function InterviewSummary({ messages }: { messages: Message[] }) {
  const userMessages = messages.filter((m) => m.role === "user");
  const assistantMessages = messages.filter((m) => m.role === "assistant");

  return (
    <div
      className="rounded-lg border p-4 space-y-3"
      style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
    >
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <MessageSquare className="h-4 w-4" style={{ color: "var(--primary)" }} />
        Interview Summary
      </h3>
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-md p-2 text-center" style={{ backgroundColor: "var(--muted)" }}>
          <div className="text-lg font-bold">{assistantMessages.length}</div>
          <div className="text-[10px]" style={{ color: "var(--muted-foreground)" }}>Questions Asked</div>
        </div>
        <div className="rounded-md p-2 text-center" style={{ backgroundColor: "var(--muted)" }}>
          <div className="text-lg font-bold">{userMessages.length}</div>
          <div className="text-[10px]" style={{ color: "var(--muted-foreground)" }}>Answers Given</div>
        </div>
        <div className="rounded-md p-2 text-center" style={{ backgroundColor: "var(--muted)" }}>
          <div className="text-lg font-bold">
            {Math.round(userMessages.reduce((sum, m) => sum + m.content.split(/\s+/).length, 0) / Math.max(userMessages.length, 1))}
          </div>
          <div className="text-[10px]" style={{ color: "var(--muted-foreground)" }}>Avg Words/Answer</div>
        </div>
      </div>
    </div>
  );
}

export default function NewRFCPage() {
  const router = useRouter();
  const { hasPermission } = useAuth();
  const [step, setStep] = useState<"setup" | "interview" | "complete">("setup");
  const [title, setTitle] = useState("");
  const [rfcType, setRfcType] = useState("architecture");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [rfcId, setRfcId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [topicsCovered, setTopicsCovered] = useState<string[]>([]);
  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canInterview = hasPermission("ai", "interview");

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Reset height to auto to get the correct scrollHeight
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
  };

  const handleStartInterview = async () => {
    if (!title.trim()) return;
    setSending(true);
    try {
      const resp = await apiPost<AIResponse>("/ai/interview/start", {
        title: title.trim(),
        rfc_type: rfcType,
      });
      setConversationId(resp.conversation_id);
      setRfcId(resp.rfc_id);
      setMessages([{
        role: "assistant",
        content: resp.message,
        timestamp: new Date().toISOString(),
      }]);
      if (resp.topics_covered) setTopicsCovered(resp.topics_covered);
      if (resp.current_topic) setCurrentTopic(resp.current_topic);
      setStep("interview");
    } catch (err) {
      console.error("Failed to start interview:", err);
    } finally {
      setSending(false);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !conversationId) return;
    const userMsg = input.trim();
    setInput("");
    // Reset textarea height
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    setMessages((prev) => [...prev, {
      role: "user",
      content: userMsg,
      timestamp: new Date().toISOString(),
    }]);
    setSending(true);

    try {
      const resp = await apiPost<AIResponse>(
        `/ai/interview/${conversationId}/message`,
        { message: userMsg }
      );
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: resp.message,
        timestamp: new Date().toISOString(),
      }]);

      if (resp.topics_covered) setTopicsCovered(resp.topics_covered);
      if (resp.current_topic) setCurrentTopic(resp.current_topic);

      if (resp.sections_generated) {
        setStep("complete");
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I had trouble processing that. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Setup step: title and type
  if (step === "setup") {
    return (
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Create New RFC</h1>
          <p style={{ color: "var(--muted-foreground)" }}>
            Start an AI-guided interview to build your RFC. The AI will ask targeted questions based on your RFC type
            and adapt based on your answers.
          </p>
        </div>

        <div className="space-y-6">
          <div>
            <label className="text-sm font-medium">RFC Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Zero Trust Network Architecture for Oracle MSCA"
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
            />
          </div>

          <div>
            <label className="text-sm font-medium">RFC Type</label>
            <p className="mt-1 text-xs" style={{ color: "var(--muted-foreground)" }}>
              This determines the topics the AI will cover. It adapts questions based on your answers.
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3">
              {RFC_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setRfcType(type.value)}
                  className="rounded-lg border p-3 text-left transition-colors"
                  style={{
                    borderColor: rfcType === type.value
                      ? "var(--primary)"
                      : "var(--border)",
                    backgroundColor: rfcType === type.value
                      ? "color-mix(in oklch, var(--primary) 8%, transparent)"
                      : "var(--card)",
                  }}
                >
                  <div className="text-sm font-medium">{type.label}</div>
                  <div className="mt-0.5 text-xs" style={{ color: "var(--muted-foreground)" }}>
                    {type.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleStartInterview}
            disabled={!title.trim() || sending || !canInterview}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md px-4 py-3 text-sm font-medium shadow-sm transition-colors disabled:opacity-50"
            style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {sending ? "Starting interview..." : "Start AI Interview"}
          </button>

          {!canInterview && (
            <p className="text-sm" style={{ color: "var(--destructive)" }}>
              You don&apos;t have permission to use the AI interview feature.
            </p>
          )}
        </div>
      </div>
    );
  }

  // Interview complete
  if (step === "complete") {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="text-center space-y-4">
          <div
            className="mx-auto flex h-16 w-16 items-center justify-center rounded-full"
            style={{ backgroundColor: "color-mix(in oklch, var(--success) 15%, transparent)" }}
          >
            <FileText className="h-8 w-8" style={{ color: "var(--success)" }} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">RFC Generated!</h1>
          <p style={{ color: "var(--muted-foreground)" }}>
            The AI has generated all sections for your RFC based on the interview.
            You can now review, edit, and refine each section.
          </p>
        </div>

        {/* Interview summary */}
        <InterviewSummary messages={messages} />

        {/* Topic coverage final state */}
        <TopicProgress rfcType={rfcType} topicsCovered={topicsCovered} />

        <div className="flex justify-center gap-3">
          <button
            onClick={() => router.push(`/rfcs/${rfcId}`)}
            className="inline-flex items-center gap-2 rounded-md px-6 py-2 text-sm font-medium shadow-sm"
            style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
          >
            View RFC
          </button>
          <button
            onClick={() => router.push(`/rfcs/${rfcId}/edit`)}
            className="inline-flex items-center gap-2 rounded-md border px-6 py-2 text-sm font-medium"
            style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
          >
            Edit Sections
          </button>
        </div>
      </div>
    );
  }

  // Interview chat
  return (
    <div className="mx-auto flex max-w-4xl gap-4" style={{ height: "calc(100vh - 8rem)" }}>
      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        <div className="shrink-0 pb-3">
          <h1 className="text-lg font-bold tracking-tight">AI Interview: {title}</h1>
          <p className="text-xs" style={{ color: "var(--muted-foreground)" }}>
            Answer the questions below. The AI adapts based on your responses -- detailed answers help it skip redundant questions.
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
                  style={{ backgroundColor: "color-mix(in oklch, var(--primary) 15%, transparent)" }}
                >
                  <Bot className="h-4 w-4" style={{ color: "var(--primary)" }} />
                </div>
              )}
              <div className="max-w-[80%] space-y-1">
                <div
                  className="rounded-lg px-4 py-3 text-sm"
                  style={{
                    backgroundColor: msg.role === "user" ? "var(--primary)" : "var(--card)",
                    color: msg.role === "user" ? "var(--primary-foreground)" : "var(--card-foreground)",
                    borderColor: msg.role === "user" ? undefined : "var(--border)",
                    borderWidth: msg.role === "user" ? undefined : "1px",
                  }}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
                <div
                  className={`flex items-center gap-1 text-[10px] ${msg.role === "user" ? "justify-end" : ""}`}
                  style={{ color: "var(--muted-foreground)" }}
                >
                  <Clock className="h-2.5 w-2.5" />
                  {formatTime(msg.timestamp)}
                </div>
              </div>
            </div>
          ))}
          {sending && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="shrink-0 border-t pt-3" style={{ borderColor: "var(--border)" }}>
          <div className="flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Type your answer... (Shift+Enter for new line)"
              className="flex-1 rounded-md border px-3 py-2 text-sm resize-none"
              style={{ borderColor: "var(--input)", backgroundColor: "var(--background)", minHeight: "40px", maxHeight: "120px" }}
              rows={1}
              disabled={sending}
            />
            <button
              onClick={handleSendMessage}
              disabled={!input.trim() || sending}
              className="rounded-md px-4 py-2 transition-colors disabled:opacity-50 shrink-0"
              style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)", height: "40px" }}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Side panel: Progress tracker */}
      <div className="hidden lg:block w-72 shrink-0 space-y-3 overflow-y-auto">
        <TopicProgress rfcType={rfcType} topicsCovered={topicsCovered} />

        {currentTopic && (
          <div
            className="rounded-lg border p-3"
            style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
          >
            <span className="text-xs font-medium" style={{ color: "var(--muted-foreground)" }}>
              Currently discussing
            </span>
            <p className="text-sm font-semibold mt-0.5" style={{ color: "var(--primary)" }}>
              {currentTopic}
            </p>
          </div>
        )}

        <div
          className="rounded-lg border p-3 space-y-1"
          style={{ backgroundColor: "var(--card)", borderColor: "var(--border)" }}
        >
          <span className="text-xs font-medium" style={{ color: "var(--muted-foreground)" }}>
            Interview Stats
          </span>
          <div className="flex justify-between text-xs">
            <span style={{ color: "var(--muted-foreground)" }}>Questions asked</span>
            <span className="font-medium">{messages.filter((m) => m.role === "assistant").length}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span style={{ color: "var(--muted-foreground)" }}>Your answers</span>
            <span className="font-medium">{messages.filter((m) => m.role === "user").length}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
