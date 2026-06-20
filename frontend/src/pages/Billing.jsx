import React from "react";
import { CreditCard, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../api/client";
import PlanBadge from "../components/PlanBadge";

const PLANS = [
  {
    key: "free",
    label: "Free",
    price: "Rs. 0 / mo",
    requests: "100 requests/day",
    keys: "2 API keys",
    support: "Community support"
  },
  {
    key: "pro",
    label: "Pro",
    price: "Rs. 999 / mo",
    requests: "10,000 requests/day",
    keys: "10 API keys",
    support: "Email support",
    featured: true
  },
  {
    key: "enterprise",
    label: "Enterprise",
    price: "Rs. 7,999 / mo",
    requests: "Unlimited requests",
    keys: "100 API keys",
    support: "Priority support and SLA"
  }
];

export default function Billing() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyPlan, setBusyPlan] = useState(null);
  const [error, setError] = useState(null);

  const params = new URLSearchParams(window.location.search);
  const stripeSuccess = params.get("success") === "1";
  const stripeCancelled = params.get("cancelled") === "1";
  const currentPlan = summary?.plan || "free";

  useEffect(() => {
    api.get("/api/usage/summary")
      .then((response) => setSummary(response.data))
      .catch((err) => setError(err.friendlyMessage || "Failed to load billing status."))
      .finally(() => setLoading(false));
  }, []);

  async function startCheckout(plan) {
    setBusyPlan(plan);
    setError(null);
    try {
      const { data } = await api.post("/api/billing/checkout", { plan });
      window.location.href = data.checkout_url;
    } catch (err) {
      setError(err.friendlyMessage || err.response?.data?.detail || "Could not start checkout.");
      setBusyPlan(null);
    }
  }

  async function openPortal() {
    setBusyPlan("portal");
    setError(null);
    try {
      const { data } = await api.post("/api/billing/portal");
      window.location.href = data.portal_url;
    } catch (err) {
      setError(err.friendlyMessage || "Could not open the billing portal.");
      setBusyPlan(null);
    }
  }

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h2>Billing</h2>
          <p>Plan, subscription status, and Stripe checkout.</p>
        </div>
        {summary && <PlanBadge plan={currentPlan} />}
      </div>

      {stripeSuccess && <div className="alert alert-success">Payment completed. The webhook updates your plan.</div>}
      {stripeCancelled && <div className="alert">Checkout cancelled. No changes were made.</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="plans-grid">
        {PLANS.map((plan) => {
          const isCurrent = plan.key === currentPlan;
          const downgrade = PLANS.findIndex((item) => item.key === plan.key) <
            PLANS.findIndex((item) => item.key === currentPlan);
          return (
            <section className={plan.featured ? "plan-card featured" : "plan-card"} key={plan.key}>
              <div className="plan-title">
                <div>
                  <h3>{plan.label}</h3>
                  <strong>{plan.price}</strong>
                </div>
                {isCurrent && <PlanBadge plan={plan.key} />}
              </div>
              <ul>
                <li>{plan.requests}</li>
                <li>{plan.keys}</li>
                <li>{plan.support}</li>
              </ul>
              {isCurrent || downgrade ? (
                <button className="ghost-button full-width" type="button" onClick={openPortal} disabled={!!busyPlan}>
                  <CreditCard size={16} />
                  {busyPlan === "portal" ? "Opening..." : "Manage subscription"}
                </button>
              ) : (
                <button
                  className="primary-button full-width"
                  type="button"
                  onClick={() => startCheckout(plan.key)}
                  disabled={!!busyPlan || loading}
                >
                  <ExternalLink size={16} />
                  {busyPlan === plan.key ? "Redirecting..." : `Upgrade to ${plan.label}`}
                </button>
              )}
            </section>
          );
        })}
      </div>
    </section>
  );
}
