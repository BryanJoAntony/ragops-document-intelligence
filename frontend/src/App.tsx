import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  Briefcase,
  Database,
  FileText,
  Gauge,
  GitCompare,
  Loader2,
  MessageSquareText,
  Route,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type TabKey = "overview" | "retrieval" | "evaluations" | "jobs" | "routing" | "ask";

type OverviewResponse = {
  documents_total: number;
  documents_indexed: number;
  chunks_total: number;
  query_audits_total: number;
  llm_call_logs_total: number;
  evaluation_runs_total: number;
  citation_validation_results_total: number;
  async_jobs_total: number;
  latest_activity: Array<Record<string, unknown>>;
};

type RetrievalResponse = {
  query_audits_total: number;
  retrieval_mode_counts: Record<string, number>;
  filter_usage_counts: Record<string, number>;
  filtered_query_count: number;
  provider_call_counts: Record<string, number>;
  average_latency_ms: number | null;
  recent_queries: Array<Record<string, unknown>>;
};

type EvaluationsResponse = {
  evaluation_runs_total: number;
  completed_runs_total: number;
  latest_average_score: number | null;
  best_average_score: number | null;
  average_of_average_scores: number | null;
  citation_validation_results_total: number;
  average_citation_validation_score: number | null;
  recent_runs: Array<Record<string, unknown>>;
};

type JobsResponse = {
  async_jobs_total: number;
  job_status_counts: Record<string, number>;
  job_type_counts: Record<string, number>;
  recent_jobs: Array<Record<string, unknown>>;
};

type RoutingResponse = {
  recommended_answer_provider: string | null;
  recommended_answer_strategy: string;
  recommended_answer_providers: string[] | null;
  estimated_context_tokens: number;
  estimated_output_tokens: number;
  provider_estimates: Array<Record<string, unknown>>;
  reasons: string[];
  warnings: string[];
};

type AskResponse = {
  request_id: string;
  question: string;
  answer: string;
  citations: Array<Record<string, unknown>>;
  retrieval: Record<string, unknown>;
  model_name: string;
  latency_ms: number;
};

const tabs: Array<{ key: TabKey; label: string; icon: React.ElementType }> = [
  { key: "overview", label: "Overview", icon: Gauge },
  { key: "retrieval", label: "Retrieval", icon: Activity },
  { key: "evaluations", label: "Evaluations", icon: BarChart3 },
  { key: "jobs", label: "Jobs", icon: Briefcase },
  { key: "routing", label: "Routing", icon: Route },
  { key: "ask", label: "Ask Demo", icon: MessageSquareText },
];

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Database size={24} />
          </div>
          <div>
            <h1>RAGOps</h1>
            <p>Document Intelligence</p>
          </div>
        </div>

        <nav className="nav">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                className={activeTab === tab.key ? "nav-item active" : "nav-item"}
                onClick={() => setActiveTab(tab.key)}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">RAG observability dashboard</p>
            <h2>{tabs.find((tab) => tab.key === activeTab)?.label}</h2>
          </div>
          <div className="api-pill">API: {API_BASE}</div>
        </header>

        {activeTab === "overview" && <OverviewPage />}
        {activeTab === "retrieval" && <RetrievalPage />}
        {activeTab === "evaluations" && <EvaluationsPage />}
        {activeTab === "jobs" && <JobsPage />}
        {activeTab === "routing" && <RoutingPage />}
        {activeTab === "ask" && <AskPage />}
      </main>
    </div>
  );
}

function OverviewPage() {
  const { data, loading, error, refresh } = useApi<OverviewResponse>("/dashboard/overview");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!data) return null;

  return (
    <section className="page-stack">
      <div className="metric-grid">
        <MetricCard label="Documents" value={data.documents_total} />
        <MetricCard label="Indexed" value={data.documents_indexed} />
        <MetricCard label="Chunks" value={data.chunks_total} />
        <MetricCard label="Query audits" value={data.query_audits_total} />
        <MetricCard label="Provider calls" value={data.llm_call_logs_total} />
        <MetricCard label="Evaluation runs" value={data.evaluation_runs_total} />
        <MetricCard label="Citation validations" value={data.citation_validation_results_total} />
        <MetricCard label="Async jobs" value={data.async_jobs_total} />
      </div>

      <Panel title="Latest activity" icon={Activity}>
        <SimpleTable rows={data.latest_activity} />
      </Panel>
    </section>
  );
}

