import type { ToolTraceEntry } from "../lib/api";

const TOOL_LABELS: Record<string, string> = {
  search_documents: "DOC SEARCH",
  get_order: "ORDER LOOKUP",
  list_orders: "ORDER LOOKUP",
  get_ticket: "TICKET LOOKUP",
  list_tickets: "TICKET LOOKUP",
  get_account: "ACCOUNT LOOKUP",
  get_operational_signals: "SIGNALS SCAN",
  propose_escalation: "ESCALATION DRAFT",
};

function summarize(entry: ToolTraceEntry): string {
  const out = entry.output;
  if (out.error) return `denied: ${out.error}`;
  if (Array.isArray(out.results)) return `${out.results.length} source(s) matched`;
  if (out.order && typeof out.order === "object") return `order ${(out.order as { order_id: string }).order_id}`;
  if (out.orders) return `${(out.orders as unknown[]).length} order(s)`;
  if (out.ticket && typeof out.ticket === "object") return `ticket ${(out.ticket as { ticket_id: string }).ticket_id}`;
  if (out.tickets) return `${(out.tickets as unknown[]).length} ticket(s)`;
  if (out.account) return "account record";
  if (out.sla_risk) return `${(out.sla_risk as unknown[]).length} SLA signal(s)`;
  if (out.pending_action) return "awaiting confirmation";
  return "ok";
}

export function ToolTrace({ trace }: { trace: ToolTraceEntry[] }) {
  if (!trace.length) return null;
  return (
    <div className="flex flex-col gap-2 my-2">
      {trace.map((entry, i) => (
        <div key={i} className="relative">
          <div className="manifest-edge rounded-t-md bg-panel-raised glass shadow-sm shadow-black/5" />
          <div className="bg-panel-raised glass shadow-sm shadow-black/5 border-x border-line px-3 py-2 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-1.5 h-1.5 rounded-full bg-route shrink-0" />
              <span className="font-mono text-[11px] tracking-wider text-route shrink-0">
                {TOOL_LABELS[entry.tool] ?? entry.tool.toUpperCase()}
              </span>
              <span className="text-xs text-muted truncate">{summarize(entry)}</span>
            </div>
            <span className="font-mono text-[10px] text-muted shrink-0">#{String(i + 1).padStart(2, "0")}</span>
          </div>
          <div className="manifest-edge rounded-b-md bg-panel-raised glass shadow-sm shadow-black/5" />
        </div>
      ))}
    </div>
  );
}
