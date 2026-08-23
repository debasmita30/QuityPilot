import { useEffect, useState } from "react";
import { getSignals, type Session, type SignalsResponse } from "../lib/api";

function LevelBadge({ level }: { level: "at_risk" | "breached" }) {
  const cls = level === "breached" ? "bg-breach/15 text-breach border-breach/40" : "bg-warn/15 text-warn border-warn/40";
  return (
    <span className={`font-mono text-[10px] tracking-wider border rounded px-1.5 py-0.5 ${cls}`}>
      {level === "breached" ? "SLA BREACHED" : "AT RISK"}
    </span>
  );
}

function Panel({ title, eyebrow, children }: { title: string; eyebrow: string; children: React.ReactNode }) {
  return (
    <div className="bg-panel glass shadow-sm shadow-black/5 border border-line rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-line">
        <div className="font-mono text-[10px] tracking-[0.25em] text-route">{eyebrow}</div>
        <div className="font-display text-lg text-paper mt-0.5">{title}</div>
      </div>
      <div className="p-4 flex flex-col gap-3">{children}</div>
    </div>
  );
}

export function Dashboard({ session }: { session: Session }) {
  const [data, setData] = useState<SignalsResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getSignals(session)
      .then(setData)
      .catch((e) => setError(String(e)));
  }, [session]);

  if (error) return <div className="p-6 text-breach text-sm">{error}</div>;
  if (!data) return <div className="p-6 text-muted text-sm">Loading signals…</div>;

  return (
    <div className="p-6 overflow-y-auto h-full">
      <div className="mb-6">
        <div className="font-mono text-[11px] tracking-[0.3em] text-signal mb-1">PROACTIVE SIGNALS</div>
        <h2 className="font-display text-2xl text-paper">What deserves attention right now</h2>
        <p className="text-muted text-sm mt-1">
          Reference time: <span className="font-mono">{data.dataset_reference_time}</span>
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Panel eyebrow="01 · SLA RISK" title="Approaching or past SLA">
          {data.sla_risk.length === 0 && <div className="text-sm text-muted">No tickets at risk.</div>}
          {data.sla_risk.map((s) => (
            <div key={s.ticket_id} className="flex items-start justify-between gap-3 border-b border-line/60 pb-3 last:border-0 last:pb-0">
              <div>
                <div className="font-mono text-xs text-paper">{s.ticket_id} · {s.account_id}</div>
                <div className="text-sm text-muted">{s.subject}</div>
                <div className="text-xs text-muted mt-1">
                  {s.elapsed_hours}h elapsed / {s.target_hours}h target · {s.severity}
                </div>
              </div>
              <LevelBadge level={s.level} />
            </div>
          ))}
        </Panel>

        <Panel eyebrow="02 · COMPLAINT SPIKES" title="Rising in the last 24h">
          {data.complaint_spikes.length === 0 && <div className="text-sm text-muted">No spikes detected.</div>}
          {data.complaint_spikes.map((s) => (
            <div key={s.category} className="border-b border-line/60 pb-3 last:border-0 last:pb-0">
              <div className="text-sm text-paper capitalize">{s.category.replace("_", " ")}</div>
              <div className="text-xs text-muted mt-1">
                {s.ticket_count_24h} tickets across {s.accounts_affected.length} account(s)
              </div>
              <div className="font-mono text-[11px] text-route mt-1">{s.ticket_ids.join(", ")}</div>
            </div>
          ))}
        </Panel>

        <Panel eyebrow="03 · KNOWN ISSUE CLUSTERS" title="Same root cause, multiple tickets">
          {data.known_issue_clusters.length === 0 && <div className="text-sm text-muted">No clusters detected.</div>}
          {data.known_issue_clusters.map((s) => (
            <div key={s.known_issue} className="border-b border-line/60 pb-3 last:border-0 last:pb-0">
              <div className="text-sm text-paper capitalize">{s.known_issue.replace(/_/g, " ")}</div>
              <div className="text-xs text-muted mt-1">accounts: {s.accounts_affected.join(", ")}</div>
              <div className="font-mono text-[11px] text-route mt-1">{s.ticket_ids.join(", ")}</div>
            </div>
          ))}
        </Panel>

        <Panel eyebrow="04 · ACCOUNT ACTIVITY" title="Unusual concentration of open tickets">
          {data.unusual_account_activity.length === 0 && <div className="text-sm text-muted">Nothing unusual.</div>}
          {data.unusual_account_activity.map((s) => (
            <div key={s.account_id} className="flex items-center justify-between border-b border-line/60 pb-3 last:border-0 last:pb-0">
              <div className="text-sm text-paper">{s.account_id}</div>
              <div className="font-mono text-xs text-warn">{s.open_ticket_count} open</div>
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
