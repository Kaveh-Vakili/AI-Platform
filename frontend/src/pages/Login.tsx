import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/client";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await login(email, password);
      localStorage.setItem("token", data.access_token);
      nav("/");
    } catch {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>STRATOS AI</div>
        <div style={s.tagline}>Document Intelligence Platform</div>
        <form onSubmit={submit} style={s.form}>
          <div style={s.field}>
            <label style={s.label}>Email</label>
            <input
              style={s.input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>
          <div style={s.field}>
            <label style={s.label}>Password</label>
            <input
              style={s.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          {error && <div style={s.error}>{error}</div>}
          <button style={s.btn} type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#EEF4FC",
  },
  card: {
    background: "#fff",
    border: "1px solid #D4E4F7",
    borderRadius: 20,
    padding: "40px 36px",
    width: 380,
    boxShadow: "0 4px 24px rgba(26,79,160,0.08)",
  },
  logo: {
    fontFamily: "'Lora', serif",
    fontSize: 24,
    fontWeight: 600,
    color: "#1A4FA0",
    marginBottom: 4,
  },
  tagline: {
    fontSize: 13,
    color: "#7A9AC2",
    marginBottom: 32,
  },
  form: { display: "flex", flexDirection: "column", gap: 16 },
  field: { display: "flex", flexDirection: "column", gap: 6 },
  label: { fontSize: 12, fontWeight: 500, color: "#1A3A6E" },
  input: {
    padding: "10px 14px",
    border: "1px solid #D4E4F7",
    borderRadius: 12,
    fontSize: 14,
    color: "#1A3A6E",
    outline: "none",
    background: "#F4F8FE",
  },
  error: {
    fontSize: 12,
    color: "#C0392B",
    background: "#FDECEA",
    padding: "8px 12px",
    borderRadius: 10,
  },
  btn: {
    padding: "11px 0",
    background: "#1A4FA0",
    color: "#fff",
    border: "none",
    borderRadius: 12,
    fontSize: 14,
    fontWeight: 500,
    marginTop: 4,
    cursor: "pointer",
  },
};