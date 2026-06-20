import React from "react";

import { Copy, Trash2 } from "lucide-react";
import { useState } from "react";

export default function KeyRow({ keyData, onRevoke }) {
  const [copied, setCopied] = useState(false);
  const displayKey = `${keyData.prefix}************`;

  function formatDate(iso) {
    if (!iso) return "Never";
    return new Date(iso).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  }

  async function copyPrefix() {
    await navigator.clipboard.writeText(`${keyData.prefix}...`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="key-row">
      <div className="key-meta">
        <div className="key-name">{keyData.name}</div>
        <code>{displayKey}</code>
      </div>
      <div className="key-date">
        <span>Last used</span>
        <strong>{formatDate(keyData.last_used)}</strong>
      </div>
      <div className="key-date">
        <span>Created</span>
        <strong>{formatDate(keyData.created_at)}</strong>
      </div>
      <div className="row-actions">
        <button className="ghost-button" type="button" onClick={copyPrefix} title="Copy key prefix">
          <Copy size={15} />
          {copied ? "Copied" : "Copy"}
        </button>
        <button className="danger-button" type="button" onClick={() => onRevoke(keyData.id)} title="Revoke key">
          <Trash2 size={15} />
          Revoke
        </button>
      </div>
    </div>
  );
}
