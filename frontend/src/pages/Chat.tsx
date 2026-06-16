import { useState, useRef, useEffect } from "react";
import { sendMessageStream } from "../api/client";
import type { Citation } from "../api/client";

interface Message {
  role: "user" | "ai";
  text: string;
  citations?: Citation[];
  tokens?: number;
}

export default function Chat({ workspaceId }: { workspaceId: string }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "ai",
      text: "Hello! I can answer questions grounded in your uploaded documents. Every claim I make will be tagged with its source. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "auto" });
  }, [messages]);

  const send = () => {
    if (!input.trim() || streaming) return;
    const question = input.trim();
    setInput("");

    setMessages((prev) => [
      ...prev,
      { role: "user", text: question },
      { role: "ai", text: "" },
    ]);
    setStreaming(true);

    sendMessageStream(
      workspaceId,
      question,
      (token) => {
        setMessages((prev) => {
          const msgs = [...prev];
          const last = msgs[msgs.length - 1];
          msgs[msgs.length - 1] = { ...last, text: last.text + token };
          return msgs;
        });
      },
      ({ citations, tokens_used }) => {
        setMessages((prev) => {
          const msgs = [...prev];
          const last = msgs[msgs.length - 1];
          msgs[msgs.length - 1] = { ...last, citations, tokens: tokens_used };
          return msgs;
        });
        setStreaming(false);
      },
      () => {
        setMessages((prev) => {
          const msgs = [...prev];
          msgs[msgs.length - 1] = {
            ...msgs[msgs.length - 1],
            text: "Something went wrong. Please try again.",
          };
          return msgs;
        });
        setStreaming(false);
      },
    );
  };

  return (
    <div style={s.page}>
      <div style={s.topbar}>
        <div>
          <div style={s.title}>Chat</div>
          <div style={s.sub}>Grounded answers from your documents</div>
        </div>
      </div>
      <div style={s.body}>
        <div style={s.messages}>
          {messages.map((m, i) => (
            <div key={i} style={{ ...s.row, ...(m.role === "user" ? s.rowUser : {}) }}>
              <div style={{ ...s.avatar, ...(m.role === "user" ? s.avatarUser : s.avatarAi) }}>
                {m.role === "user" ? "K" : "AI"}
              </div>
              <div style={s.bubbleWrap}>
                <div style={{ ...s.bubble, ...(m.role === "user" ? s.bubbleUser : s.bubbleAi) }}>
                  {m.text || (streaming && i === messages.length - 1 ? <span style={s.cursor}>▌</span> : "")}
                </div>
                {m.citations && m.citations.length > 0 && (
                  <div style={s.citations}>
                    {m.citations.map((c) => (
                      <span key={c.chunk_id} style={s.cite}>
                        📎 {c.filename} · {(c.score * 100).toFixed(0)}%
                      </span>
                    ))}
                  </div>
                )}
                {m.tokens !== undefined && (
                  <div style={s.tokenCount}>{m.tokens} tokens</div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <div style={s.inputRow}>
          <input
            style={s.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask a question about your documents..."
            disabled={streaming}
          />
          <button style={{ ...s.btn, opacity: streaming ? 0.6 : 1 }} onClick={send} disabled={streaming}>
            {streaming ? "…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", height: "100vh" },
  topbar: {
    padding: "16px 24px",
    borderBottom: "1px solid #D4E4F7",
    background: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: { fontFamily: "'Lora',serif", fontSize: 17, fontWeight: 600, color: "#0D2D6B" },
  sub: { fontSize: 12, color: "#7A9AC2", marginTop: 1 },
  body: { flex: 1, display: "flex", flexDirection: "column", padding: 24, gap: 16, overflow: "hidden" },
  messages: { flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 },
  row: { display: "flex", gap: 10, alignItems: "flex-start" },
  rowUser: { flexDirection: "row-reverse" },
  avatar: {
    width: 32, height: 32, borderRadius: "50%", display: "flex",
    alignItems: "center", justifyContent: "center", fontSize: 11,
    fontWeight: 600, flexShrink: 0,
  },
  avatarUser: { background: "#1A4FA0", color: "#fff" },
  avatarAi: { background: "#E3EDFC", color: "#1A4FA0", border: "1px solid #C8D9F0" },
  bubbleWrap: { display: "flex", flexDirection: "column", gap: 6, maxWidth: "80%" },
  bubble: { padding: "11px 15px", borderRadius: 16, fontSize: 13, lineHeight: 1.65, whiteSpace: "pre-wrap" },
  bubbleUser: {
    background: "#1A4FA0", color: "#fff",
    borderRadius: "16px 16px 4px 16px",
  },
  bubbleAi: {
    background: "#fff", color: "#1A3A6E",
    border: "1px solid #D4E4F7",
    borderRadius: "16px 16px 16px 4px",
    minHeight: 40,
  },
  cursor: { display: "inline-block", color: "#1A4FA0", animation: "none" },
  citations: { display: "flex", flexWrap: "wrap", gap: 6 },
  cite: {
    fontSize: 11, background: "#E3EDFC", border: "1px solid #C8D9F0",
    borderRadius: 8, padding: "3px 8px", color: "#1A4FA0",
  },
  tokenCount: { fontSize: 10, color: "#A0BAD8" },
  inputRow: { display: "flex", gap: 10 },
  input: {
    flex: 1, padding: "11px 16px", border: "1px solid #D4E4F7",
    borderRadius: 14, fontSize: 13, color: "#1A3A6E",
    background: "#fff", outline: "none",
  },
  btn: {
    padding: "11px 20px", background: "#1A4FA0", color: "#fff",
    border: "none", borderRadius: 14, fontSize: 13, fontWeight: 500,
    cursor: "pointer",
  },
};
