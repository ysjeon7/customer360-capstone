import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { runForwardEtl, recentRuns } from "../api/client";

export default function Reports() {
  const qc = useQueryClient();

  const runs = useQuery({
    queryKey: ["job-runs"],
    queryFn: recentRuns,
    refetchInterval: 5000,
  });

  const trigger = useMutation({
    mutationFn: runForwardEtl,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job-runs"] }),
  });

  return (
    <div>
      <h1>Reports</h1>

      <button disabled={trigger.isPending} onClick={() => trigger.mutate()}>
        {trigger.isPending ? "Starting…" : "Run forward-ETL"}
      </button>
      {trigger.isSuccess && <span> ✓ triggered run {trigger.data.run_id}</span>}
      {trigger.error && <span style={{ color: "red" }}> {String(trigger.error)}</span>}

      <h3>Recent runs</h3>
      {runs.isLoading && <p>Loading…</p>}
      <table>
        <thead>
          <tr><th>Run ID</th><th>Lifecycle</th><th>Result</th><th>Started</th></tr>
        </thead>
        <tbody>
          {runs.data?.runs.map((r) => (
            <tr key={r.run_id}>
              <td>{r.run_id}</td>
              <td>{r.life_cycle_state}</td>
              <td>{r.result_state ?? "-"}</td>
              <td>{r.start_time ? new Date(r.start_time).toLocaleString() : "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