function RetrievalPage() {
  const { data, loading, error, refresh } = useApi<RetrievalResponse>("/dashboard/retrieval");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!data) return null;

  return (
    <section className="page-stack">
      <div className="metric-grid">
        <MetricCard label="Query audits" value={data.query_audits_total} />
        <MetricCard label="Filtered queries" value={data.filtered_query_count} />
        <MetricCard label="Average latency" value={formatMs(data.average_latency_ms)} />
      </div>

      <div className="two-col">
        <Panel title="Retrieval modes" icon={GitCompare}>
          <KeyValueList data={data.retrieval_mode_counts} />
        </Panel>

        <Panel title="Filter usage" icon={FileText}>
          <KeyValueList data={data.filter_usage_counts} />
        </Panel>
      </div>

      <Panel title="Provider calls" icon={Database}>
        <KeyValueList data={data.provider_call_counts} />
      </Panel>

      <Panel title="Recent queries" icon={Activity}>
        <SimpleTable rows={data.recent_queries} />
      </Panel>
    </section>
  );
}

function EvaluationsPage() {
  const { data, loading, error, refresh } = useApi<EvaluationsResponse>("/dashboard/evaluations");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!data) return null;

  return (
    <section className="page-stack">
      <div className="metric-grid">
        <MetricCard label="Runs" value={data.evaluation_runs_total} />
        <MetricCard label="Completed" value={data.completed_runs_total} />
        <MetricCard label="Latest score" value={formatScore(data.latest_average_score)} />
        <MetricCard label="Best score" value={formatScore(data.best_average_score)} />
        <MetricCard label="Avg score" value={formatScore(data.average_of_average_scores)} />
        <MetricCard label="Avg citation score" value={formatScore(data.average_citation_validation_score)} />
      </div>

      <Panel title="Recent evaluation runs" icon={BarChart3}>
        <SimpleTable rows={data.recent_runs} />
      </Panel>
    </section>
  );
}

function JobsPage() {
  const { data, loading, error, refresh } = useApi<JobsResponse>("/dashboard/jobs");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!data) return null;

  return (
    <section className="page-stack">
      <div className="metric-grid">
        <MetricCard label="Async jobs" value={data.async_jobs_total} />
      </div>

      <div className="two-col">
        <Panel title="Job status counts" icon={Briefcase}>
          <KeyValueList data={data.job_status_counts} />
        </Panel>

        <Panel title="Job type counts" icon={Database}>
          <KeyValueList data={data.job_type_counts} />
        </Panel>
      </div>

      <Panel title="Recent jobs" icon={Activity}>
        <SimpleTable rows={data.recent_jobs} />
      </Panel>
    </section>
  );
}

function RoutingPage() {
  const [question, setQuestion] = useState("Where should audit history be stored?");
  const [taskType, setTaskType] = useState("qa");
  const [priority, setPriority] = useState("balanced");
  const [allowPaid, setAllowPaid] = useState(false);
  const [requireCompare, setRequireCompare] = useState(false);
  const [data, setData] = useState<RoutingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/routing/answer-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          retrieval_mode: "hybrid",
          top_k: 5,
          task_type: taskType,
          priority,
          allow_paid_providers: allowPaid,
          max_estimated_cost_usd: allowPaid ? 0.01 : 0.0,
          require_compare: requireCompare,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      setData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Routing request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-stack">
      <Panel title="Answer routing plan" icon={Route}>
        <div className="form-grid">
          <label>
            Question
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
          </label>

          <label>
            Task type
            <select value={taskType} onChange={(event) => setTaskType(event.target.value)}>
              <option value="qa">QA</option>
              <option value="summary">Summary</option>
              <option value="comparison">Comparison</option>
              <option value="evaluation">Evaluation</option>
            </select>
          </label>

          <label>
            Priority
            <select value={priority} onChange={(event) => setPriority(event.target.value)}>
              <option value="balanced">Balanced</option>
              <option value="cost">Cost</option>
              <option value="quality">Quality</option>
              <option value="latency">Latency</option>
            </select>
          </label>

          <label className="checkbox-row">
            <input type="checkbox" checked={allowPaid} onChange={(event) => setAllowPaid(event.target.checked)} />
            Allow paid providers
          </label>

          <label className="checkbox-row">
            <input type="checkbox" checked={requireCompare} onChange={(event) => setRequireCompare(event.target.checked)} />
            Require compare
          </label>

          <button className="primary-btn" onClick={submit} disabled={loading}>
            {loading ? "Planning..." : "Build routing plan"}
          </button>
        </div>
      </Panel>

      {error && <ErrorState message={error} onRetry={submit} />}

      {data && (
        <>
          <div className="metric-grid">
            <MetricCard label="Provider" value={data.recommended_answer_provider || "compare"} />
            <MetricCard label="Strategy" value={data.recommended_answer_strategy} />
            <MetricCard label="Context tokens" value={data.estimated_context_tokens} />
            <MetricCard label="Output tokens" value={data.estimated_output_tokens} />
          </div>

          <Panel title="Provider estimates" icon={Database}>
            <SimpleTable rows={data.provider_estimates} />
          </Panel>

          <Panel title="Reasons" icon={Activity}>
            <ul className="plain-list">
              {data.reasons.map((reason) => <li key={reason}>{reason}</li>)}
              {data.warnings.map((warning) => <li key={warning}>Warning: {warning}</li>)}
            </ul>
          </Panel>
        </>
      )}
    </section>
  );
}

