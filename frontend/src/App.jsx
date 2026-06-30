import React, { useState, useEffect } from 'react';
import {
  Activity, Users, FileText, Settings, Rocket, CheckCircle, Clock, Plus, X, Search,
  FileDown, BarChart2, Mail, Phone, Globe, Brain, Zap, Target, TrendingUp,
  ChevronRight, AlertCircle, Star, MapPin, Briefcase, Bot, Shield, Eye, Trash2
} from 'lucide-react';
import { fetchLeads, approveHitl, createLead, autoGenerateLeads, fetchProposals, fetchBusinessProfile, createBusinessProfile, fetchGeographyConfig, saveGeographyConfig, deleteLead, clearAllLeads, fetchSmtpSettings, saveSmtpSettings } from './api';
import './App.css';

// ─── SIDEBAR ──────────────────────────────────────────────────────────────────
const Sidebar = ({ currentView, setCurrentView }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'leads', label: 'Lead Pipeline', icon: Users },
    { id: 'intelligence', label: 'AI Intelligence', icon: Brain },
    { id: 'proposals', label: 'Proposals', icon: FileText },
    { id: 'crm', label: 'CRM Pipeline', icon: Target },
    { id: 'analytics', label: 'Analytics', icon: BarChart2 },
    { id: 'outreach', label: 'Outreach', icon: Mail },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];
  return (
    <div className="sidebar">
      <div className="brand">
        <div className="brand-icon-wrap"><Rocket size={22} /></div>
        <span>LeadForge <span className="brand-ai">AI</span></span>
      </div>
      <div className="nav-label">CORE SYSTEM</div>
      <div className="nav-links">
        {navItems.map(({ id, label, icon: Icon }) => (
          <div key={id} className={`nav-item ${currentView === id ? 'active' : ''}`} onClick={() => setCurrentView(id)}>
            <Icon size={18} />
            <span>{label}</span>
            {currentView === id && <div className="nav-indicator" />}
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <div className="agent-status">
          <div className="status-dot pulse" />
          <span>12 Agents Active</span>
        </div>
      </div>
    </div>
  );
};

// ─── HELPERS ──────────────────────────────────────────────────────────────────
const getBadgeClass = (state) => {
  if (['INGESTED'].includes(state)) return 'badge-gray';
  if (['ENRICHMENT', 'SCORING'].includes(state)) return 'badge-blue';
  if (['DECISION'].includes(state)) return 'badge-orange';
  if (['PROPOSAL'].includes(state)) return 'badge-purple';
  if (['OUTREACH', 'FOLLOW_UP'].includes(state)) return 'badge-pink';
  if (['RESPONSE', 'CRM_UPDATE'].includes(state)) return 'badge-teal';
  if (['CLOSED_LOOP'].includes(state)) return 'badge-green';
  if (['NURTURE'].includes(state)) return 'badge-yellow';
  return 'badge-gray';
};

const ScoreBar = ({ score }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%' }}>
      <div style={{ flex: 1, height: '12px', background: '#ffeedd', borderRadius: '9999px', overflow: 'hidden' }}>
        <div style={{ width: `${score || 0}%`, height: '100%', background: 'linear-gradient(90deg, #b8b8ff 0%, #9381ff 100%)', borderRadius: '9999px', transition: 'width 0.5s' }} />
      </div>
      <span style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: 700, minWidth: '28px', fontFamily: 'Courier New, Courier, monospace' }}>{score || '-'}</span>
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, sub, color = 'var(--accent-primary)' }) => (
  <div className="glass-panel stat-card hover-lift">
    <div className="stat-icon" style={{ background: `${color}22`, color }}><Icon size={20} /></div>
    <div className="stat-body">
      <div className="stat-value">{value}</div>
      <div className="stat-title">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  </div>
);

