import React from "react";
import { Check, Copy, KeyRound, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../api/client";
import KeyRow from "../components/KeyRow";

export default function ApiKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [revealedKey, setRevealedKey] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchKeys();
  }, []);

  async function fetchKeys() {
    setLoading(true);
    try {
      const { data } = await api.get("/api/keys");
      setKeys(data);
    } catch (err) {
      setError(err.friendlyMessage || "Failed to load API keys.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    setRevealedKey(null);
    try {
      const { data } = await api.post("/api/keys", { name: newName.trim() });
      setRevealedKey(data.key);
      setNewName("");
      await fetchKeys();
    } catch (err) {
      setError(err.friendlyMessage || err.response?.data?.detail || "Failed to create API key.");
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(keyId) {
    if (!window.confirm("Revoke this key? Applications using it will stop working immediately.")) {
      return;
    }
    try {
      await api.delete(`/api/keys/${keyId}`);
      setKeys((prev) => prev.filter((key) => key.id !== keyId));
    } catch (err) {
      setError(err.friendlyMessage || "Failed to revoke API key.");
    }
  }

  async function copyNewKey() {
    await navigator.clipboard.writeText(revealedKey);
  }

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h2>API keys</h2>
          <p>Create, rotate, and revoke tenant-scoped keys.</p>
        </div>
      </div>

      {revealedKey && (
        <div className="alert alert-success">
          <Check size={16} />
          <div>
            <strong>Key created. Copy it now.</strong>
            <code>{revealedKey}</code>
          </div>
          <button className="ghost-button" type="button" onClick={copyNewKey}>
            <Copy size={15} />
            Copy
          </button>
        </div>
      )}

      {error && <div className="alert alert-danger">{error}</div>}

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Create a key</h3>
            <p>Raw keys are shown once and stored only as hashes.</p>
          </div>
        </div>
        <form className="inline-form" onSubmit={handleCreate}>
          <KeyRound size={18} />
          <input
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            placeholder="Production server"
            disabled={creating}
          />
          <button className="primary-button" type="submit" disabled={creating || !newName.trim()}>
            <Plus size={16} />
            {creating ? "Creating..." : "Create"}
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Active keys</h3>
            <p>{keys.length} key{keys.length === 1 ? "" : "s"}</p>
          </div>
        </div>
        {loading ? (
          <div className="empty-state">Loading keys...</div>
        ) : keys.length === 0 ? (
          <div className="empty-state">No active keys yet.</div>
        ) : (
          <div className="key-list">
            {keys.map((key) => (
              <KeyRow key={key.id} keyData={key} onRevoke={handleRevoke} />
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
