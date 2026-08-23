import { useEffect, useState } from "react";
import { listAccounts, login, type Account, type Session } from "../lib/api";

export function Login({ onLogin }: { onLogin: (session: Session) => void }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [mode, setMode] = useState<"customer" | "internal">("internal");
  const [accountId, setAccountId] = useState("");
  const [role, setRole] = useState("ops_manager");
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    listAccounts().then((r) => {
      setAccounts(r.accounts);
      if (r.accounts.length) setAccountId(r.accounts[0].account_id);
    });
  }, []);

  async function submit() {
    if (!name.trim()) {
      setError("enter a name to continue");
      return;
    }
    try {
      const session = await login({
        persona: mode,
        account_id: mode === "customer" ? accountId : undefined,
        role: mode === "internal" ? role : undefined,
        display_name: name.trim(),
      });
      onLogin(session);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="mb-8">
          <div className="text-xs font-mono uppercase tracking-[0.3em] text-signal mb-2">
            ParcelPilot / Console Access
          </div>
          <h1 className="font-display text-4xl font-semibold text-paper">QuityPilot</h1>
          <p className="text-muted mt-2 text-sm leading-relaxed">
            Manifest-scoped access. Choose how you're signing in — this stands in for real
            authentication and account context in the demo.
          </p>
        </div>

        <div className="bg-panel glass shadow-sm shadow-black/5 border border-line rounded-xl overflow-hidden">
          <div className="grid grid-cols-2 border-b border-line">
            <button
              className={`py-3 text-sm font-medium transition ${
                mode === "internal" ? "bg-panel-raised glass shadow-sm shadow-black/5 text-paper" : "text-muted"
              }`}
              onClick={() => setMode("internal")}
            >
              Internal Ops
            </button>
            <button
              className={`py-3 text-sm font-medium transition ${
                mode === "customer" ? "bg-panel-raised glass shadow-sm shadow-black/5 text-paper" : "text-muted"
              }`}
              onClick={() => setMode("customer")}
            >
              Customer
            </button>
          </div>

          <div className="p-6 flex flex-col gap-4">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs uppercase tracking-wide text-muted">Your name</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Priya Nair"
                className="bg-ink border border-line rounded-lg px-3 py-2 text-sm text-paper outline-none focus:border-signal"
              />
            </label>

            {mode === "internal" ? (
              <label className="flex flex-col gap-1.5">
                <span className="text-xs uppercase tracking-wide text-muted">Role</span>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="bg-ink border border-line rounded-lg px-3 py-2 text-sm text-paper outline-none focus:border-signal"
                >
                  <option value="support_agent">Support Agent</option>
                  <option value="ops_manager">Ops Manager</option>
                </select>
              </label>
            ) : (
              <label className="flex flex-col gap-1.5">
                <span className="text-xs uppercase tracking-wide text-muted">Account</span>
                <select
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  className="bg-ink border border-line rounded-lg px-3 py-2 text-sm text-paper outline-none focus:border-signal"
                >
                  {accounts.map((a) => (
                    <option key={a.account_id} value={a.account_id}>
                      {a.name} · {a.tier}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {error && <div className="text-xs text-breach">{error}</div>}

            <button
              onClick={submit}
              className="mt-1 bg-signal text-ink font-semibold text-sm rounded-lg py-2.5 hover:brightness-110 transition"
            >
              Enter console
            </button>
          </div>
        </div>

        <p className="text-xs text-muted mt-4 leading-relaxed">
          Internal roles see cross-account tools and the signals dashboard. Customer sessions are
          scoped to the selected account at the data layer — try asking about another account's
          order to see it get refused.
        </p>
      </div>
    </div>
  );
}
