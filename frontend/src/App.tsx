import { useEffect, useState } from "react";
import type { Session } from "./lib/api";
import { Login } from "./components/Login";
import { ChatPanel } from "./components/ChatPanel";
import { Dashboard } from "./components/Dashboard";

const STORAGE_KEY = "quitypilot_session";

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [view, setView] = useState<"chat" | "dashboard">("chat");

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) setSession(JSON.parse(raw));
  }, []);

  function handleLogin(s: Session) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
    setSession(s);
  }

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY);
    setSession(null);
    setView("chat");
  }

  if (!session) return <Login onLogin={handleLogin} />;

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b border-line bg-panel-raised glass px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="font-display text-lg font-semibold text-paper">QuityPilot</span>
          <span className="font-mono text-[10px] tracking-[0.25em] text-muted border border-line rounded px-2 py-0.5">
            {session.persona === "internal" ? session.role.toUpperCase().replace("_", " ") : "CUSTOMER"}
          </span>
        </div>

        <nav className="flex items-center gap-1">
          <button
            onClick={() => setView("chat")}
            className={`text-sm px-3 py-1.5 rounded-lg transition ${
              view === "chat" ? "bg-panel-raised glass shadow-sm shadow-black/5 text-paper" : "text-muted hover:text-paper"
            }`}
          >
            Chat
          </button>
          {session.persona === "internal" && (
            <button
              onClick={() => setView("dashboard")}
              className={`text-sm px-3 py-1.5 rounded-lg transition ${
                view === "dashboard" ? "bg-panel-raised glass shadow-sm shadow-black/5 text-paper" : "text-muted hover:text-paper"
              }`}
            >
              Signals
            </button>
          )}
        </nav>

        <div className="flex items-center gap-3">
          <span className="text-sm text-muted">{session.display_name}</span>
          <button onClick={handleLogout} className="text-xs text-muted hover:text-signal transition">
            Switch session
          </button>
        </div>
      </header>

      <main className="flex-1 min-h-0">
        {view === "chat" ? <ChatPanel session={session} /> : <Dashboard session={session} />}
      </main>
    </div>
  );
}

export default App;
