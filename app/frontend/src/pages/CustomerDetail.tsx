import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import {
  getCustomer, getMetrics, addNote, overrideSegment,
} from "../api/client";

type Tab = "profile" | "activity" | "metrics" | "segment";

export default function CustomerDetail() {
  const { id = "" } = useParams();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("profile");
  const [note, setNote] = useState("");
  const [seg, setSeg] = useState("");

  const detail = useQuery({ queryKey: ["customer", id], queryFn: () => getCustomer(id) });
  const metrics = useQuery({ queryKey: ["metrics", id], queryFn: () => getMetrics(id) });

  const noteMut = useMutation({
    mutationFn: () => addNote(id, note),
    onSuccess: () => { setNote(""); qc.invalidateQueries({ queryKey: ["customer", id] }); },
  });
  const segMut = useMutation({
    mutationFn: () => overrideSegment(id, seg),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["customer", id] }),
  });

  const profile = detail.data?.profile as Record<string, any> | undefined;

  return (
    <div>
      <Link to="/customers">← Back</Link>
      <h1>Customer {id}</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {(["profile", "activity", "metrics", "segment"] as Tab[]).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{ fontWeight: tab === t ? "bold" : "normal" }}>{t}</button>
        ))}
      </div>

      {tab === "profile" && profile && (
        <ul>
          <li>Name: {profile.first_name} {profile.last_name}</li>
          <li>Email: {profile.email}</li>
          <li>Phone: {profile.phone}</li>
          <li>Segment: {profile.segment_id}</li>
          <li>Signup: {profile.signup_date}</li>
          <li>Churn: {profile.churn_score}</li>
          <li>LTV: {profile.lifetime_value}</li>
        </ul>
      )}

      {tab === "activity" && (
        <table>
          <thead><tr><th>Txn</th><th>Date</th><th>Channel</th><th>Status</th><th>Amount</th></tr></thead>
          <tbody>
            {detail.data?.transactions.map((t: any) => (
              <tr key={t.transaction_id}>
                <td>{t.transaction_id}</td><td>{t.transaction_date}</td>
                <td>{t.channel}</td><td>{t.status}</td><td>{t.amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === "metrics" && (
        metrics.isLoading ? <p>Loading…</p> :
        metrics.data && (
          <ul>
            <li>Lifetime spend: {metrics.data.lifetime_spend}</li>
            <li>Last 30d: {metrics.data.spend_30d}</li>
            <li>Last 90d: {metrics.data.spend_90d}</li>
            <li>Open tickets: {metrics.data.open_tickets}</li>
            <li>Avg CSAT: {metrics.data.avg_csat ?? "n/a"}</li>
            <li>Top categories: {metrics.data.top_categories.map((c) => `${c.category} (${c.spend})`).join(", ")}</li>
          </ul>
        )
      )}

      {tab === "segment" && (
        <div>
          <p>Current segment: {profile?.segment_id}</p>
          <input placeholder="new segment (e.g. S2)" value={seg}
            onChange={(e) => setSeg(e.target.value)} />
          <button disabled={!seg || segMut.isPending} onClick={() => segMut.mutate()}>Override</button>
          {segMut.isSuccess && <span> ✓ saved</span>}
        </div>
      )}

      <hr />
      <h3>Add note</h3>
      <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
      <br />
      <button disabled={!note || noteMut.isPending} onClick={() => noteMut.mutate()}>Add note</button>
      {noteMut.isSuccess && <span> ✓ added</span>}
    </div>
  );
}
