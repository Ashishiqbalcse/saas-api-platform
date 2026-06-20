import React from "react";

const PLAN_LABELS = {
  free: "Free",
  pro: "Pro",
  enterprise: "Enterprise"
};

export default function PlanBadge({ plan }) {
  return (
    <span className={`plan-badge plan-${plan}`}>
      {PLAN_LABELS[plan] || plan}
    </span>
  );
}