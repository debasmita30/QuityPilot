const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export type Persona = "customer" | "internal";

export interface Session {
  token: string;
  persona: Persona;
  account_id: string | null;
  role: string;
  display_name: string;
}

export interface Account {
  account_id: string;
  name: string;
  tier: string;
}

export interface ToolTraceEntry {
  tool: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
}

export interface PendingAction {
  action_id: string;
  type: string;
  ticket_id: string | null;
  order_id: string | null;
  account_id: string | null;
  reason: string;
  priority: string;
  requested_by: string;
  status: string;
}

export interface ChatResponse {
  conversation_id: string;
  reply: string;
  trace: ToolTraceEntry[];
  pending_action: PendingAction | null;
}

async function request<T>(path: string, options: RequestInit = {}, session?: Session | null): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (session) headers["Authorization"] = `Bearer ${session.token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${body}`);
  }
  return res.json();
}

export function listAccounts(): Promise<{ accounts: Account[] }> {
  return request("/auth/accounts");
}

export function login(payload: {
  persona: Persona;
  account_id?: string;
  role?: string;
  display_name: string;
}): Promise<Session> {
  return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function sendMessage(
  session: Session,
  message: string,
  conversationId: string | null
): Promise<ChatResponse> {
  return request(
    "/chat",
    {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    },
    session
  );
}

export function confirmAction(session: Session, actionId: string) {
  return request(`/actions/${actionId}/confirm`, { method: "POST" }, session);
}

export function cancelAction(session: Session, actionId: string) {
  return request(`/actions/${actionId}/cancel`, { method: "POST" }, session);
}

export interface SlaSignal {
  type: string;
  level: "at_risk" | "breached";
  ticket_id: string;
  account_id: string;
  severity: string;
  elapsed_hours: number;
  target_hours: number;
  subject: string;
}

export interface SpikeSignal {
  type: string;
  category: string;
  ticket_count_24h: number;
  accounts_affected: string[];
  ticket_ids: string[];
}

export interface ClusterSignal {
  type: string;
  known_issue: string;
  accounts_affected: string[];
  ticket_ids: string[];
}

export interface ActivitySignal {
  type: string;
  account_id: string;
  open_ticket_count: number;
}

export interface SignalsResponse {
  dataset_reference_time: string;
  sla_risk: SlaSignal[];
  complaint_spikes: SpikeSignal[];
  known_issue_clusters: ClusterSignal[];
  unusual_account_activity: ActivitySignal[];
}

export function getSignals(session: Session): Promise<SignalsResponse> {
  return request("/dashboard/signals", {}, session);
}
