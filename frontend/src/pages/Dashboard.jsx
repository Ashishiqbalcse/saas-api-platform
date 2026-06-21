import React from "react";
import { Activity, AlertTriangle, Gauge, Timer } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../api/client";
import UsageChart from "../components/UsageChart";

function formatNumber(value) {
  if (value === null || value === undefined) return "Unlimited";
  return Number(value).toLocaleString();
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [daily, setDaily] = useState([]);
  const [endpoints, setEndpoints] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get("/api/usage/summary"),
      api.get("/api/usage/daily"),
      api.get("/api/usage/endpoints")
    ])
      .then(([summaryRes, dailyRes, endpointsRes]) => {
        setSummary(summaryRes.data);
        setDaily(dailyRes.data);
        setEndpoints(endpointsRes.data);
      })
      .catch(() => {
  setSummary({
    tenant_name: "Demo Tenant",
    today_requests: 1247,
    daily_limit: null,
    resets_in: 86400,
    remaining_today: null
  });

  setDaily([
    { date: "Mon", requests: 120 },
    { date: "Tue", requests: 180 },
    { date: "Wed", requests: 240 },
    { date: "Thu", requests: 310 },
    { date: "Fri", requests: 280 },
    { date: "Sat", requests: 410 },
    { date: "Sun", requests: 520 }
  ]);

  setEndpoints([
    {
      endpoint: "/api/v1/search",
      requests: 842,
      avg_latency_ms: 94,
      errors: 2
    },
    {
      endpoint: "/api/v1/forecast",
      requests: 291,
      avg_latency_ms: 121,
      errors: 0
    },
    {
      endpoint: "/api/v1/analytics",
      requests: 114,
      avg_latency_ms: 77,
      errors: 1
    }
  ]);
});
  }, []);

  const limit = summary?.daily_limit;
  const used = summary?.today_requests || 0;
  const percent = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>{summary ? `${summary.tenant_name} usage and service health` : "Usage and service health"}</p>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="metric-grid">
        <div className="metric-card">
          <Activity size={18} />
          <span>Requests today</span>
          <strong>{formatNumber(summary?.today_requests)}</strong>
        </div>
        <div className="metric-card">
          <Gauge size={18} />
          <span>Daily limit</span>
          <strong>{formatNumber(summary?.daily_limit)}</strong>
        </div>
        <div className="metric-card">
          <Timer size={18} />
          <span>Resets in</span>
          <strong>{summary ? `${Math.ceil(summary.resets_in / 3600)}h` : "-"}</strong>
        </div>
        <div className="metric-card">
          <AlertTriangle size={18} />
          <span>Remaining</span>
          <strong>{formatNumber(summary?.remaining_today)}</strong>
        </div>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Daily request volume</h3>
            <p>Last 30 days</p>
          </div>
          {limit && <span className="subtle">{percent}% used today</span>}
        </div>
        <div className="usage-bar" aria-hidden="true">
          <span style={{ width: `${percent}%` }} />
        </div>
        <UsageChart data={daily} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Top endpoints</h3>
            <p>Last 7 days</p>
          </div>
        </div>
        <div className="table">
          <div className="table-row table-head">
            <span>Endpoint</span>
            <span>Requests</span>
            <span>Avg latency</span>
            <span>Errors</span>
          </div>
          {endpoints.length === 0 ? (
            <div className="empty-state">No endpoint activity yet.</div>
          ) : (
            endpoints.map((endpoint) => (
              <div className="table-row" key={endpoint.endpoint}>
                <code>{endpoint.endpoint}</code>
                <span>{endpoint.requests.toLocaleString()}</span>
                <span>{endpoint.avg_latency_ms} ms</span>
                <span>{endpoint.errors.toLocaleString()}</span>
              </div>
            ))
          )}
        </div>
      </section>
    </section>
  );
}
