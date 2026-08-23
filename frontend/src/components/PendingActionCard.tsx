import { useState } from "react";
import { cancelAction, confirmAction, type PendingAction, type Session } from "../lib/api";

export function PendingActionCard({
  session,
  action,
  onResolved,
}: {
  session: Session;
  action: PendingAction;
  onResolved: (status: "confirmed" | "cancelled") => void;
}) {
  const [busy, setBusy] = useState(false);

  async function handleConfirm() {
    setBusy(true);
    await confirmAction(session, action.action_id);
    setBusy(false);
    onResolved("confirmed");
  }

  async function handleCancel() {
    setBusy(true);
    await cancelAction(session, action.action_id);
    setBusy(false);
    onResolved("cancelled");
  }

  return (
    <div className="border border-signal/40 bg-signal-soft rounded-xl p-4 my-2">
      <div className="flex items-center gap-2 mb-2">
        <span className="w-1.5 h-1.5 rounded-full bg-signal pulse-dot" />
        <span className="font-mono text-[11px] tracking-wider text-signal">
          CONFIRMATION REQUIRED — NOTHING HAS BEEN CREATED YET
        </span>
      </div>
      <div className="text-sm text-paper mb-1">Escalation, priority: {action.priority}</div>
      <div className="text-sm text-muted mb-3">{action.reason}</div>
      {(action.ticket_id || action.order_id) && (
        <div className="font-mono text-xs text-muted mb-3">
          {action.ticket_id ? `ticket ${action.ticket_id}` : ""}
          {action.ticket_id && action.order_id ? " · " : ""}
          {action.order_id ? `order ${action.order_id}` : ""}
        </div>
      )}
      <div className="flex gap-2">
        <button
          disabled={busy}
          onClick={handleConfirm}
          className="bg-signal text-ink text-sm font-semibold rounded-lg px-4 py-1.5 hover:brightness-110 disabled:opacity-50"
        >
          Confirm escalation
        </button>
        <button
          disabled={busy}
          onClick={handleCancel}
          className="border border-line text-paper text-sm rounded-lg px-4 py-1.5 hover:border-muted disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
