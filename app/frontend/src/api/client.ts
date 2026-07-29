export interface CustomerListItem {
  customer_id: string;
  first_name: string;
  last_name: string;
  email: string;
  country: string;
  city: string;
  segment_id: string;
  lifetime_value: number;
  churn_score: number;
}

export interface CustomerListResponse {
  items: CustomerListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CustomerDetail {
  profile: Record<string, unknown>;
  transactions: Record<string, unknown>[];
}

export interface CustomerMetrics {
  lifetime_spend: number;
  spend_30d: number;
  spend_90d: number;
  open_tickets: number;
  avg_csat: number | null;
  top_categories: { category: string; spend: number }[];
}

export interface AppConfig {
  databricks_host: string;
  dashboard_id: string;
  genie_space_id: string;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export function getConfig(): Promise<AppConfig> {
  return req<AppConfig>("/api/config");
}

export interface GenieMessage {
  conversation_id: string;
  message_id: string;
  status: string | null;
  content: string | null;
  attachments: {
    attachment_id: string;
    text: string | null;
    has_query: boolean;
    query_description: string | null;
  }[];
  query_result?: { columns: string[]; rows: unknown[][] };
}

export function genieStart(content: string): Promise<GenieMessage> {
  return req("/api/genie/conversations", {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function genieReply(conversationId: string, content: string): Promise<GenieMessage> {
  return req(`/api/genie/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function genieGetMessage(
  conversationId: string,
  messageId: string,
): Promise<GenieMessage> {
  return req(`/api/genie/conversations/${conversationId}/messages/${messageId}`);
}

export interface JobRun {
  run_id: number;
  life_cycle_state: string | null;
  result_state: string | null;
  start_time?: number;
  run_page_url?: string;
}

export function runForwardEtl(): Promise<{ run_id: number }> {
  return req("/api/jobs/run-forward-etl", { method: "POST" });
}

export function getRun(runId: number): Promise<JobRun> {
  return req(`/api/jobs/${runId}`);
}

export function recentRuns(): Promise<{ runs: JobRun[] }> {
  return req("/api/jobs/");
}

export function listCustomers(params: {
  segment?: string;
  min_ltv?: number;
  max_churn?: number;
  page?: number;
  page_size?: number;
}): Promise<CustomerListResponse> {
  const q = new URLSearchParams();
  if (params.segment) q.set("segment", params.segment);
  if (params.min_ltv != null) q.set("min_ltv", String(params.min_ltv));
  if (params.max_churn != null) q.set("max_churn", String(params.max_churn));
  if (params.page != null) q.set("page", String(params.page));
  if (params.page_size != null) q.set("page_size", String(params.page_size));
  return req<CustomerListResponse>(`/api/customers?${q.toString()}`);
}

export function getCustomer(id: string): Promise<CustomerDetail> {
  return req<CustomerDetail>(`/api/customers/${id}`);
}

export function getMetrics(id: string): Promise<CustomerMetrics> {
  return req<CustomerMetrics>(`/api/customers/${id}/metrics`);
}

export function addNote(id: string, note_text: string): Promise<{ note_id: string }> {
  return req(`/api/customers/${id}/notes`, {
    method: "POST",
    body: JSON.stringify({ note_text }),
  });
}

export function overrideSegment(
  id: string,
  override_segment: string,
  reason?: string,
): Promise<{ customer_id: string; override_segment: string }> {
  return req(`/api/customers/${id}/segment`, {
    method: "POST",
    body: JSON.stringify({ override_segment, reason }),
  });
}
