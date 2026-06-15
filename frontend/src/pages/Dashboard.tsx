import { useQuery } from "@tanstack/react-query";
import { getDocuments, getAuditLogs } from "../api/client";

interface Doc {
  id: string;
  filename: string;
  status: string;
  file_size: number;
}

interface AuditLog {
  id: string;
  action: string;
  entity_type: string;
  details: unknown;
  created_at: string;
}

export default function Dashboard({ workspaceId }: { workspaceId: string }) {
  const { data: docs = [] } = useQuery<Doc[]>({
    queryKey: ["documents", workspaceId],
    queryFn: () => getDocuments(workspaceId),
  });

  const { data: logs = [] } = useQuery<AuditLog[]>({
    queryKey: ["audit", workspaceId],
    queryFn: () => getAuditLogs(workspaceId),
  });

  const readyDocs = docs.filter((d) => d.status === "ready").length;
  const runs = logs.filter((l) => l.action === "run_completed").length;

  const actionColor: Record<string, string> = {
    run_completed: "#1A7A46", run_started: "#1A4FA0",
    step_completed: "#5A7BA0", step_failed: "#C0392B",
    awaiting_approval: "#D07B12",
  };
  const actionBg: Record<string, string> = {
    run_completed: "#E3F5EC", run_started: "#E3EDFC",
    step_completed: "#EEF4FC", step_failed: "#FDECEA",
    awaiting_approval: "#FFF3E0",
  };

  return (
    <div style={s.page}>
      <div style={s.topbar}>
        <div>
          <div style={s.title}>Dashboard</div>
          <div style={s.sub}>Smith & Partners Workspace</div>
        </div>
      </div>
      <div style={s.body}>
        <div style={s.metrics}>
          <div style={s.metric}>
            <div style={s.mLabel}>Documents</div>
            <div style={s.mValue}>{docs.length}</div>
            <div style={s.mSub}>{readyDocs} ready</div>
          </div>
          <div style={s.metric}>
            <div style={s.mLabel}>Completed Runs</div>
            <div style={s.mValue}>{runs}</div>
            <div style={s.mSub}>This workspace</div>
          </div>
          <div style={s.metric}>
            <div style={s.mLabel}>Audit Events</div>
            <div style={s.mValue}>{logs.length}</div>
            <div style={s.mSub}>Full trail</div>
          </div>
          <div style={s.metric}>
            <div style={s.mLabel}>Status</div>
            <div style={s.mValue}>
              <span style={s.activeBadge}>Active</span>
            </div>
            <div style={s.mSub}>Backend connected</div>
          </div>
        </div>
        <div style={s.sectionHeader}>Audit log</div>
        <div style={s.tableWrap}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Action</th>
                <th style={s.th}>Details</th>
                <th style={s.th}>Time</th>
              </tr>
            </thead>
            <tbody>
              {logs.slice(0, 20).map((l) => (
                <tr key={l.id}>
                  <td style={s.td}>
                    <span style={{
                      ...s.badge,
                      background: actionBg[l.action] || "#EEF4FC",
                      color: actionColor[l.action] || "#5A7BA0",
                    }}>
                      {l.action}
                    </span>
                  </td>
                  <td style={{ ...s.td, ...s.tdDetail }}>
                    {JSON.stringify(l.details).slice(0, 80)}
                  </td>
                  <td style={{ ...s.td, color: "#7A9AC2", fontSize: 11 }}>
                    {new Date(l.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={3} style={{ ...s.td, textAlign: "center", color: "#7A9AC2" }}>
                    No audit events yet. Run a workflow to see events here.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
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
  mValue: { fontSize: 22, fontWeight: 500, color: "#0D2D6B", fontFamily: "'Lora',serif" },
  mSub: { fontSize: 11, color: "#A0BAD8", marginTop: 3 },
  activeBadge: {
    background: "#E3F5EC", color: "#1A7A46",
    padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 500,
  },
  sectionHeader: { fontSize: 13, fontWeight: 500, color: "#1A3A6E", marginBottom: 14 },
  tableWrap: { borderRadius: 16, overflow: "hidden", border: "1px solid #D4E4F7" },
  table: { width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 12 },
  th: {
    textAlign: "left", padding: "9px 14px", color: "#7A9AC2",
    fontWeight: 500, fontSize: 11, textTransform: "uppercase",
    letterSpacing: "0.5px", background: "#F4F8FE", borderBottom: "1px solid #D4E4F7",
  },
  td: { padding: "10px 14px", borderBottom: "1px solid #EEF4FC", background: "#fff", verticalAlign: "middle" },
  tdDetail: { fontSize: 11, color: "#5A7BA0", fontFamily: "monospace" },
  badge: { display: "inline-flex", padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 500 },
};