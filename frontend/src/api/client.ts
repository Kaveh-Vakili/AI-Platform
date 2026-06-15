import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

// --- Auth ---
export const login = (email: string, password: string) =>
  api.post("/auth/login", { email, password }).then((r) => r.data);

export const register = (email: string, password: string) =>
  api.post("/auth/register", { email, password }).then((r) => r.data);

export const getMe = () => api.get("/auth/me").then((r) => r.data);

// --- Workspaces ---
export const getWorkspaces = () =>
  api.get("/workspaces").then((r) => r.data);

export const createWorkspace = (name: string, description?: string) =>
  api.post("/workspaces", { name, description }).then((r) => r.data);

// --- Documents ---
export const getDocuments = (workspaceId: string) =>
  api.get(`/workspaces/${workspaceId}/documents`).then((r) => r.data);

export const uploadDocument = (workspaceId: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post(`/workspaces/${workspaceId}/documents`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const deleteDocument = (workspaceId: string, docId: string) =>
  api.delete(`/workspaces/${workspaceId}/documents/${docId}`);

export const embedDocuments = (workspaceId: string) =>
  api.post(`/workspaces/${workspaceId}/embed`).then((r) => r.data);

// --- Chat ---
export const sendMessage = (workspaceId: string, message: string) =>
  api
    .post(`/workspaces/${workspaceId}/chat`, { message })
    .then((r) => r.data);

// --- Workflows ---
export const getTemplates = () =>
  api.get("/workflows/templates").then((r) => r.data);

export const startRun = (
  templateId: string,
  workspaceId: string,
  focus: string
) =>
  api
    .post("/workflows/run", { template_id: templateId, workspace_id: workspaceId, focus })
    .then((r) => r.data);

export const getRun = (runId: string) =>
  api.get(`/workflows/runs/${runId}`).then((r) => r.data);

export const getRunSteps = (runId: string) =>
  api.get(`/workflows/runs/${runId}/steps`).then((r) => r.data);

export const getRunExecutions = (runId: string) =>
  api.get(`/workflows/runs/${runId}/executions`).then((r) => r.data);

// --- Monitoring ---
export const getTokenUsage = (runId: string) =>
  api.get(`/workflow-runs/${runId}/token-usage`).then((r) => r.data);

export const getCostSummary = (runId: string) =>
  api.get(`/workflow-runs/${runId}/cost-summary`).then((r) => r.data);

export const getHallucinationChecks = (runId: string) =>
  api.get(`/workflow-runs/${runId}/hallucination-checks`).then((r) => r.data);

// --- Audit ---
export const getAuditLogs = (workspaceId: string) =>
  api.get(`/workspaces/${workspaceId}/audit-logs`).then((r) => r.data);