// ─── LEAD DETAIL DRAWER ───────────────────────────────────────────────────────
const LeadDrawer = ({ lead, onClose }) => {
  if (!lead) return null;
  const intel = lead.intelligence;
  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={e => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h2>{lead.company_name}</h2>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{lead.source} · {lead.location || 'Unknown Location'}</span>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="drawer-section">
          <div className="drawer-section-title"><Zap size={14} /> Workflow State</div>
          <span className={`badge ${getBadgeClass(lead.workflow_state)}`}>{lead.workflow_state}</span>
        </div>

        {intel?.lead_score != null && (
          <div className="drawer-section">
            <div className="drawer-section-title"><Star size={14} /> Lead Score</div>
            <ScoreBar score={intel.lead_score} />
            <div style={{ marginTop: '6px' }}>
              <span className={`badge ${intel.lead_score >= 70 ? 'badge-green' : intel.lead_score >= 40 ? 'badge-orange' : 'badge-gray'}`}>
                {intel.classification || 'Unscored'}
              </span>
            </div>
          </div>
        )}

        {intel?.website_audit && (
          <div className="drawer-section">
            <div className="drawer-section-title"><Globe size={14} /> Website Audit</div>
            <div className="intel-grid">
              <div className="intel-chip"><span>Design</span><strong>{intel.website_audit.design_score}/100</strong></div>
              <div className="intel-chip"><span>Speed</span><strong>{intel.website_audit.speed_score}/100</strong></div>
              <div className="intel-chip"><span>Mobile</span><strong>{intel.website_audit.mobile_responsive ? '✓ Yes' : '✗ No'}</strong></div>
            </div>
            {intel.website_audit.ux_issues?.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>UX Issues</div>
                {intel.website_audit.ux_issues.map((issue, i) => (
                  <div key={i} className="issue-tag"><AlertCircle size={11} /> {issue}</div>
                ))}
              </div>
            )}
          </div>
        )}

        {intel?.ai_opportunities && (
          <div className="drawer-section">
            <div className="drawer-section-title"><Bot size={14} /> AI Opportunities</div>
            <div className="intel-grid">
              <div className="intel-chip"><span>Support Bot</span><strong>{intel.ai_opportunities.support_bottleneck ? '🔥 Needed' : '—'}</strong></div>
              <div className="intel-chip"><span>Sales Agent</span><strong>{intel.ai_opportunities.sales_bottleneck ? '🔥 Needed' : '—'}</strong></div>
              <div className="intel-chip"><span>HR Agent</span><strong>{intel.ai_opportunities.hr_bottleneck ? '🔥 Needed' : '—'}</strong></div>
            </div>
            {intel.ai_opportunities.recommended_agents?.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                {intel.ai_opportunities.recommended_agents.map((a, i) => (
                  <span key={i} className="badge badge-purple" style={{ marginRight: '6px', marginBottom: '4px' }}>{a}</span>
                ))}
              </div>
            )}
            {intel.ai_opportunities.roi_estimation && (
              <div style={{ marginTop: '8px', fontSize: '0.8rem', color: '#10b981' }}>
                Estimated ROI: {intel.ai_opportunities.roi_estimation}
              </div>
            )}
          </div>
        )}

        {intel?.personalized_message && (
          <div className="drawer-section">
            <div className="drawer-section-title"><Mail size={14} /> Personalized Outreach</div>
            <div className="outreach-block">
              <div className="outreach-label">Subject Line</div>
              <div className="outreach-content">{intel.personalized_message.subject_line}</div>
            </div>
            <div className="outreach-block" style={{ marginTop: '10px' }}>
              <div className="outreach-label">Email Body</div>
              <div className="outreach-content" style={{ whiteSpace: 'pre-wrap', maxHeight: '150px', overflowY: 'auto' }}>{intel.personalized_message.email_body}</div>
            </div>
            <div className="outreach-block" style={{ marginTop: '10px' }}>
              <div className="outreach-label">LinkedIn DM</div>
              <div className="outreach-content">{intel.personalized_message.linkedin_dm}</div>
            </div>
          </div>
        )}

        {intel?.crm_update && (
          <div className="drawer-section">
            <div className="drawer-section-title"><Target size={14} /> CRM Update</div>
            <div className="intel-grid">
              <div className="intel-chip"><span>Stage</span><strong>{intel.crm_update.pipeline_stage}</strong></div>
              <div className="intel-chip"><span>Close %</span><strong>{intel.crm_update.probability_to_close}%</strong></div>
            </div>
          </div>
        )}

        <div className="drawer-section">
          <div className="drawer-section-title"><Briefcase size={14} /> Contact Info</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {lead.website && <span><Globe size={13} style={{ marginRight: '6px' }} />{lead.website}</span>}
            {lead.email && <span><Mail size={13} style={{ marginRight: '6px' }} />{lead.email}</span>}
            {lead.contact_person && <span><Users size={13} style={{ marginRight: '6px' }} />{lead.contact_person}</span>}
            {lead.linkedin && <span><ChevronRight size={13} style={{ marginRight: '6px' }} />{lead.linkedin}</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── DASHBOARD ────────────────────────────────────────────────────────────────
const Dashboard = ({ leads }) => {
  const total = leads.length;
  const hot = leads.filter(l => l.workflow_state === 'PROPOSAL' || l.workflow_state === 'OUTREACH').length;
  const inProgress = leads.filter(l => ['ENRICHMENT', 'SCORING', 'DECISION'].includes(l.workflow_state)).length;
  const closed = leads.filter(l => l.workflow_state === 'CLOSED_LOOP').length;
  const hitl = leads.filter(l => l.requires_hitl).length;
  const states = ['INGESTED','ENRICHMENT','SCORING','DECISION','PROPOSAL','OUTREACH','FOLLOW_UP','RESPONSE','CRM_UPDATE','CLOSED_LOOP'];
  const stateCounts = states.map(s => ({ state: s, count: leads.filter(l => l.workflow_state === s).length }));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Mission Control</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>Real-time overview of your 12-Agent Revenue Machine</p>
        </div>
        <div className="status-live"><div className="status-dot pulse" /> Live</div>
      </div>

      <div className="stats-grid">
        <StatCard icon={Users} label="Total Leads" value={total} sub="in pipeline" color="#6366f1" />
        <StatCard icon={Zap} label="Hot Prospects" value={hot} sub="ready for proposal" color="#ef4444" />
        <StatCard icon={Activity} label="In Progress" value={inProgress} sub="agents working" color="#f59e0b" />
        <StatCard icon={CheckCircle} label="Closed Loop" value={closed} sub="fully processed" color="#10b981" />
        <StatCard icon={Shield} label="HITL Queue" value={hitl} sub="awaiting approval" color="#8b5cf6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginTop: '24px' }}>
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h2 style={{ marginBottom: '24px', fontSize: '1rem' }}>10-State Pipeline Funnel</h2>
          {stateCounts.map(({ state, count }) => (
            <div key={state} style={{ marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '0.8rem' }}>
                <span className={`badge ${getBadgeClass(state)}`} style={{ fontSize: '0.7rem' }}>{state}</span>
                <span style={{ color: 'var(--text-muted)' }}>{count} leads</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.07)', borderRadius: '3px' }}>
                <div style={{
                  width: total > 0 ? `${(count / total) * 100}%` : '0%',
                  height: '100%',
                  background: 'var(--accent-primary)',
                  borderRadius: '3px',
                  transition: 'width 0.6s ease'
                }} />
              </div>
            </div>
          ))}
        </div>

        <div className="glass-panel" style={{ padding: '28px' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '1rem' }}>Active Agents</h2>
          {[
            { name: 'Lead Discovery', status: 'Searching', color: '#6366f1' },
            { name: 'Website Audit', status: 'Analyzing', color: '#f59e0b' },
            { name: 'AI Opportunity', status: 'Detecting', color: '#10b981' },
            { name: 'Lead Enrichment', status: 'Enriching', color: '#3b82f6' },
            { name: 'Lead Scoring', status: 'Scoring', color: '#ef4444' },
            { name: 'Personalization', status: 'Writing', color: '#8b5cf6' },
            { name: 'Outreach', status: 'Sending', color: '#ec4899' },
            { name: 'Follow-up', status: 'Scheduling', color: '#14b8a6' },
            { name: 'Meeting Booking', status: 'Qualifying', color: '#f97316' },
            { name: 'Proposal Gen', status: 'Generating', color: '#a855f7' },
            { name: 'CRM Agent', status: 'Updating', color: '#06b6d4' },
            { name: 'Analytics', status: 'Reporting', color: '#84cc16' },
          ].map(({ name, status, color }) => (
            <div key={name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color }} />
                <span style={{ fontSize: '0.82rem' }}>{name}</span>
              </div>
              <span style={{ fontSize: '0.72rem', color, background: `${color}22`, padding: '2px 8px', borderRadius: '20px' }}>{status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── AUTO GENERATE MODAL ──────────────────────────────────────────────────────
const AutoGenerateModal = ({ isOpen, onClose, onSubmit }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const presets = [
    'ecommerce businesses without a website instagram tiktok',
    'restaurants without online ordering system',
    'startups who need AI automation and agentic solutions',
    'local businesses without mobile-friendly websites'
  ];
  if (!isOpen) return null;
  const handleSubmit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    await onSubmit(query);
    setLoading(false);
    onClose();
  };
  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '560px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ background: 'var(--accent-primary)22', padding: '8px', borderRadius: '10px' }}><Brain size={20} color="var(--accent-primary)" /></div>
            <div>
              <h2>AI Lead Discovery</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>Searches Instagram, TikTok, LinkedIn, Quora + Google across Tier 1 countries</p>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>
        <div className="form-group">
          <label>Describe Your Ideal Target</label>
          <input type="text" placeholder="e.g. ecommerce businesses without website instagram tiktok" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
        </div>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>Quick Presets</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {presets.map(p => (
              <button key={p} className="preset-chip" onClick={() => setQuery(p)}>{p.slice(0, 40)}...</button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSubmit} disabled={loading || !query.trim()}>
            {loading ? <span className="spinner" /> : <><Search size={16} /> Launch AI Search</>}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── ADD LEAD MODAL ───────────────────────────────────────────────────────────
const LeadModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({ company_name: '', website: '', email: '', contact_person: '', location: '', source: 'Manual' });
  if (!isOpen) return null;
  const upd = (k, v) => setFormData(p => ({ ...p, [k]: v }));
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Add Lead Manually</h2>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>
        {[['company_name','Company Name','Acme Corp'],['website','Website','https://acme.com'],['email','Email','ceo@acme.com'],['contact_person','Contact Person','John Doe'],['location','Location','New York, USA']].map(([k, l, p]) => (
          <div className="form-group" key={k}>
            <label>{l}</label>
            <input type="text" placeholder={p} value={formData[k]} onChange={e => upd(k, e.target.value)} />
          </div>
        ))}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={() => { if (formData.company_name) { onSubmit(formData); onClose(); } }}>
            <Plus size={16} /> Ingest Lead
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── LEAD PIPELINE ────────────────────────────────────────────────────────────
const LeadsTable = ({ leads, onApprove, onAddLead, onAutoGenerate, onDelete, onClearAll }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAutoModalOpen, setIsAutoModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);
  const [filter, setFilter] = useState('ALL');

  const states = ['ALL', 'INGESTED', 'ENRICHMENT', 'SCORING', 'DECISION', 'PROPOSAL', 'OUTREACH', 'CLOSED_LOOP'];
  const filtered = filter === 'ALL' ? leads : leads.filter(l => l.workflow_state === filter);

  const exportToCSV = () => {
    if (leads.length === 0) return alert("No leads to export");
    const headers = ["ID", "Company Name", "Website", "Source", "Workflow State", "Location", "Email", "Score", "Classification"];
    const rows = leads.map(l => [
      l.id,
      `"${(l.company_name || '').replace(/"/g, '""')}"`,
      l.website || '',
      l.source || '',
      l.workflow_state || '',
      l.location || '',
      l.email || '',
      l.intelligence?.lead_score || '',
      l.intelligence?.classification || ''
    ]);
    const csvContent = [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "leads_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToJSON = () => {
    if (leads.length === 0) return alert("No leads to export");
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(leads, null, 2))}`;
    const link = document.createElement("a");
    link.setAttribute("href", jsonString);
    link.setAttribute("download", "leads_export.json");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Lead Pipeline</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>15-State Autonomous Workflow Engine</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-secondary hover-lift" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-hot)', borderColor: 'var(--status-hot)' }} onClick={() => { if (confirm("Clear all scraped data? This cannot be undone.")) onClearAll(); }}>
            <Trash2 size={16} /> Clear All
          </button>
          <button className="btn-secondary hover-lift" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={exportToCSV}>
            <FileDown size={16} /> Export CSV
          </button>
          <button className="btn-secondary hover-lift" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={exportToJSON}>
            <FileDown size={16} /> Export JSON
          </button>
          <button className="btn-secondary hover-lift" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#8b5cf6', borderColor: '#8b5cf6' }} onClick={() => setIsAutoModalOpen(true)}>
            <Brain size={16} /> AI Discover
          </button>
          <button className="btn-primary hover-lift" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => setIsModalOpen(true)}>
            <Plus size={16} /> Add Lead
          </button>
        </div>
      </div>

      <div className="filter-bar">
        {states.map(s => (
          <button key={s} className={`filter-chip ${filter === s ? 'active' : ''}`} onClick={() => setFilter(s)}>
            {s === 'ALL' ? `All (${leads.length})` : `${s} (${leads.filter(l => l.workflow_state === s).length})`}
          </button>
        ))}
      </div>

      <LeadModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSubmit={onAddLead} />
      <AutoGenerateModal isOpen={isAutoModalOpen} onClose={() => setIsAutoModalOpen(false)} onSubmit={onAutoGenerate} />
      <LeadDrawer lead={selectedLead} onClose={() => setSelectedLead(null)} />

      <div className="glass-panel table-container">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Company</th>
              <th>Source</th>
              <th>State</th>
              <th>Score</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan="7" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
                <Brain size={40} style={{ opacity: 0.2, marginBottom: '12px' }} />
                <div>No leads yet. Hit AI Discover to start!</div>
              </td></tr>
            ) : filtered.map(lead => (
              <tr key={lead.id} className="table-row-hover" onClick={() => setSelectedLead(lead)}>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>#{lead.id}</td>
                <td>
                  <div style={{ fontWeight: 600 }}>{lead.company_name}</div>
                  {lead.website && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{lead.website}</div>}
                </td>
                <td><span className="source-tag">{lead.source || 'Manual'}</span></td>
                <td><span className={`badge ${getBadgeClass(lead.workflow_state)}`}>{lead.workflow_state}</span></td>
                <td style={{ minWidth: '120px' }}><ScoreBar score={lead.intelligence?.lead_score} /></td>
                <td>
                  {lead.requires_hitl
                    ? <span style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}><Clock size={14} /> Needs Approval</span>
                    : <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}><CheckCircle size={14} /> Autonomous</span>}
                </td>
                <td onClick={e => e.stopPropagation()}>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="icon-btn" title="View Details" onClick={() => setSelectedLead(lead)}><Eye size={15} /></button>
                    <button className="icon-btn" title="Delete Lead" style={{ color: 'var(--status-hot)' }} onClick={() => onDelete(lead.id)}><Trash2 size={15} /></button>
                    {lead.requires_hitl && ['SCORING', 'DECISION', 'PERSONALIZATION'].includes(lead.workflow_state) && (
                      <button className="btn-primary" style={{ padding: '4px 12px', fontSize: '0.78rem' }} onClick={() => onApprove(lead.id)}>Approve</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── AI INTELLIGENCE ──────────────────────────────────────────────────────────
const IntelligenceView = ({ leads, onApprove }) => {
  const enriched = leads.filter(l => l.intelligence?.website_audit);
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Intelligence Center</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>Website Audits, AI Opportunities & Personalized Outreach</p>
        </div>
      </div>
      {enriched.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Brain size={48} style={{ opacity: 0.15, marginBottom: '16px' }} />
          <p>No deep intelligence data yet. Generate leads and let the agents run!</p>
        </div>
      ) : (
        <div className="intel-cards-grid">
          {enriched.map(lead => (
            <div key={lead.id} className="glass-panel intel-card hover-lift">
              <div className="intel-card-header">
                <div>
                  <div style={{ fontWeight: 700 }}>{lead.company_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{lead.source}</div>
                </div>
                <ScoreBar score={lead.intelligence.lead_score} />
              </div>
              {lead.intelligence.website_audit && (
                <div style={{ marginTop: '16px' }}>
                  <div className="drawer-section-title"><Globe size={12} /> Website Audit</div>
                  <div className="intel-grid">
                    <div className="intel-chip"><span>Design</span><strong>{lead.intelligence.website_audit.design_score}</strong></div>
                    <div className="intel-chip"><span>Speed</span><strong>{lead.intelligence.website_audit.speed_score}</strong></div>
                  </div>
                </div>
              )}
              {lead.intelligence.ai_opportunities?.recommended_agents?.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <div className="drawer-section-title"><Bot size={12} /> Recommended Agents</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                    {lead.intelligence.ai_opportunities.recommended_agents.map((a, i) => (
                      <span key={i} className="badge badge-purple" style={{ fontSize: '0.7rem' }}>{a}</span>
                    ))}
                  </div>
                </div>
              )}
              {lead.intelligence.personalized_message?.subject_line && (
                <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(99,102,241,0.08)', borderRadius: '8px', fontSize: '0.78rem', color: 'var(--text-muted)', borderLeft: '2px solid var(--accent-primary)' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>📧 {lead.intelligence.personalized_message.subject_line}</strong>
                </div>
              )}
              {lead.requires_hitl && ['SCORING', 'DECISION', 'PERSONALIZATION'].includes(lead.workflow_state) && (
                <button className="btn-primary" style={{ padding: '8px 12px', fontSize: '0.8rem', marginTop: '16px', width: '100%', justifyContent: 'center' }} onClick={() => onApprove(lead.id)}>
                  Approve Lead
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── PROPOSALS ────────────────────────────────────────────────────────────────
const ProposalsView = () => {
  const [proposals, setProposals] = useState([]);
  const [selected, setSelected] = useState(null);
  useEffect(() => { fetchProposals().then(setProposals).catch(console.error); }, []);
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Proposals</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>AI-generated personalized proposals for Hot Leads</p>
        </div>
      </div>
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal-content" style={{ maxWidth: '700px', maxHeight: '80vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selected.title}</h2>
              <button className="icon-btn" onClick={() => setSelected(null)}><X size={20} /></button>
            </div>
            {selected.content && Object.entries(selected.content).map(([k, v]) => (
              <div key={k} className="drawer-section">
                <div className="drawer-section-title">{k.replace(/_/g, ' ').toUpperCase()}</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>{typeof v === 'string' ? v : Array.isArray(v) ? v.join(', ') : JSON.stringify(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="glass-panel table-container">
        <table>
          <thead>
            <tr><th>#</th><th>Lead ID</th><th>Proposal Title</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {proposals.length === 0 ? (
              <tr><td colSpan="4" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
                <FileText size={40} style={{ opacity: 0.15, marginBottom: '12px' }} />
                <div>No proposals yet. Hot Leads automatically trigger proposal generation.</div>
              </td></tr>
            ) : proposals.map(p => (
              <tr key={p.id} className="table-row-hover">
                <td>#{p.id}</td>
                <td>Lead #{p.lead_id}</td>
                <td style={{ fontWeight: 600 }}>{p.title}</td>
                <td>
                  <button className="btn-secondary hover-lift" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }} onClick={() => setSelected(p)}>
                    <Eye size={14} /> View Proposal
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── CRM PIPELINE ─────────────────────────────────────────────────────────────
const CRMView = ({ leads, onApprove }) => {
  const stages = ['Lead Found', 'Qualified', 'Contacted', 'Replied', 'Meeting Scheduled', 'Proposal Sent', 'Won'];
  const getStage = (lead) => {
    const ws = lead.workflow_state;
    if (ws === 'INGESTED') return 'Lead Found';
    if (['ENRICHMENT', 'SCORING', 'DECISION', 'NURTURE'].includes(ws)) return 'Qualified';
    if (ws === 'OUTREACH') return 'Contacted';
    if (ws === 'FOLLOW_UP') return 'Replied';
    if (['RESPONSE', 'MEETING_BOOKED'].includes(ws)) return 'Meeting Scheduled';
    if (['PROPOSAL', 'PERSONALIZATION'].includes(ws)) return 'Proposal Sent';
    if (['CLOSED_LOOP', 'CRM_UPDATE', 'ANALYTICS'].includes(ws)) return 'Won';
    return 'Lead Found';
  };
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>CRM Pipeline</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>Revenue pipeline across all 7 stages</p>
        </div>
      </div>
      <div className="crm-board">
        {stages.map(stage => {
          const stageLeads = leads.filter(l => getStage(l) === stage);
          return (
            <div key={stage} className="crm-column">
              <div className="crm-column-header">
                <span>{stage}</span>
                <span className="crm-count">{stageLeads.length}</span>
              </div>
              <div className="crm-cards">
                {stageLeads.map(lead => (
                  <div key={lead.id} className="crm-card hover-lift">
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '6px' }}>{lead.company_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>{lead.source}</div>
                    <ScoreBar score={lead.intelligence?.lead_score} />
                    {lead.intelligence?.crm_update?.probability_to_close != null && (
                      <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#10b981' }}>
                        {lead.intelligence.crm_update.probability_to_close}% close probability
                      </div>
                    )}
                    {lead.requires_hitl && ['SCORING', 'DECISION', 'PERSONALIZATION'].includes(lead.workflow_state) && (
                      <button className="btn-primary" style={{ padding: '6px 10px', fontSize: '0.75rem', marginTop: '10px', width: '100%', justifyContent: 'center' }} onClick={() => onApprove(lead.id)}>
                        Approve
                      </button>
                    )}
                  </div>
                ))}
                {stageLeads.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '0.75rem', opacity: 0.5 }}>Empty</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─── ANALYTICS ────────────────────────────────────────────────────────────────
const AnalyticsView = ({ leads }) => {
  const total = leads.length;
  const hot = leads.filter(l => ['PROPOSAL', 'OUTREACH', 'FOLLOW_UP'].includes(l.workflow_state)).length;
  const closed = leads.filter(l => l.workflow_state === 'CLOSED_LOOP').length;
  const convRate = total > 0 ? ((closed / total) * 100).toFixed(1) : 0;
  const sourceCounts = leads.reduce((acc, l) => { acc[l.source || 'Manual'] = (acc[l.source || 'Manual'] || 0) + 1; return acc; }, {});

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>Pipeline performance metrics</p>
        </div>
      </div>
      <div className="stats-grid" style={{ marginBottom: '24px' }}>
        <StatCard icon={Users} label="Leads Found" value={total} color="#6366f1" />
        <StatCard icon={TrendingUp} label="Hot Prospects" value={hot} color="#ef4444" />
        <StatCard icon={CheckCircle} label="Closed Loop" value={closed} color="#10b981" />
        <StatCard icon={BarChart2} label="Conversion Rate" value={`${convRate}%`} color="#f59e0b" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '1rem' }}>Leads by Source</h2>
          {Object.entries(sourceCounts).length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No data yet.</div>
          ) : Object.entries(sourceCounts).map(([source, count]) => (
            <div key={source} style={{ marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '0.82rem' }}>
                <span>{source}</span>
                <span style={{ color: 'var(--text-muted)' }}>{count}</span>
              </div>
              <div style={{ height: '8px', background: 'rgba(255,255,255,0.07)', borderRadius: '4px' }}>
                <div style={{ width: `${(count / total) * 100}%`, height: '100%', background: 'var(--accent-primary)', borderRadius: '4px' }} />
              </div>
            </div>
          ))}
        </div>

        <div className="glass-panel" style={{ padding: '28px' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '1rem' }}>Monthly Targets</h2>
          {[
            { label: 'Leads Found', target: 5000, current: total },
            { label: 'Qualified Leads', target: 1000, current: hot + closed },
            { label: 'Positive Replies', target: 100, current: Math.max(0, closed * 2) },
            { label: 'Meetings Booked', target: 30, current: Math.max(0, closed) },
            { label: 'Proposals Sent', target: 10, current: leads.filter(l => l.workflow_state === 'PROPOSAL').length },
            { label: 'New Clients', target: 5, current: Math.max(0, closed) },
          ].map(({ label, target, current }) => (
            <div key={label} style={{ marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '0.82rem' }}>
                <span>{label}</span>
                <span style={{ color: 'var(--text-muted)' }}>{current} / {target}</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.07)', borderRadius: '3px' }}>
                <div style={{ width: `${Math.min(100, (current / target) * 100)}%`, height: '100%', background: current >= target ? '#10b981' : 'var(--accent-primary)', borderRadius: '3px' }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── OUTREACH VIEW ────────────────────────────────────────────────────────────
const OutreachView = ({ leads, onApprove }) => {
  const outreached = leads.filter(l => l.intelligence?.personalized_message);
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Outreach Center</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>All personalized AI-written emails and LinkedIn messages</p>
        </div>
      </div>
      {outreached.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Mail size={48} style={{ opacity: 0.15, marginBottom: '16px' }} />
          <p>No outreach generated yet. Generate leads and wait for the AI pipeline to run.</p>
        </div>
      ) : outreached.map(lead => (
        <div key={lead.id} className="glass-panel hover-lift" style={{ padding: '24px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <span style={{ fontWeight: 700 }}>{lead.company_name}</span>
              <span className={`badge ${getBadgeClass(lead.workflow_state)}`} style={{ marginLeft: '12px' }}>{lead.workflow_state}</span>
              {lead.requires_hitl && lead.workflow_state === 'PERSONALIZATION' && (
                <button className="btn-primary" style={{ padding: '4px 12px', fontSize: '0.78rem', marginLeft: '16px' }} onClick={() => onApprove(lead.id)}>
                  Approve & Send
                </button>
              )}
            </div>
            <ScoreBar score={lead.intelligence.lead_score} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="outreach-block">
              <div className="outreach-label"><Mail size={12} style={{ marginRight: '4px' }} /> Email – {lead.intelligence.personalized_message.subject_line}</div>
              <div className="outreach-content" style={{ fontSize: '0.8rem', maxHeight: '80px', overflowY: 'auto' }}>{lead.intelligence.personalized_message.email_body}</div>
            </div>
            <div className="outreach-block">
              <div className="outreach-label"><ChevronRight size={12} style={{ marginRight: '4px' }} /> LinkedIn DM</div>
              <div className="outreach-content" style={{ fontSize: '0.8rem', maxHeight: '80px', overflowY: 'auto' }}>{lead.intelligence.personalized_message.linkedin_dm}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// ─── SETTINGS ─────────────────────────────────────────────────────────────────
const SettingsForm = () => {
  const [formData, setFormData] = useState({ company_name: '', industry: '', services: '', target_customers: '', pricing: '', geography: '', website: '' });
  const [geoConfig, setGeoConfig] = useState({
    tier1_countries: '',
    tier2_countries: '',
    tier3_countries: '',
    active_tiers: [],
    platforms: []
  });
  const [smtpConfig, setSmtpConfig] = useState({ email_user: '', email_password: '' });
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [loadingGeo, setLoadingGeo] = useState(false);
  const [loadingSmtp, setLoadingSmtp] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [geoSaved, setGeoSaved] = useState(false);
  const [smtpSaved, setSmtpSaved] = useState(false);

  useEffect(() => {
    fetchBusinessProfile().then(p => {
      if (p) setFormData({ ...p, services: (p.services || []).join(', ') });
    }).catch(console.error);

    fetchGeographyConfig().then(g => {
      if (g) {
        setGeoConfig({
          tier1_countries: (g.tier1_countries || []).join(', '),
          tier2_countries: (g.tier2_countries || []).join(', '),
          tier3_countries: (g.tier3_countries || []).join(', '),
          active_tiers: g.active_tiers || [],
          platforms: g.platforms || []
        });
      }
    }).catch(console.error);

    fetchSmtpSettings().then(s => {
      if (s) setSmtpConfig(s);
    }).catch(console.error);
  }, []);

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setLoadingProfile(true);
    try {
      await createBusinessProfile({ ...formData, services: formData.services.split(',').map(s => s.trim()) });
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
    } catch (err) { alert('Failed to save profile: ' + err.message); }
    setLoadingProfile(false);
  };

  const handleGeoSubmit = async (e) => {
    e.preventDefault();
    setLoadingGeo(true);
    try {
      await saveGeographyConfig({
        tier1_countries: geoConfig.tier1_countries.split(',').map(c => c.trim()).filter(Boolean),
        tier2_countries: geoConfig.tier2_countries.split(',').map(c => c.trim()).filter(Boolean),
        tier3_countries: geoConfig.tier3_countries.split(',').map(c => c.trim()).filter(Boolean),
        active_tiers: geoConfig.active_tiers,
        platforms: geoConfig.platforms
      });
      setGeoSaved(true);
      setTimeout(() => setGeoSaved(false), 3000);
    } catch (err) { alert('Failed to save geography config: ' + err.message); }
    setLoadingGeo(false);
  };

  const handleSmtpSubmit = async (e) => {
    e.preventDefault();
    setLoadingSmtp(true);
    try {
      await saveSmtpSettings(smtpConfig);
      setSmtpSaved(true);
      setTimeout(() => setSmtpSaved(false), 3000);
    } catch (err) { alert('Failed to save SMTP settings: ' + err.message); }
    setLoadingSmtp(false);
  };

  const toggleTier = (tier) => {
    setGeoConfig(prev => {
      const active = prev.active_tiers.includes(tier)
        ? prev.active_tiers.filter(t => t !== tier)
        : [...prev.active_tiers, tier];
      return { ...prev, active_tiers: active };
    });
  };

  const togglePlatform = (plat) => {
    setGeoConfig(prev => {
      const active = prev.platforms.includes(plat)
        ? prev.platforms.filter(p => p !== plat)
        : [...prev.platforms, plat];
      return { ...prev, platforms: active };
    });
  };

  const updProfile = (k, v) => setFormData(p => ({ ...p, [k]: v }));
  const updGeo = (k, v) => setGeoConfig(p => ({ ...p, [k]: v }));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>System Settings</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>Configure your profile & target sources</p>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ marginBottom: '24px', fontSize: '1rem' }}>Your Business Profile</h2>
          <form onSubmit={handleProfileSubmit}>
            {[
              ['company_name', 'Company Name', 'LeadForge AI'],
              ['industry', 'Industry', 'AI & Web Development'],
              ['services', 'Services (comma-separated)', 'Web Dev, AI Agents, SaaS, Ecommerce'],
              ['target_customers', 'Target Customers', 'SMBs in Tier 1 countries'],
              ['pricing', 'Pricing Model', '$2,000 - $50,000 per project'],
              ['geography', 'Geography', 'USA, UK, Canada, Australia, Germany'],
              ['website', 'Website URL', 'https://yourcompany.com'],
            ].map(([k, l, p]) => (
              <div className="form-group" key={k}>
                <label>{l}</label>
                <input type="text" placeholder={p} value={formData[k]} onChange={e => updProfile(k, e.target.value)} required />
              </div>
            ))}
            <button type="submit" className="btn-primary" disabled={loadingProfile} style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}>
              {loadingProfile ? <span className="spinner" /> : profileSaved ? <><CheckCircle size={16} /> Profile Saved!</> : 'Save & Regenerate ICP'}
            </button>
          </form>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel" style={{ padding: '32px' }}>
            <h2 style={{ marginBottom: '24px', fontSize: '1rem' }}>Geography & Sources Config</h2>
            <form onSubmit={handleGeoSubmit}>
              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label style={{ marginBottom: '10px', display: 'block' }}>Active Country Tiers</label>
                <div style={{ display: 'flex', gap: '16px' }}>
                  {['tier1', 'tier2', 'tier3'].map(t => (
                    <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: 'pointer' }}>
                      <input type="checkbox" checked={geoConfig.active_tiers.includes(t)} onChange={() => toggleTier(t)} />
                      {t.toUpperCase()}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Tier 1 Countries (comma-separated)</label>
                <input type="text" value={geoConfig.tier1_countries} onChange={e => updGeo('tier1_countries', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Tier 2 Countries (comma-separated)</label>
                <input type="text" value={geoConfig.tier2_countries} onChange={e => updGeo('tier2_countries', e.target.value)} />
              </div>
              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label>Tier 3 Countries (comma-separated)</label>
                <input type="text" value={geoConfig.tier3_countries} onChange={e => updGeo('tier3_countries', e.target.value)} />
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label style={{ marginBottom: '10px', display: 'block' }}>Target Discovery Platforms</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  {['linkedin', 'instagram', 'tiktok', 'quora', 'pinterest', 'googlemaps'].map(p => {
                    const labelMap = {
                      linkedin: 'LinkedIn',
                      instagram: 'Instagram',
                      tiktok: 'TikTok',
                      quora: 'Quora',
                      pinterest: 'Pinterest',
                      googlemaps: 'Google Maps'
                    };
                    return (
                      <label key={p} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                        <input type="checkbox" checked={geoConfig.platforms.includes(p)} onChange={() => togglePlatform(p)} />
                        {labelMap[p] || p}
                      </label>
                    );
                  })}
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loadingGeo} style={{ width: '100%', justifyContent: 'center' }}>
                {loadingGeo ? <span className="spinner" /> : geoSaved ? <><CheckCircle size={16} /> Saved Config!</> : 'Save Sources & Countries'}
              </button>
            </form>
          </div>

          <div className="glass-panel" style={{ padding: '32px' }}>
            <h2 style={{ marginBottom: '24px', fontSize: '1rem' }}>Google SMTP Integration</h2>
            <form onSubmit={handleSmtpSubmit}>
              <div className="form-group">
                <label>Gmail Address</label>
                <input type="email" placeholder="your.name@gmail.com" value={smtpConfig.email_user} onChange={e => setSmtpConfig(p => ({ ...p, email_user: e.target.value }))} required />
              </div>
              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label>App Password</label>
                <input type="password" placeholder="xxxx xxxx xxxx xxxx" value={smtpConfig.email_password} onChange={e => setSmtpConfig(p => ({ ...p, email_password: e.target.value }))} required />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
                  Generate an App Password in your Google Account Security settings.
                </span>
              </div>
              <button type="submit" className="btn-primary" disabled={loadingSmtp} style={{ width: '100%', justifyContent: 'center' }}>
                {loadingSmtp ? <span className="spinner" /> : smtpSaved ? <><CheckCircle size={16} /> SMTP Configured!</> : 'Save SMTP Settings'}
              </button>
            </form>
          </div>

          <div className="glass-panel" style={{ padding: '28px' }}>
            <h2 style={{ marginBottom: '16px', fontSize: '1rem' }}>AI Model Configuration</h2>
            <div className="intel-chip" style={{ marginBottom: '8px' }}><span>Provider</span><strong>OpenRouter</strong></div>
            <div className="intel-chip" style={{ marginBottom: '8px' }}><span>Model</span><strong>Llama 3.3 70B</strong></div>
            <div className="intel-chip" style={{ marginBottom: '8px' }}><span>Retry Logic</span><strong>3x Auto-Retry</strong></div>
            <div className="intel-chip"><span>Max Leads/Search</span><strong>100</strong></div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── ROOT APP ─────────────────────────────────────────────────────────────────
function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try { setLeads(await fetchLeads()); }
    catch (e) { console.error('API error', e); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (id) => { try { await approveHitl(id); loadData(); } catch (e) { alert(e.message); } };
  const handleAddLead = async (data) => { try { await createLead(data); loadData(); } catch (e) { alert(e.message); } };
  const handleAutoGenerate = async (query) => {
    try { 
      await autoGenerateLeads(query);
      alert('🚀 AI agents are now scanning the web! New leads will appear in the pipeline within 60 seconds.');
    } catch (e) { alert(e.message); }
  };

  const handleDeleteLead = async (id) => {
    try {
      await deleteLead(id);
      loadData();
    } catch (e) {
      alert("Failed to delete lead: " + e.message);
    }
  };

  const handleClearAllLeads = async () => {
    try {
      await clearAllLeads();
      loadData();
    } catch (e) {
      alert("Failed to clear leads: " + e.message);
    }
  };

  return (
    <div className="app-container">
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <div className="main-content">
        {loading ? (
          <div className="loading-screen"><span className="spinner large" /><p>Initializing Agent Network...</p></div>
        ) : (
          <>
            {currentView === 'dashboard' && <Dashboard leads={leads} />}
            {currentView === 'leads' && <LeadsTable leads={leads} onApprove={handleApprove} onAddLead={handleAddLead} onAutoGenerate={handleAutoGenerate} onDelete={handleDeleteLead} onClearAll={handleClearAllLeads} />}
            {currentView === 'intelligence' && <IntelligenceView leads={leads} onApprove={handleApprove} />}
            {currentView === 'proposals' && <ProposalsView />}
            {currentView === 'crm' && <CRMView leads={leads} onApprove={handleApprove} />}
            {currentView === 'analytics' && <AnalyticsView leads={leads} />}
            {currentView === 'outreach' && <OutreachView leads={leads} onApprove={handleApprove} />}
            {currentView === 'settings' && <SettingsForm />}
          </>
        )}
      </div>
    </div>
  );
}

export default App;
