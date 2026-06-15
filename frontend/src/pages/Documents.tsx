import { useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDocuments, uploadDocument, deleteDocument, embedDocuments } from "../api/client";

interface Doc {
  id: string;
  filename: string;
  status: string;
  file_size: number;
}

export default function Documents({ workspaceId }: { workspaceId: string }) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: docs = [], isLoading } = useQuery<Doc[]>({
    queryKey: ["documents", workspaceId],
    queryFn: () => getDocuments(workspaceId),
    refetchInterval: 3000,
  });

  const upload = useMutation({
    mutationFn: (file: File) => uploadDocument(workspaceId, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", workspaceId] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteDocument(workspaceId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", workspaceId] }),
  });

  const embed = useMutation({
    mutationFn: () => embedDocuments(workspaceId),
  });

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload.mutate(file);
  };

  const statusColor: Record<string, string> = {
    ready: "#1A7A46", parsing: "#D07B12", failed: "#C0392B", uploaded: "#1A4FA0",
  };
  const statusBg: Record<string, string> = {
    ready: "#E3F5EC", parsing: "#FFF3E0", failed: "#FDECEA", uploaded: "#E3EDFC",
  };

  return (
    <div style={s.page}>
      <div style={s.topbar}>
        <div>
          <div style={s.title}>Documents</div>
          <div style={s.sub}>{docs.length} files · Auto-refreshing</div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button style={s.btnOutline} onClick={() => embed.mutate()}>
            {embed.isPending ? "Embedding..." : "⚡ Embed all"}
          </button>
          <button style={s.btn} onClick={() => fileRef.current?.click()}>
            ↑ Upload PDF
          </button>
          <input ref={fileRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={onFile} />
        </div>
      </div>
      <div style={s.body}>
        {isLoading && <div style={s.empty}>Loading...</div>}
        {!isLoading && docs.length === 0 && (
          <div style={s.empty}>No documents yet. Upload a PDF to get started.</div>
        )}
        {docs.map((doc) => (
          <div key={doc.id} style={s.row}>
            <span style={{ fontSize: 22 }}>📄</span>
            <div style={{ flex: 1 }}>
              <div style={s.docName}>{doc.filename}</div>
              <div style={s.docMeta}>
                {doc.file_size ? `${(doc.file_size / 1024).toFixed(0)} KB · ` : ""}
                {doc.status}
              </div>
            </div>
            <span style={{
              ...s.badge,
              background: statusBg[doc.status] || "#EEF4FC",
              color: statusColor[doc.status] || "#5A7BA0",
            }}>
              {doc.status}
            </span>
            <button
              style={s.del}
              onClick={() => remove.mutate(doc.id)}
            >
              ✕
            </button>
          </div>
        ))}
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
  body: { flex: 1, padding: 24, display: "flex", flexDirection: "column", gap: 10, overflowY: "auto" },
  row: {
    display: "flex", alignItems: "center", gap: 14,
    padding: "14px 16px", background: "#fff",
    borderRadius: 16, border: "1px solid #D4E4F7",
  },
  docName: { fontSize: 13, fontWeight: 500, color: "#1A3A6E" },
  docMeta: { fontSize: 11, color: "#7A9AC2", marginTop: 2 },
  badge: { padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 500 },
  del: {
    background: "none", border: "none", color: "#A0BAD8",
    cursor: "pointer", fontSize: 14, padding: "4px 6px", borderRadius: 8,
  },
  btn: {
    padding: "8px 16px", background: "#1A4FA0", color: "#fff",
    border: "none", borderRadius: 12, fontSize: 12, fontWeight: 500,
  },
  btnOutline: {
    padding: "8px 16px", background: "#fff", color: "#1A4FA0",
    border: "1px solid #C8D9F0", borderRadius: 12, fontSize: 12, fontWeight: 500,
  },
  empty: { textAlign: "center", padding: 48, color: "#7A9AC2", fontSize: 13 },
};