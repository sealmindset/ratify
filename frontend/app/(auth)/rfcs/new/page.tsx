"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AIResponse } from "@/lib/types";
import { Bot, Send, Loader2, FileText, Sparkles } from "lucide-react";

const RFC_TYPES = [
  { value: "infrastructure", label: "Infrastructure", description: "Network, compute, storage, DR/failover" },
  { value: "security", label: "Security", description: "Auth, encryption, compliance, threat model" },
  { value: "architecture", label: "Architecture", description: "System design, API contracts, data model" },
  { value: "process", label: "Process", description: "Workflows, procedures, team processes" },
  { value: "integration", label: "Integration", description: "System connections, data flows, APIs" },
  { value: "data", label: "Data", description: "Schemas, pipelines, governance, analytics" },
  { value: "other", label: "Other", description: "Anything that doesn't fit above" },
];

interface Message {
  role: "user" | "assistant";
  content: string;
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

  const canInterview = hasPermission("ai", "interview");

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
      setMessages([{ role: "assistant", content: resp.message }]);
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
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setSending(true);

    try {
      const resp = await apiPost<AIResponse>(
        `/ai/interview/${conversationId}/message`,
        { message: userMsg }
      );
      setMessages((prev) => [...prev, { role: "assistant", content: resp.message }]);

      if (resp.sections_generated) {
        setStep("complete");
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I had trouble processing that. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  // Setup step: title and type
  if (step === "setup") {
    return (
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Create New RFC</h1>
          <p style={{ color: "var(--muted-foreground)" }}>
            Start an AI-guided interview to build your RFC. The AI will ask targeted questions based on your RFC type.
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
              This determines which questions the AI will ask.
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
              You don't have permission to use the AI interview feature.
            </p>
          )}
        </div>
      </div>
    );
  }

  // Interview complete
  if (step === "complete") {
    return (
      <div className="mx-auto max-w-2xl space-y-6 text-center">
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
    <div className="mx-auto flex max-w-3xl flex-col" style={{ height: "calc(100vh - 8rem)" }}>
      <div className="shrink-0 pb-4">
        <h1 className="text-lg font-bold tracking-tight">AI Interview: {title}</h1>
        <p className="text-xs" style={{ color: "var(--muted-foreground)" }}>
          Answer the questions below. The AI will adapt based on your responses.
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
            <div
              className="max-w-[80%] rounded-lg px-4 py-3 text-sm"
              style={{
                backgroundColor: msg.role === "user" ? "var(--primary)" : "var(--card)",
                color: msg.role === "user" ? "var(--primary-foreground)" : "var(--card-foreground)",
                borderColor: msg.role === "user" ? undefined : "var(--border)",
                borderWidth: msg.role === "user" ? undefined : "1px",
              }}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}
        {sending && (
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
              <Loader2 className="h-4 w-4 animate-spin" style={{ color: "var(--muted-foreground)" }} />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 border-t pt-4" style={{ borderColor: "var(--border)" }}>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
            placeholder="Type your answer..."
            className="flex-1 rounded-md border px-3 py-2 text-sm"
            style={{ borderColor: "var(--input)", backgroundColor: "var(--background)" }}
            disabled={sending}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || sending}
            className="rounded-md px-4 py-2 transition-colors disabled:opacity-50"
            style={{ backgroundColor: "var(--primary)", color: "var(--primary-foreground)" }}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