function AskPage() {
  const [question, setQuestion] = useState("Where should audit history be stored?");
  const [filename, setFilename] = useState("sample_policy_milestone3.txt");
  const [retrievalMode, setRetrievalMode] = useState("hybrid");
  const [data, setData] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setLoading(true);
    setError("");

    const filters = filename.trim() ? { filename: filename.trim() } : undefined;

    try {
      const response = await fetch(`${API_BASE}/query/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          top_k: 5,
          retrieval_mode: retrievalMode,
          filters,
          answer_strategy: "single",
          answer_provider: "local_extractive",
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      setData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ask request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-stack">
      <Panel title="Ask with retrieval filters" icon={MessageSquareText}>
        <div className="form-grid">
          <label>
            Question
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
          </label>

          <label>
            Retrieval mode
            <select value={retrievalMode} onChange={(event) => setRetrievalMode(event.target.value)}>
              <option value="hybrid">Hybrid</option>
              <option value="vector">Vector</option>
              <option value="bm25">BM25</option>
              <option value="fuzzy">Fuzzy</option>
            </select>
          </label>

          <label>
            Filename filter
            <input value={filename} onChange={(event) => setFilename(event.target.value)} />
          </label>

          <button className="primary-btn" onClick={submit} disabled={loading}>
            {loading ? "Asking..." : "Ask"}
          </button>
        </div>
      </Panel>

      {error && <ErrorState message={error} onRetry={submit} />}

      {data && (
        <>
          <Panel title="Answer" icon={MessageSquareText}>
            <p className="answer-text">{data.answer}</p>
          </Panel>

          <div className="metric-grid">
            <MetricCard label="Request ID" value={data.request_id} />
            <MetricCard label="Model" value={data.model_name} />
            <MetricCard label="Latency" value={`${data.latency_ms} ms`} />
            <MetricCard label="Citations" value={data.citations.length} />
          </div>

          <Panel title="Retrieval metadata" icon={Activity}>
            <JsonBlock value={data.retrieval} />
          </Panel>

          <Panel title="Citations" icon={FileText}>
            <SimpleTable rows={data.citations} />
          </Panel>
        </>
      )}
    </section>
  );
}

function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const url = useMemo(() => `${API_BASE}${path}`, [path]);

  async function load() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      setData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [url]);

  return { data, loading, error, refresh: load };
}

function MetricCard({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="metric-card">
      <p>{label}</p>
      <strong>{value ?? "—"}</strong>
    </div>
  );
}

function Panel({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <Icon size={18} />
        <h3>{title}</h3>
      </div>
      {children}
    </section>
  );
}

function KeyValueList({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);

  if (!entries.length) return <p className="muted">No data yet.</p>;

  return (
    <div className="kv-list">
      {entries.map(([key, value]) => (
        <div className="kv-row" key={key}>
          <span>{key}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function SimpleTable({ rows }: { rows: Array<Record<string, unknown>> }) {
  if (!rows.length) return <p className="muted">No rows yet.</p>;

  const columns = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key));
      return set;
    }, new Set<string>())
  ).slice(0, 8);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => <td key={column}>{formatCell(row[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

function LoadingState() {
  return (
    <div className="state-card">
      <Loader2 className="spin" size={24} />
      <p>Loading dashboard data...</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="state-card error">
      <p>{message}</p>
      <button className="secondary-btn" onClick={onRetry}>Retry</button>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function formatScore(value: number | null): string {
  if (value === null) return "—";
  return value.toFixed(4);
}

function formatMs(value: number | null): string {
  if (value === null) return "—";
  return `${value.toFixed(1)} ms`;
}

export default App;
