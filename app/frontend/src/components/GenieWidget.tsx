import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  genieStart, genieReply, genieGetMessage, getConfig, GenieMessage,
} from "../api/client";

interface ChatItem {
  role: "user" | "genie";
  text: string;
  result?: { columns: string[]; rows: unknown[][] };
}

const TERMINAL = ["COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"];
const POLL_MS = 1500;
const MAX_POLLS = 20; // ~30s

async function pollMessage(convId: string, msgId: string): Promise<GenieMessage> {
  for (let i = 0; i < MAX_POLLS; i++) {
    const msg = await genieGetMessage(convId, msgId);
    const status = (msg.status || "").replace(/^MessageStatus\./, "");
    if (TERMINAL.some((t) => status.includes(t))) return msg;
    await new Promise((r) => setTimeout(r, POLL_MS));
  }
  throw new Error("Genie did not respond in time");
}

function answerText(msg: GenieMessage): string {
  const parts = msg.attachments.map((a) => a.text || a.query_description).filter(Boolean);
  return (parts.join("\n") || msg.content || "(no answer)") as string;
}

export default function GenieWidget() {
  const [open, setOpen] = useState(false);
  const [enlarged, setEnlarged] = useState(false);
  const [convId, setConvId] = useState<string | null>(null);
  const [items, setItems] = useState<ChatItem[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cfg = useQuery({ queryKey: ["config"], queryFn: getConfig, enabled: open });

  async function send() {
    if (!input.trim() || busy) return;
    const q = input.trim();
    setInput("");
    setItems((prev) => [...prev, { role: "user", text: q }]);
    setBusy(true);
    setError(null);
    try {
      const start = convId ? await genieReply(convId, q) : await genieStart(q);
      if (!convId) setConvId(start.conversation_id);
      const final = await pollMessage(start.conversation_id, start.message_id);
      setItems((prev) => [...prev, {
        role: "genie",
        text: answerText(final),
        result: final.query_result,
      }]);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        style={{ position: "fixed", bottom: 24, right: 24, borderRadius: 24, padding: "12px 20px" }}
      >
        Ask Genie
      </button>
    );
  }

  const genieUrl = cfg.data
    ? `${cfg.data.databricks_host}/genie/rooms/${cfg.data.genie_space_id}`
    : "#";

  return (
    <div style={{
      position: "fixed", bottom: 24, right: 24,
      width: enlarged ? 640 : 360, height: enlarged ? 640 : 460,
      background: "#fff", border: "1px solid #ccc", borderRadius: 8,
      display: "flex", flexDirection: "column", boxShadow: "0 4px 16px rgba(0,0,0,.2)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", padding: 8, borderBottom: "1px solid #eee" }}>
        <strong>Genie</strong>
        <span style={{ display: "flex", gap: 8 }}>
          {enlarged && cfg.data && (
            <a href={genieUrl} target="_blank" rel="noreferrer">Open in workspace</a>
          )}
          <button onClick={() => setEnlarged((v) => !v)}>{enlarged ? "Shrink" : "Enlarge"}</button>
          <button onClick={() => setOpen(false)}>×</button>
        </span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 8 }}>
        {items.map((it, i) => (
          <div key={i} style={{ margin: "6px 0", textAlign: it.role === "user" ? "right" : "left" }}>
            <div style={{ whiteSpace: "pre-wrap" }}>
              <b>{it.role === "user" ? "You" : "Genie"}:</b> {it.text}
            </div>
            {it.result && (
              <table style={{ fontSize: 12, marginTop: 4 }}>
                <thead><tr>{it.result.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                <tbody>
                  {it.result.rows.slice(0, 10).map((r, ri) => (
                    <tr key={ri}>{(r as unknown[]).map((v, ci) => <td key={ci}>{String(v)}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ))}
        {busy && <div><i>Genie is typing…</i></div>}
        {error && <div style={{ color: "red" }}>{error}</div>}
      </div>

      <div style={{ display: "flex", gap: 4, padding: 8, borderTop: "1px solid #eee" }}>
        <input
          style={{ flex: 1 }}
          value={input}
          placeholder="Ask a question…"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button disabled={busy} onClick={send}>Send</button>
      </div>
    </div>
  );
}
