import { useQuery } from "@tanstack/react-query";
import { getConfig } from "../api/client";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["config"],
    queryFn: getConfig,
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p style={{ color: "red" }}>{String(error)}</p>;
  if (!data) return null;

  const src = `${data.databricks_host}/embed/dashboardsv3/${data.dashboard_id}`;

  return (
    <div>
      <h1>Dashboard</h1>
      <iframe
        title="AI/BI Dashboard"
        src={src}
        style={{ width: "100%", height: "80vh", border: "none" }}
      />
    </div>
  );
}
