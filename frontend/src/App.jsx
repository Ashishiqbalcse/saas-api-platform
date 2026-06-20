import React from "react";
import { useEffect, useState } from "react";
import { CreditCard, KeyRound, LayoutDashboard, LogOut } from "lucide-react";
import api from "./api/client";
import PlanBadge from "./components/PlanBadge";
import ApiKeys from "./pages/ApiKeys";
import Billing from "./pages/Billing";
import Dashboard from "./pages/Dashboard";

const TABS = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "keys", label: "API keys", icon: KeyRound },
  { key: "billing", label: "Billing", icon: CreditCard }
];

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [apiKey, setApiKey] = useState(localStorage.getItem("api_key") || "");
  const [keyInput, setKeyInput] = useState("");
  const [summary, setSummary] = useState(null);
  const [setupError, setSetupError] = useState(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    const onUnauthorized = () => {
      setApiKey("");
      setSummary(null);
      setSetupError("Your API key is invalid or has been revoked.");
    };
    window.addEventListener("api:unauthorized", onUnauthorized);
    return () => window.removeEventListener("api:unauthorized", onUnauthorized);
  }, []);

  useEffect(() => {
    if (!apiKey) return;
    api.get("/api/usage/summary").then((r) => setSummary(r.data)).catch(() => {});
  }, [apiKey, tab]);

  async function handleKeySubmit(event) {
    event.preventDefault();
    if (!keyInput.trim()) return;
    setVerifying(true);
    setSetupError(null);
    localStorage.setItem("api_key", keyInput.trim());
    try {
      await api.get("/api/v1/health/authed");
      setApiKey(keyInput.trim());
      setKeyInput("");
    } catch {
      localStorage.removeItem("api_key");
      setSetupError("Invalid API key. Check it and try again.");
    } finally {
      setVerifying(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("api_key");
    setApiKey("");
    setSummary(null);
  }

  if (!apiKey) {
    return (
      <main className="setup-shell">
        <section className="setup-panel" aria-label="API key setup">
          <div className="brand-row">
            <div className="brand-mark">S</div>
            <div>
              <h1>SaaS API Platform</h1>
              <p>Enter an API key to open the developer dashboard.</p>
            </div>
          </div>

          {setupError && <div className="alert alert-danger">{setupError}</div>}

          <form className="stack" onSubmit={handleKeySubmit}>
            <label htmlFor="api-key">API key</label>
            <input
              id="api-key"
              value={keyInput}
              onChange={(event) => setKeyInput(event.target.value)}
              placeholder="sk_live_..."
              autoFocus
              disabled={verifying}
            />
            <button className="primary-button" type="submit" disabled={verifying || !keyInput.trim()}>
              <KeyRound size={16} />
              {verifying ? "Verifying..." : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="nav-left">
          <div className="brand-compact">
            <div className="brand-mark">S</div>
            <span>API Platform</span>
          </div>
          <nav className="tabs" aria-label="Dashboard sections">
            {TABS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.key}
                  className={tab === item.key ? "tab active" : "tab"}
                  onClick={() => setTab(item.key)}
                  type="button"
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="topbar-actions">
          {summary && <PlanBadge plan={summary.plan} />}
          <button className="icon-button" type="button" onClick={handleLogout} title="Sign out">
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {tab === "dashboard" && <Dashboard />}
      {tab === "keys" && <ApiKeys />}
      {tab === "billing" && <Billing />}
    </main>
  );
}
