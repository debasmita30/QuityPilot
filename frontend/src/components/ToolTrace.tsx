import { useState } from "react";
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

interface DocResult {
  doc_id: string;
  title: string;
  status: string;
  scope: string;
  heading: string;
  relevance: number;
}

interface OrderRecord {
  order_id: string;
  status: string;
  carrier: string;
  shipment_fee_inr: number;
  carrier_fault: boolean;
  customer_fault: boolean;
}

interface TicketRecord {
  ticket_id: string;
  status: string;
  subject: string;
}

function summarize(entry: ToolTraceEntry): string {
  const out = entry.output;
  if (out.error) return `denied: ${out.error}`;
  if (Array.isArray(out.results)) return `${out.results.length} source(s) matched`;
  if (out.order && typeof out.order === "object") return `order ${(out.order as OrderRecord).order_id}`;
  if (out.orders) return `${(out.orders as unknown[]).length} order(s)`;
  if (out.ticket && typeof out.ticket === "object") return `ticket ${(out.ticket as TicketRecord).ticket_id}`;
  if (out.tickets) return `${(out.tickets as unknown[]).length} ticket(s)`;
  if (out.account) return "account record";
  if (out.sla_risk) return `${(out.sla_risk as unknown[]).length} SLA signal(s)`;
  if (out.pending_action) return "awaiting confirmation";
  return "ok";
}

function SourceBadge({ status, scope }: { status: string; scope: string }) {
  const statusCls = status === "deprecated" ? "bg-breach/15 text-breach border-breach/40" : "bg-ok/15 text-ok border-ok/40";
  const scopeLabel = scope === "general" ? "GENERAL" : "ACCOUNT-SPECIFIC";
  return (
    <span className="flex items-center gap-1.5">
      <span className={`font-mono text-[9px] tracking-wider border rounded px-1 py-0.5 ${statusCls}`}>
        {status === "deprecated" ? "DEPRECATED" : "CURRENT"}
      </span>
      <span className="font-mono text-[9px] tracking-wider text-route border border-route/30 rounded px-1 py-0.5">
        {scopeLabel}
      </span>
    </span>
  );
}

function formatINR(amount: number): string {
  return `₹${amount.toLocaleString("en-IN")}`;
}

function Detail({ entry }: { entry: ToolTraceEntry }) {
  const out = entry.output;

  if (Array.isArray(out.results)) {
    const results = out.results as DocResult[];
    if (!results.length) return <div className="text-xs text-muted">No matching sources.</div>;
    return (
      <div className="flex flex-col gap-2">
        {results.map((r, i) => (
          <div key={i} className="flex items-start justify-between gap-2 text-xs">
            <div className="min-w-0">
              <div className="text-paper truncate">{r.title}</div>
              <div className="text-muted truncate">{r.heading}</div>
            </div>
            <SourceBadge status={r.status} scope={r.scope} />
          </div>
        ))}
      </div>
    );
  }

  if (out.order) {
    const o = out.order as OrderRecord;
    return (
      <div className="text-xs text-paper flex flex-col gap-1">
        <div>{o.order_id} · {o.status} · {o.carrier}</div>
        <div>{formatINR(o.shipment_fee_inr)}{o.carrier_fault ? " · carrier fault" : ""}{o.customer_fault ? " · customer fault" : ""}</div>
      </div>
    );
  }

  if (out.orders) {
    const orders = out.orders as OrderRecord[];
    return (
      <div className="flex flex-col gap-1">
        {orders.map((o, i) => (
          <div key={i} className="text-xs text-paper">
            {o.order_id} · {o.status} · {formatINR(o.shipment_fee_inr)}
          </div>
        ))}
      </div>
    );
  }

  if (out.ticket) {
    const t = out.ticket as TicketRecord;
    return <div className="text-xs text-paper">{t.ticket_id} · {t.status} · {t.subject}</div>;
  }

  if (out.tickets) {
    const tickets = out.tickets as TicketRecord[];
    return (
      <div className="flex flex-col gap-1">
        {tickets.map((t, i) => (
          <div key={i} className="text-xs text-paper">{t.ticket_id} · {t.status} · {t.subject}</div>
        ))}
      </div>
    );
  }

  if (out.pending_action) {
    const p = out.pending_action as { reason: string; priority: string };
    return <div className="text-xs text-paper">{p.priority} · {p.reason}</div>;
  }

  return null;
}

export function ToolTrace({ trace }: { trace: ToolTraceEntry[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  if (!trace.length) return null;

  return (
    <div className="flex flex-col gap-2 my-2">
      {trace.map((entry, i) => {
        const denied = entry.output.error === "access_denied";
        const isOpen = openIndex === i;
        return (
          <div key={i} className="relative">
            <div className="manifest-edge rounded-t-md bg-panel-raised glass shadow-sm shadow-black/5" />
            <button
              onClick={() => setOpenIndex(isOpen ? null : i)}
              className={`w-full text-left bg-panel-raised glass shadow-sm shadow-black/5 border-x border-line px-3 py-2 flex items-center justify-between gap-3 ${
                denied ? "border-l-2 border-l-breach" : ""
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${denied ? "bg-breach" : "bg-route"}`} />
                <span className={`font-mono text-[11px] tracking-wider shrink-0 ${denied ? "text-breach" : "text-route"}`}>
                  {TOOL_LABELS[entry.tool] ?? entry.tool.toUpperCase()}
                </span>
                <span className="text-xs text-muted truncate">{summarize(entry)}</span>
              </div>
              <span className="font-mono text-[10px] text-muted shrink-0">#{String(i + 1).padStart(2, "0")}</span>
            </button>
            {isOpen && (
              <div className="bg-panel-raised glass shadow-sm shadow-black/5 border-x border-b border-line px-3 py-2">
                <Detail entry={entry} />
              </div>
            )}
            <div className="manifest-edge rounded-b-md bg-panel-raised glass shadow-sm shadow-black/5" />
          </div>
        );
      })}
    </div>
  );
}
