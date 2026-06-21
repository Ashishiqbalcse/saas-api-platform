import React, { useEffect, useState } from "react";
import { CreditCard, KeyRound, LayoutDashboard } from "lucide-react";

import api from "./api/client";
import PlanBadge from "./components/PlanBadge";
import ApiKeys from "./pages/ApiKeys";
import Billing from "./pages/Billing";
import Dashboard from "./pages/Dashboard";

const TABS = [
{ key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
{ key: "keys", label: "API Keys", icon: KeyRound },
{ key: "billing", label: "Billing", icon: CreditCard }
];

export default function App() {
const [tab, setTab] = useState("dashboard");
const [summary, setSummary] = useState(null);

useEffect(() => {
api
.get("/api/usage/summary")
.then((response) => setSummary(response.data))
.catch(() => {});
}, [tab]);

return ( <main className="app-shell"> <header className="topbar"> <div className="nav-left"> <div className="brand-compact"> <div className="brand-mark">S</div> <span>API Platform</span> </div>

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
    </div>
  </header>

  {tab === "dashboard" && <Dashboard />}
  {tab === "keys" && <ApiKeys />}
  {tab === "billing" && <Billing />}
</main>

);
}
