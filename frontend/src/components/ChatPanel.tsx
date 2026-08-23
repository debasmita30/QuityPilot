import { useRef, useState } from "react";
import { sendMessage, type PendingAction, type Session, type ToolTraceEntry } from "../lib/api";
import { ToolTrace } from "./ToolTrace";
import { PendingActionCard } from "./PendingActionCard";

interface Turn {
  role: "user" | "assistant";
  text: string;
  trace?: ToolTraceEntry[];
  pendingAction?: PendingAction | null;
  pendingResolution?: "confirmed" | "cancelled";
}

const SUGGESTIONS = [
  "Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.",
  "Should LumenWorks get a service credit for ORD-2002?",
  "What severity is TKT-501 and is it within its response target?",
  "Does KI-211 explain why TKT-504's order still shows BOOKED?",
];

export function ChatPanel({ session }: { session: Session }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  async function submit(text: string) {
    if (!text.trim() || loading) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await sendMessage(session, text, conversationId);
      setConversationId(res.conversation_id);
      setTurns((t) => [
        ...t,
        { role: "assistant", text: res.reply, trace: res.trace, pendingAction: res.pending_action },
      ]);
    } catch (e) {
      setTurns((t) => [...t, { role: "assistant", text: `Request failed: ${String(e)}` }]);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => listRef.current?.scrollTo(0, listRef.current.scrollHeight));
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div ref={listRef} className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-5">
        {turns.length === 0 && (
          <div className="max-w-2xl mx-auto mt-10 text-center">
            <div className="font-mono text-[11px] tracking-[0.3em] text-signal mb-3">
              MANIFEST CLEAR — READY FOR REQUESTS
            </div>
            <p className="text-muted text-sm mb-6">
              Signed in as {session.display_name} ·{" "}
              {session.persona === "internal" ? `internal, ${session.role}` : `customer account`}
            </p>
            <div className="grid gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="text-left text-sm border border-line bg-panel glass shadow-sm shadow-black/5 hover:border-signal/50 rounded-lg px-4 py-3 text-paper/90 transition"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {turns.map((turn, i) => (
          <div key={i} className={turn.role === "user" ? "flex justify-end" : "flex justify-start"}>
            {turn.role === "user" ? (
              <div className="max-w-xl bg-panel-raised glass shadow-sm shadow-black/5 border border-line rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm text-paper">
                {turn.text}
              </div>
            ) : (
              <div className="max-w-2xl w-full">
                {turn.trace && <ToolTrace trace={turn.trace} />}
                <div className="bg-panel glass shadow-sm shadow-black/5 border border-line rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-paper whitespace-pre-wrap leading-relaxed">
                  {turn.text}
                </div>
                {turn.pendingAction && !turn.pendingResolution && (
                  <PendingActionCard
                    session={session}
                    action={turn.pendingAction}
                    onResolved={(status) =>
                      setTurns((prev) =>
                        prev.map((t, idx) => (idx === i ? { ...t, pendingResolution: status } : t))
                      )
                    }
                  />
                )}
                {turn.pendingResolution && (
                  <div className="font-mono text-[11px] text-muted mt-2 px-1">
                    {turn.pendingResolution === "confirmed" ? "✓ escalation created" : "✕ cancelled"}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-muted text-xs font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-signal pulse-dot" />
            reasoning across tools…
          </div>
        )}
      </div>

      <div className="border-t border-line bg-panel-raised glass px-6 py-4">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit(input)}
            placeholder="Ask about a policy, order, ticket, or escalation…"
            className="flex-1 bg-panel glass shadow-sm shadow-black/5 border border-line rounded-lg px-4 py-2.5 text-sm text-paper outline-none focus:border-signal"
          />
          <button
            onClick={() => submit(input)}
            disabled={loading}
            className="bg-signal text-ink text-sm font-semibold rounded-lg px-5 py-2.5 hover:brightness-110 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
