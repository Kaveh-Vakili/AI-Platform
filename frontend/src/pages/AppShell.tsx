import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import Chat from "./Chat";
import Documents from "./Documents";
import Workflows from "./Workflows";
import Dashboard from "./Dashboard";

const NAV_TOP = [
  { id: "chat", icon: "💬", label: "Chat", path: "/" },
  { id: "documents", icon: "📄", label: "Documents", path: "/documents" },
  { id: "workflows", icon: "⚡", label: "Workflows", path: "/workflows" },
];
const NAV_BOTTOM = [
  { id: "dashboard", icon: "📊", label: "Dashboard", path: "/dashboard" },
];

const WORKSPACE_ID = "68035ab6-524c-4463-a335-7f2e3194c182";

export { WORKSPACE_ID };

export default function AppShell() {
  const nav = useNavigate();
  const loc = useLocation();
  const active = loc.pathname;

  const logout = () => {
    localStorage.removeItem("token");
    nav("/login");
  };

  return (
    <div style={s.app}>
      <aside style={s.sidebar}>
        <div style={s.logo}>
          <div style={s.logoName}>STRATOS AI</div>
          <div style={s.logoTag}>Document Intelligence</div>
        </div>
        <nav style={s.nav}>
          <div style={s.navSection}>Main</div>
          {NAV_TOP.map((item) => (
            <div
              key={item.id}
              style={{
                ...s.navItem,
                ...(active === item.path ? s.navActive : {}),
              }}
              onClick={() => nav(item.path)}
            >
              <span style={s.navIcon}>{item.icon}</span>
              {item.label}
            </div>
          ))}
          <div style={s.navSpacer} />
          <div style={s.navSection}>Overview</div>
          {NAV_BOTTOM.map((item) => (
            <div
              key={item.id}
              style={{
                ...s.navItem,
                ...(active === item.path ? s.navActive : {}),
              }}
              onClick={() => nav(item.path)}
            >
              <span style={s.navIcon}>{item.icon}</span>
              {item.label}
            </div>
          ))}
        </nav>
        <div style={s.workspace}>
          <div style={s.wsLabel}>Active workspace</div>
          <div style={s.wsName}>Smith & Partners</div>
        </div>
        <div style={s.logoutBtn} onClick={logout}>
          Sign out
        </div>
      </aside>

      <main style={s.main}>
        <Routes>
          <Route path="/" element={<Chat workspaceId={WORKSPACE_ID} />} />
          <Route path="/documents" element={<Documents workspaceId={WORKSPACE_ID} />} />
          <Route path="/workflows" element={<Workflows workspaceId={WORKSPACE_ID} />} />
          <Route path="/dashboard" element={<Dashboard workspaceId={WORKSPACE_ID} />} />
        </Routes>
      </main>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  app: { display: "flex", minHeight: "100vh", background: "#EEF4FC" },
  sidebar: {
    width: 220,
    flexShrink: 0,
    background: "#1A4FA0",
    display: "flex",
    flexDirection: "column",
  },
  logo: {
    padding: "22px 18px 18px",
    borderBottom: "1px solid rgba(255,255,255,0.1)",
  },
  logoName: {
    fontFamily: "'Lora', serif",
    fontSize: 18,
    fontWeight: 600,
    color: "#fff",
  },
  logoTag: {
    fontSize: 10,
    color: "rgba(255,255,255,0.5)",
    textTransform: "uppercase",
    letterSpacing: "0.8px",
    marginTop: 2,
  },
  nav: {
    padding: "14px 10px",
    flex: 1,
    display: "flex",
    flexDirection: "column",
  },
  navSection: {
    fontSize: 10,
    color: "rgba(255,255,255,0.4)",
    textTransform: "uppercase",
    letterSpacing: "0.8px",
    padding: "10px 8px 6px",
    fontWeight: 500,
  },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "9px 12px",
    borderRadius: 12,
    cursor: "pointer",
    fontSize: 13,
    color: "rgba(255,255,255,0.65)",
    marginBottom: 3,
  },
  navActive: {
    background: "rgba(255,255,255,0.18)",
    color: "#fff",
    fontWeight: 500,
  },
  navIcon: { fontSize: 15 },
  navSpacer: { flex: 1 },
  workspace: {
    margin: "0 10px 8px",
    padding: "12px 14px",
    background: "rgba(255,255,255,0.1)",
    border: "1px solid rgba(255,255,255,0.15)",
    borderRadius: 14,
  },
  wsLabel: {
    fontSize: 10,
    color: "rgba(255,255,255,0.4)",
    textTransform: "uppercase",
    letterSpacing: "0.8px",
    marginBottom: 3,
  },
  wsName: { fontSize: 13, color: "#fff", fontWeight: 500 },
  logoutBtn: {
    margin: "0 10px 16px",
    padding: "8px 14px",
    fontSize: 12,
    color: "rgba(255,255,255,0.5)",
    cursor: "pointer",
    borderRadius: 10,
    textAlign: "center",
  },
  main: { flex: 1, display: "flex", flexDirection: "column", minWidth: 0 },
};