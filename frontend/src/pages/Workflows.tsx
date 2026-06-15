import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getTemplates, startRun, getRun, getRunSteps, getCostSummary, getHallucinationChecks } from "../api/client";

interface Template {
  id: string;
  name: string;
  description: string;
}

interface Run {
  run_id: string;
  status: string;
  template: string;
}

interface Step {
  step_order: number;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  output_preview: string | null;
}

interface CostSummary {
  run_id: string;
  total_tokens: number;
  total_cost: number;
  call_count: number;
}

interface HallucinationCheck {
  id: string;
  risk_level: string;
  source_alignment_score: number;
  unsupported_claims: string[];
  missing_citations: string[];
  recommended_rewrite: string | null;
}

export default function Workflows({ workspaceId }: { workspaceId: string }) {
  const [runId, setRunId] = useState<string | null>(null);
  const [focus, setFocus] = useState("Analyze the uploaded documents.");

  const { data: templates = [] } = useQuery<Template[]>({
    queryKey: ["templates"],
    queryFn: getTemplates,
  });

  const { data: run } = useQuery<Run>({
    queryKey: ["run", runId],
    queryFn: () => getRun(runId!),
    enabled: !!runId,
    refetchInterval: (q) => q.state.data?.status === "completed" || q.state.data?.status === "failed" ? false : 2000,
  });

  const { data: steps = [] } = useQuery<Step[]>({
    queryKey: ["steps", runId],
    queryFn: () => getRunSteps(runId!),
    enabled: !!runId,
    refetchInterval: run?.status === "completed" ? false : 2000,
  });

  const { data: cost } = useQuery<CostSummary>({
    queryKey: ["cost", runId],
    queryFn: () => getCostSummary(runId!),
    enabled: !!runId && run?.status === "completed",
  });

  const { data: halluc = [] } = useQuery<HallucinationCheck[]>({
    queryKey: ["halluc", runId],
    queryFn: () => getHallucinationChecks(runId!),
    enabled: !!runId && run?.status === "completed",
  });

  const start = useMutation({
    mutationFn: (templateId: string) => startRun(templateId, workspaceId, focus),
    onSuccess: (data) => setRunId(data.run_id),
  });

  const statusColor: Record<string, string> = {
    completed: "#1A7A46", failed: "#C0392B", running: "#D07B12", pending: "#1A4FA0",
  };
  const statusBg: Record<string, string> = {
    completed: "#E3F5EC", failed: "#FDECEA", running: "#FFF3E0", pending: "#E3EDFC",
  };
  const riskColor: Record<string, string> = { high: "#C0392B", medium: "#D07B12", low: "#1A7A46" };
  const riskBg: Record<string, string> = { high: "#FDECEA", medium: "#FFF3E0", low: "#E3F5EC" };
  const STEP_ACCENTS = ["#1A4FA0", "#7B5EA7", "#E8A020", "#1A7A46", "#C0392B"];

  if (runId && run) {
    const check = halluc[0];
    return (
      <div style={s.page}>
        <div style={s.topbar}>
          <div>
            <div style={s.title}>Run Detail</div>
            <div style={s.sub}>{run.run_id?.slice(0, 8)}</div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <span style={{ ...s.badge, background: statusBg[run.status], color: statusColor[run.status] }}>
              {run.status}
            </span>
            <button style={s.btnOutline} onClick={() => setRunId(null)}>← Back</button>
          </div>
        </div>
        <div style={s.body}>
          {cost && (
            <div style={s.metrics}>
              <div style={s.metric}>
                <div style={s.mLabel}>Total Tokens</div>
                <div style={s.mValue}>{cost.total_tokens.toLocaleString()}</div>
              </div>
              <div style={s.metric}>
                <div style={s.mLabel}>Estimated Cost</div>
                <div style={s.mValue}>${cost.total_cost}</div>
              </div>
              <div style={s.metric}>
                <div style={s.mLabel}>LLM Calls</div>
                <div style={s.mValue}>{cost.call_count}</div>
              </div>
              {check && (
                <div style={s.metric}>
                  <div style={s.mLabel}>Hallucination Risk</div>
                  <div style={s.mValue}>
                    <span style={{ ...s.badge, background: riskBg[check.risk_level], color: riskColor[check.risk_level] }}>
                      {check.risk_level}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
          <div style={s.sectionHeader}>Agent execution trace</div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            {steps.map((step, i) => (
              <div key={step.step_order} style={{ display: "flex", gap: 16, marginBottom: 12 }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 32, flexShrink: 0 }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: "50%", display: "flex",
                    alignItems: "center", justifyContent: "center", fontSize: 12,
                    border: `2px solid ${statusColor[step.status] || "#C8D9F0"}`,
                    background: statusBg[step.status] || "#EEF4FC",
                    color: statusColor[step.status] || "#7A9AC2",
                  }}>
                    {step.status === "completed" ? "✓" : step.status === "failed" ? "✕" : "…"}
                  </div>
                  {i < steps.length - 1 && (
                    <div style={{ width: 1, flex: 1, background: "#D4E4F7", marginTop: 4, minHeight: 16 }} />
                  )}
                </div>
                <div style={{
                  flex: 1, padding: "12px 16px", background: "#fff",
                  border: "1px solid #D4E4F7",
                  borderLeft: `3px solid ${STEP_ACCENTS[step.step_order % STEP_ACCENTS.length]}`,
                  borderRadius: "0 16px 16px 0",
                  marginBottom: 4,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 13, fontWeight: 500, color: "#1A3A6E" }}>
                      Step {step.step_order + 1}
                    </span>
                    <span style={{ fontSize: 11, color: "#7A9AC2" }}>
                      {step.started_at ? new Date(step.started_at).toLocaleTimeString() : ""}
                    </span>
                  </div>
                  {step.output_preview && (
                    <div style={{ fontSize: 12, color: "#5A7BA0", lineHeight: 1.6 }}>
                      {step.output_preview.slice(0, 120)}...
                    </div>
                  )}
                </div>
              </div>
            ))}
            {run.status !== "completed" && run.status !== "failed" && (
              <div style={{ textAlign: "center", padding: 20, color: "#7A9AC2", fontSize: 13 }}>
                Running agents...
              </div>
            )}
          </div>
          {check?.recommended_rewrite && (
            <div style={s.rewriteBox}>
              <div style={s.rewriteTitle}>⚠ Recommended rewrite</div>
              <div style={s.rewriteText}>{check.recommended_rewrite.slice(0, 300)}...</div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={s.page}>
      <div style={s.topbar}>
        <div>
          <div style={s.title}>Workflows</div>
          <div style={s.sub}>Run governed agent pipelines</div>
        </div>
      </div>
      <div style={s.body}>
        <div style={s.focusRow}>
          <label style={s.focusLabel}>Focus prompt</label>
          <input
            style={s.focusInput}
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            placeholder="What should the agents focus on?"
          />
        </div>
        <div style={s.sectionHeader}>Templates</div>
        <div style={s.grid}>
          {templates.map((t) => (
            <div key={t.id} style={s.card}>
              <div style={s.cardIcon}>⚡</div>
              <div style={s.cardName}>{t.name}</div>
              <div style={s.cardDesc}>{t.description}</div>
              <button
                style={s.btn}
                onClick={() => start.mutate(t.id)}
                disabled={start.isPending}
              >
                {start.isPending ? "Starting..." : "Run workflow"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", height: "100vh" },
  topbar: {
    padding: "16px 24px", borderBottom: "1px solid #D4E4F7",
    background: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between",
  },
  title: { fontFamily: "'Lora',serif", fontSize: 17, fontWeight: 600, color: "#0D2D6B" },
  sub: { fontSize: 12, color: "#7A9AC2", marginTop: 1 },
  body: { flex: 1, padding: 24, overflowY: "auto" },
  metrics: { display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 24 },
  metric: { background: "#fff", borderRadius: 16, padding: "14px 16px", border: "1px solid #D4E4F7" },
  mLabel: { fontSize: 11, color: "#7A9AC2", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 6 },
  mValue: { fontSize: 20, fontWeight: 500, color: "#0D2D6B", fontFamily: "'Lora',serif" },
  sectionHeader: { fontSize: 13, fontWeight: 500, color: "#1A3A6E", marginBottom: 14 },
  badge: { display: "inline-flex", padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 500 },
  focusRow: { marginBottom: 24, display: "flex", flexDirection: "column", gap: 6 },
  focusLabel: { fontSize: 12, fontWeight: 500, color: "#1A3A6E" },
  focusInput: {
    padding: "10px 14px", border: "1px solid #D4E4F7", borderRadius: 12,
    fontSize: 13, color: "#1A3A6E", background: "#fff", outline: "none",
  },
  grid: { display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 },
  card: {
    background: "#fff", border: "1px solid #D4E4F7",
    borderRadius: 18, padding: 20,
  },
  cardIcon: { fontSize: 24, marginBottom: 10 },
  cardName: { fontSize: 14, fontWeight: 500, color: "#1A3A6E", marginBottom: 6 },
  cardDesc: { fontSize: 12, color: "#7A9AC2", lineHeight: 1.5, marginBottom: 14 },
  btn: {
    width: "100%", padding: "9px 0", background: "#1A4FA0",
    color: "#fff", border: "none", borderRadius: 12,
    fontSize: 13, fontWeight: 500,
  },
  btnOutline: {
    padding: "7px 14px", background: "#fff", color: "#1A4FA0",
    border: "1px solid #C8D9F0", borderRadius: 12, fontSize: 12, fontWeight: 500,
  },
  rewriteBox: {
    marginTop: 20, padding: 16, background: "#FFF3E0",
    border: "1px solid #F5D5A0", borderRadius: 16,
  },
  rewriteTitle: { fontSize: 12, fontWeight: 500, color: "#D07B12", marginBottom: 8 },
  rewriteText: { fontSize: 12, color: "#7A4A0A", lineHeight: 1.6 },
};