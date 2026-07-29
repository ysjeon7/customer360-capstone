import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { listCustomers } from "../api/client";

const PAGE_SIZE = 25;

export default function Customers() {
  const navigate = useNavigate();
  const [segment, setSegment] = useState("");
  const [minLtv, setMinLtv] = useState("");
  const [maxChurn, setMaxChurn] = useState("");
  const [page, setPage] = useState(1);

  const filters = {
    segment: segment || undefined,
    min_ltv: minLtv ? Number(minLtv) : undefined,
    max_churn: maxChurn ? Number(maxChurn) : undefined,
    page,
    page_size: PAGE_SIZE,
  };

  const { data, isLoading, error } = useQuery({
    queryKey: ["customers", filters],
    queryFn: () => listCustomers(filters),
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      <h1>Customers</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input placeholder="segment (e.g. S1)" value={segment}
          onChange={(e) => { setSegment(e.target.value); setPage(1); }} />
        <input placeholder="min LTV" value={minLtv}
          onChange={(e) => { setMinLtv(e.target.value); setPage(1); }} />
        <input placeholder="max churn" value={maxChurn}
          onChange={(e) => { setMaxChurn(e.target.value); setPage(1); }} />
      </div>

      {isLoading && <p>Loading…</p>}
      {error && <p style={{ color: "red" }}>{String(error)}</p>}

      {data && (
        <>
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Name</th><th>Email</th><th>Country</th>
                <th>Segment</th><th>LTV</th><th>Churn</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr key={c.customer_id} style={{ cursor: "pointer" }}
                  onClick={() => navigate(`/customers/${c.customer_id}`)}>
                  <td>{c.customer_id}</td>
                  <td>{c.first_name} {c.last_name}</td>
                  <td>{c.email}</td>
                  <td>{c.country}</td>
                  <td>{c.segment_id}</td>
                  <td>{c.lifetime_value?.toFixed(2)}</td>
                  <td>{c.churn_score?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center" }}>
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
            <span>Page {data.page} / {totalPages} ({data.total} total)</span>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
          </div>
        </>
      )}
    </div>
  );
}
