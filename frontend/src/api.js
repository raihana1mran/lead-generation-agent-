const API_BASE = 'http://localhost:8000/api';

// ─── helper ──────────────────────────────────────────────────────────────────
const post = (url, body) =>
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

// ─── LEADS ───────────────────────────────────────────────────────────────────
export const fetchLeads = async () => {
  const res = await fetch(`${API_BASE}/leads/`);
  if (!res.ok) throw new Error('Failed to fetch leads');
  const data = await res.json();
  // Attach nested intelligence if present
  return Array.isArray(data) ? data : [];
};

export const createLead = async (leadData) => {
  const res = await post(`${API_BASE}/leads/`, leadData);
  if (!res.ok) throw new Error('Failed to create lead');
  return res.json();
};

export const autoGenerateLeads = async (query) => {
  const res = await post(`${API_BASE}/leads/auto-generate`, { query });
  if (!res.ok) throw new Error('Failed to start auto-generation');
  return res.json();
};

// ─── PROPOSALS ───────────────────────────────────────────────────────────────
export const fetchProposals = async () => {
  const res = await fetch(`${API_BASE}/proposals/`);
  if (!res.ok) throw new Error('Failed to fetch proposals');
  const data = await res.json();
  return Array.isArray(data) ? data : [];
};

// ─── BUSINESS PROFILE ────────────────────────────────────────────────────────
export const fetchBusinessProfile = async () => {
  const res = await fetch(`${API_BASE}/business/`);
  if (!res.ok) throw new Error('Failed to fetch business profile');
  const data = await res.json();
  return Array.isArray(data) && data.length > 0 ? data[0] : null;
};

export const createBusinessProfile = async (profileData) => {
  const res = await post(`${API_BASE}/business/`, profileData);
  if (!res.ok) throw new Error('Failed to save business profile');
  return res.json();
};

// ─── GEOGRAPHY CONFIG ────────────────────────────────────────────────────────
export const fetchGeographyConfig = async () => {
  try {
    const res = await fetch(`${API_BASE}/geography/`);
    if (!res.ok) return null;
    const data = await res.json();
    return Array.isArray(data) && data.length > 0 ? data[0] : null;
  } catch { return null; }
};

export const saveGeographyConfig = async (config) => {
  const res = await post(`${API_BASE}/geography/`, config);
  if (!res.ok) throw new Error('Failed to save geography config');
  return res.json();
};

// ─── ANALYTICS ───────────────────────────────────────────────────────────────
export const fetchDashboardStats = async () => {
  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
};

// ─── WORKFLOW ─────────────────────────────────────────────────────────────────
export const approveHitl = async (leadId) => {
  const res = await post(`${API_BASE}/workflow/hitl/approve/${leadId}`, {});
  if (!res.ok) throw new Error('Failed to approve lead');
  return res.json();
};

export const fetchWorkflowStatus = async (leadId) => {
  const res = await fetch(`${API_BASE}/workflow/status/${leadId}`);
  if (!res.ok) throw new Error('Failed to fetch workflow status');
  return res.json();
};

export const deleteLead = async (leadId) => {
  const res = await fetch(`${API_BASE}/leads/${leadId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete lead');
  return res.json();
};

export const clearAllLeads = async () => {
  const res = await fetch(`${API_BASE}/leads/`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to clear leads');
  return res.json();
};

// ─── SMTP SETTINGS ───────────────────────────────────────────────────────────
export const fetchSmtpSettings = async () => {
  const res = await fetch(`${API_BASE}/outreach/smtp`);
  if (!res.ok) throw new Error('Failed to fetch SMTP settings');
  return res.json();
};

export const saveSmtpSettings = async (settings) => {
  const res = await post(`${API_BASE}/outreach/smtp`, settings);
  if (!res.ok) throw new Error('Failed to save SMTP settings');
  return res.json();
};
