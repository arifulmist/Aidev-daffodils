import React, { useState, useEffect } from 'react';
import {
  Search, ShieldCheck, AlertTriangle, ArrowRight, CheckCircle2, XCircle,
  HelpCircle, Cpu, FileText, Database, ShieldAlert, Sparkles, Check,
  CornerDownRight, BarChart2, GitFork, UserCheck, Layers, ExternalLink
} from 'lucide-react';

export default function InvestigationTab({
  initialTransactionId,
  initialComplaintText,
  initialComplaintId,
  onCaseLogged
}) {
  const [transactionId, setTransactionId] = useState(initialTransactionId || 'TX10082');
  const [complaintText, setComplaintText] = useState(initialComplaintText || '');
  const [complaintId, setComplaintId] = useState(initialComplaintId || '');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Candidate matcher state (Phase 8)
  const [candidates, setCandidates] = useState([]);
  const [searchingCandidates, setSearchingCandidates] = useState(false);

  // Demo cases state (Phase 17)
  const [demoCases, setDemoCases] = useState([]);
  const [selectedDemo, setSelectedDemo] = useState('case-1');

  // Feedback / routing modal state
  const [routingSuccess, setRoutingSuccess] = useState(null);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideRootCause, setOverrideRootCause] = useState('MERCHANT_ACK_FAILURE');
  const [overrideTeam, setOverrideTeam] = useState('Reconciliation');
  const [overrideNotes, setOverrideNotes] = useState('');

  // What-If Causal Counterfactual State
  const [showWhatIfModal, setShowWhatIfModal] = useState(false);
  const [whatIfHypotheses, setWhatIfHypotheses] = useState({
    merchant_ack_received: false,
    reversal_succeeded: false,
    balance_sufficient: false,
    network_timeout_cleared: false
  });
  const [whatIfResult, setWhatIfResult] = useState(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);

  // Exportable Audit Dossier State
  const [showDossierModal, setShowDossierModal] = useState(false);
  const [dossierData, setDossierData] = useState(null);
  const [dossierLoading, setDossierLoading] = useState(false);

  const handleRunWhatIf = async () => {
    if (!result) return;
    setWhatIfLoading(true);
    try {
      const res = await fetch('/api/investigations/what-if', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: result.transaction.transaction_id,
          hypotheses: whatIfHypotheses
        })
      });
      const data = await res.json();
      if (data && data.simulation) {
        setWhatIfResult(data.simulation);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setWhatIfLoading(false);
    }
  };

  const handleOpenDossier = async () => {
    if (!result) return;
    setShowDossierModal(true);
    setDossierLoading(true);
    try {
      const res = await fetch(`/api/investigations/${result.transaction.transaction_id}/dossier`);
      const data = await res.json();
      setDossierData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setDossierLoading(false);
    }
  };

  // Fetch demo cases on mount
  useEffect(() => {
    fetch('/api/demo/cases')
      .then((r) => r.json())
      .then((data) => {
        if (data.demo_cases) {
          setDemoCases(data.demo_cases);
        }
      })
      .catch((e) => console.error(e));
  }, []);

  // Run initial investigation
  useEffect(() => {
    if (initialTransactionId) {
      setTransactionId(initialTransactionId);
      if (initialComplaintText) setComplaintText(initialComplaintText);
      runInvestigation(initialTransactionId, initialComplaintText);
    } else {
      runInvestigation('TX10082', 'I paid ৳2,500 to the shop around 2:30 PM but they didn\'t receive it. Money was deducted and no reversal was received.');
    }
  }, [initialTransactionId]);

  const loadDemo = (demo) => {
    setSelectedDemo(demo.id);
    setTransactionId(demo.transaction_id);
    setComplaintText(demo.complaint_text);
    setCandidates([]);
    runInvestigation(demo.transaction_id, demo.complaint_text);
  };

  const runInvestigation = async (txId, text) => {
    if (!txId || !txId.trim()) {
      handleMatchLookup(text);
      return;
    }

    setLoading(true);
    setError(null);
    setRoutingSuccess(null);
    setCandidates([]);

    try {
      const res = await fetch('/api/investigations/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: txId.trim(),
          complaint_text: text || complaintText || null,
          complaint_id: complaintId || null
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Investigation failed');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Phase 8: Candidate matching when no exact transaction ID is supplied
  const handleMatchLookup = async (textToMatch) => {
    setSearchingCandidates(true);
    setError(null);
    try {
      const res = await fetch('/api/transactions/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          complaint_text: textToMatch || complaintText
        })
      });
      const data = await res.json();
      if (data.candidates && data.candidates.length > 0) {
        setCandidates(data.candidates);
      } else {
        setError('No candidate transactions matched the customer complaint. Try specifying Transaction ID.');
      }
    } catch (e) {
      setError('Failed to query candidate transactions.');
    } finally {
      setSearchingCandidates(false);
    }
  };

  // Accept and route recommendation
  const handleAcceptRouting = async () => {
    if (!result) return;
    try {
      const res = await fetch('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          complaint_id: complaintId || null,
          transaction_id: result.transaction.transaction_id,
          root_cause: result.ml_prediction.predicted_root_cause,
          confidence: result.ml_prediction.confidence,
          priority: result.llm_report.risk_assessment === 'HIGH' ? 'HIGH' : 'MEDIUM',
          assigned_team: result.llm_report.assigned_team,
          recommendation: result.llm_report.recommended_action
        })
      });
      const data = await res.json();
      setRoutingSuccess(`Case ${data.case_id} created and dispatched to ${data.assigned_team}!`);
      if (onCaseLogged) onCaseLogged();
    } catch (e) {
      alert('Failed to log case');
    }
  };

  // Submit Human-in-the-Loop Feedback / Override (Phase 15)
  const handleFeedbackSubmit = async (actionType) => {
    if (!result) return;
    try {
      // First ensure case is saved
      const caseRes = await fetch('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          complaint_id: complaintId || null,
          transaction_id: result.transaction.transaction_id,
          root_cause: result.ml_prediction.predicted_root_cause,
          confidence: result.ml_prediction.confidence,
          priority: 'MEDIUM',
          assigned_team: result.llm_report.assigned_team,
          recommendation: result.llm_report.recommended_action
        })
      });
      const caseData = await caseRes.json();

      // Submit feedback log
      await fetch(`/api/cases/${caseData.case_id}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operator_action: actionType,
          actual_root_cause: actionType === 'ACCEPTED' ? result.ml_prediction.predicted_root_cause : overrideRootCause,
          actual_team: actionType === 'ACCEPTED' ? result.llm_report.assigned_team : overrideTeam,
          resolved_by: 'Senior_Officer_Tariq',
          resolution_notes: overrideNotes || 'Officer confirmed resolution through automated AI investigator.'
        })
      });

      setShowOverrideModal(false);
      setRoutingSuccess(`Feedback recorded into model continuous learning dataset! Case ${caseData.case_id} resolved.`);
      if (onCaseLogged) onCaseLogged();
    } catch (e) {
      alert('Failed to record feedback');
    }
  };

  return (
    <div className="space-y-6">
      {/* Phase 17 Demo Scenarios Quick-Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
              Pre-Configured Hackathon Demo Scenarios
            </span>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">1-Click Evaluation Benchmark</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
          {demoCases.map((d) => {
            const isSelected = selectedDemo === d.id;
            return (
              <button
                key={d.id}
                onClick={() => loadDemo(d)}
                className={`p-3 rounded-xl text-left transition-all border ${
                  isSelected
                    ? 'bg-amber-500/15 border-amber-500 text-white shadow-md shadow-amber-500/10'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300 hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-amber-400 font-semibold">
                    {d.transaction_id}
                  </span>
                  <span className="text-[10px] font-medium text-slate-400">৳{d.amount.toLocaleString()}</span>
                </div>
                <div className="text-xs font-bold truncate text-white">{d.title.split(':')[1] || d.title}</div>
                <div className="text-[10px] text-slate-400 mt-1 line-clamp-1">{d.expected_root_cause}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Search & Investigation Input Bar */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            runInvestigation(transactionId, complaintText);
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
            {/* Transaction ID input */}
            <div className="lg:col-span-3">
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Transaction ID (Optional if in text)
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={transactionId}
                  onChange={(e) => setTransactionId(e.target.value)}
                  placeholder="e.g. TX10082"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 placeholder:text-slate-600"
                />
              </div>
            </div>

            {/* Customer Complaint Text input */}
            <div className="lg:col-span-7">
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Customer Complaint (English / Banglish / Fuzzy Cues)
              </label>
              <input
                type="text"
                value={complaintText}
                onChange={(e) => setComplaintText(e.target.value)}
                placeholder="e.g. I paid ৳2,500 to shop around 2:30 PM but they didn't receive it..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 placeholder:text-slate-600"
              />
            </div>

            {/* Investigate Button */}
            <div className="lg:col-span-2 flex items-end">
              <button
                type="submit"
                disabled={loading || searchingCandidates}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 transition-all hover:scale-[1.02] disabled:opacity-50"
              >
                {loading ? (
                  <span className="inline-block animate-spin w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                <span>{loading ? 'Analyzing...' : 'Investigate'}</span>
              </button>
            </div>
          </div>
        </form>

        {/* Phase 8 Candidate Transaction Matcher Cards */}
        {candidates.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-amber-300 font-semibold flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5" />
                Multiple Candidate Transactions Matched (Select to Confirm)
              </span>
              <span className="text-[11px] text-slate-500 font-mono">Multi-Criteria Candidate Matching</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {candidates.map((cand) => (
                <div
                  key={cand.transaction_id}
                  className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-amber-500/50 transition-all cursor-pointer"
                  onClick={() => {
                    setTransactionId(cand.transaction_id);
                    runInvestigation(cand.transaction_id, complaintText);
                  }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-mono font-bold text-amber-400">{cand.transaction_id}</span>
                    <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Match: {(cand.match_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 font-medium">৳{cand.amount.toLocaleString()} • {cand.status}</div>
                  <div className="text-[11px] text-slate-500 font-mono mt-1">{cand.time_formatted} • Merchant {cand.merchant_id}</div>
                  <div className="text-[10px] text-slate-400 mt-1 italic">{cand.match_reason}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Routing Success Banner */}
      {routingSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span className="text-sm font-medium">{routingSuccess}</span>
          </div>
          <span className="text-xs font-mono px-2 py-1 rounded bg-emerald-500/20 text-emerald-300">
            SLA Clock Started
          </span>
        </div>
      )}

      {/* Main Investigation Results Grid */}
      {result && (
        <div className="space-y-6">
          {/* Enhanced Action & Intelligence Ribbon */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => { setShowWhatIfModal(true); setWhatIfResult(null); }}
                className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-purple-500/20 to-purple-600/20 hover:from-purple-500/30 hover:to-purple-600/30 border border-purple-500/40 text-purple-200 text-xs font-mono font-bold flex items-center gap-2 transition-all shadow-md shadow-purple-500/10 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span>Test What-If Counterfactual 🧪</span>
              </button>
              <button
                onClick={handleOpenDossier}
                className="px-3.5 py-2 rounded-xl bg-slate-950/80 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono font-semibold flex items-center gap-2 transition-all cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5 text-amber-400" />
                <span>Export Audit Dossier (SHA-256) 📄</span>
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
              {result.self_healing && result.self_healing.eligible && (
                <span className="px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 font-bold animate-pulse">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  <span>⚡ Instant Micro-Dispute Settlement Qualified (৳{result.evidence.amount})</span>
                </span>
              )}
              {result.privacy && result.privacy.pii_redacted && (
                <span className="px-2.5 py-1 rounded-lg bg-blue-500/15 text-blue-300 border border-blue-500/30 flex items-center gap-1 text-[11px]">
                  <ShieldCheck className="w-3 h-3 text-blue-400" />
                  <span>Privacy Shield: PII Sanitized</span>
                </span>
              )}
              <span className="px-2.5 py-1 rounded-lg bg-slate-950 text-slate-400 border border-slate-800 text-[11px]">
                SLA: BB Circular 04/2022
              </span>
            </div>
          </div>

          {/* Top Bar: Structured Evidence Chips (Phase 4) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {/* Chip 1: Wallet Debited */}
            <div className={`p-4 rounded-xl border ${
              result.evidence.wallet_debited
                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-900/60 border-slate-800 text-slate-400'
            }`}>
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">Wallet Debit</div>
              <div className="text-lg font-bold mt-1 flex items-center gap-2">
                {result.evidence.wallet_debited ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <XCircle className="w-5 h-5 text-slate-500" />}
                <span>{result.evidence.wallet_debited ? 'Confirmed' : 'No Debit'}</span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">৳{result.evidence.amount.toLocaleString()}</div>
            </div>

            {/* Chip 2: Merchant Received */}
            <div className={`p-4 rounded-xl border ${
              result.evidence.merchant_received
                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
            }`}>
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">Merchant Capture</div>
              <div className="text-lg font-bold mt-1 flex items-center gap-2">
                {result.evidence.merchant_received ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <XCircle className="w-5 h-5 text-rose-400" />}
                <span>{result.evidence.merchant_received ? 'Captured' : 'Failed / Timeout'}</span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">ACK: {result.evidence.merchant_ack ? 'YES' : 'NO'}</div>
            </div>

            {/* Chip 3: Reversal Found */}
            <div className={`p-4 rounded-xl border ${
              result.evidence.reversal_found
                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                : 'bg-amber-950/20 border-amber-500/30 text-amber-300'
            }`}>
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">Auto-Reversal</div>
              <div className="text-lg font-bold mt-1 flex items-center gap-2">
                {result.evidence.reversal_found ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertTriangle className="w-5 h-5 text-amber-400" />}
                <span>{result.evidence.reversal_found ? 'Completed' : 'Not Found'}</span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">SLA Check: {result.evidence.reversal_found ? 'Closed' : 'Action Required'}</div>
            </div>

            {/* Chip 4: Failure Code */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-300">
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400">Switch Failure Code</div>
              <div className="text-lg font-mono font-bold mt-1 text-amber-400 truncate">
                {result.evidence.failure_code}
              </div>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">Duration: {result.evidence.duration_sec.toFixed(1)}s</div>
            </div>
          </div>

          {/* Dual Column: Timeline & Intelligence Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Reconstructed Chronological Event Timeline (Phase 4) */}
            <div className="lg:col-span-5 rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                    Reconstructed Event Timeline
                  </h3>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  {result.timeline.length} Events Logged
                </span>
              </div>

              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {result.timeline.map((ev, idx) => {
                  const isFail = ev.event_status === 'FAILED' || ev.event_type.includes('TIMEOUT') || ev.event_type.includes('FAIL');
                  const isWarn = ev.event_status === 'PENDING' || ev.event_type.includes('LAG');
                  return (
                    <div key={idx} className="relative group">
                      {/* Timeline dot */}
                      <span className={`absolute -left-6 top-1 w-3.5 h-3.5 rounded-full border-2 border-slate-950 ${
                        isFail ? 'bg-rose-500' : isWarn ? 'bg-amber-400' : 'bg-emerald-400'
                      }`} />

                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-slate-300">
                            {ev.timestamp}
                          </span>
                          <span className={`text-[10px] font-mono uppercase px-1.5 py-0.2 rounded font-semibold ${
                            isFail
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              : isWarn
                              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                              : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          }`}>
                            {ev.event_type}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300">
                          {ev.human_description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* NLP Intent Badge */}
              <div className="pt-3 border-t border-slate-800/80">
                <div className="text-[11px] font-mono text-slate-400 mb-1">Customer Complaint Classification:</div>
                <div className="flex items-center justify-between text-xs font-mono p-2.5 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-amber-300 font-semibold">{result.complaint_analysis.category}</span>
                  <span className="text-slate-400">Confidence: {(result.complaint_analysis.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* Right Column: AI Analysis, Consensus, Anomaly & Recommendations */}
            <div className="lg:col-span-7 space-y-5">
              {/* Box 1: Multi-Model Consensus & Explainability (Phase 5 vs Phase 6, Phase 14) */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                      Root Cause Diagnostics & Model Consensus
                    </h3>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                    result.explainability.agreement
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}>
                    {result.explainability.agreement_label}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Rule Engine Verdict */}
                  <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                      <span>Deterministic Rule Engine</span>
                      <span className="text-amber-400 font-semibold">{result.rule_engine.rule_matched}</span>
                    </div>
                    <div className="text-base font-mono font-extrabold text-white">
                      {result.rule_engine.predicted_root_cause}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      Baseline logic confidence: {(result.rule_engine.confidence * 100).toFixed(0)}%
                    </div>
                  </div>

                  {/* ML Random Forest Verdict */}
                  <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                      <span>Random Forest Classifier</span>
                      <span className="text-emerald-400 font-semibold">100 Trees</span>
                    </div>
                    <div className="text-base font-mono font-extrabold text-amber-400">
                      {result.ml_prediction.predicted_root_cause}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      ML Confidence: {(result.ml_prediction.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Driving Features Attribution (Phase 14 Explainability) */}
                {result.ml_prediction.driving_features && result.ml_prediction.driving_features.length > 0 && (
                  <div>
                    <div className="text-[11px] font-mono text-slate-400 mb-2 flex items-center justify-between">
                      <span>Key Features Driving Prediction:</span>
                      <span className="text-[10px] text-slate-500 font-mono">Relative Importance Weights</span>
                    </div>
                    <div className="space-y-1.5">
                      {result.ml_prediction.driving_features.map((feat, idx) => (
                        <div key={idx} className="flex items-center gap-3 text-xs font-mono">
                          <span className="w-40 text-slate-300 truncate">{feat.feature}</span>
                          <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-amber-500 to-amber-300 rounded-full"
                              style={{ width: `${Math.min(100, feat.importance * 250)}%` }}
                            />
                          </div>
                          <span className="text-slate-400 w-12 text-right">{(feat.importance * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Local Tree Feature Attribution Waterfall (SHAP-style local contributions) */}
                {result.explainability.local_feature_attributions && result.explainability.local_feature_attributions.length > 0 && (
                  <div className="pt-3 border-t border-slate-800">
                    <div className="text-[11px] font-mono text-slate-400 mb-2 flex items-center justify-between">
                      <span className="font-bold text-amber-300">Local Tree Feature Attribution Waterfall:</span>
                      <span className="text-[10px] text-slate-500 font-mono">Sample-Specific Impact</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {result.explainability.local_feature_attributions.map((attr, idx) => (
                        <div key={idx} className="p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-mono flex items-center justify-between">
                          <span className="text-slate-300 truncate">{attr.feature}={attr.value}</span>
                          <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                            attr.direction === 'SUPPORTS_CAUSE'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-rose-500/20 text-rose-300'
                          }`}>
                            {attr.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Confidence Abstain Warning (Bangladesh Bank SLA Risk Control) */}
                {result.explainability.abstain_recommended && (
                  <div className="p-3 rounded-xl bg-amber-500/15 border border-amber-500/40 text-amber-300 text-xs font-mono flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>SLA Risk Warning: Confidence is under 75%. Senior officer verification required under Bangladesh Bank guidelines.</span>
                  </div>
                )}
              </div>

              {/* Box 2: Operational Anomaly Gauge (Phase 9) */}
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-xl">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    result.anomaly_detection.is_anomaly
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}>
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                        Operational Anomaly Monitor
                      </span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        result.anomaly_detection.is_anomaly
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {result.anomaly_detection.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-0.5">
                      {result.anomaly_detection.is_anomaly
                        ? result.anomaly_detection.reasons.join(' • ')
                        : 'Behavior consistent with normal historical velocity curve.'}
                    </p>
                  </div>
                </div>

                <div className="text-right pl-4">
                  <div className="text-xl font-mono font-extrabold text-white">
                    {(result.anomaly_detection.anomaly_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">Outlier Score</div>
                </div>
              </div>

              {/* Box 3: Historical Similar Cases (Phase 10 RAG) */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <GitFork className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                      Historical Similar Cases (RAG Retrieval)
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">Top 3 Precedents</span>
                </div>

                <div className="space-y-2">
                  {result.similar_cases.map((sc, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-amber-400">{sc.case_code} — {sc.title}</span>
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          {(sc.similarity_score * 100).toFixed(0)}% Similarity
                        </span>
                      </div>
                      <p className="text-slate-300 text-[11px]">{sc.symptoms}</p>
                      <div className="text-emerald-400 text-[11px] font-medium flex items-center gap-1.5 pt-0.5">
                        <Check className="w-3.5 h-3.5" />
                        <span>Resolution Precedent: {sc.resolution} ({sc.assigned_team})</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Box 4: Evidence-Grounded AI Analyst Briefing (Phase 11) */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/30 border border-amber-500/40 shadow-2xl space-y-4">
                <div className="flex items-center justify-between border-b border-amber-500/20 pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-amber-400" />
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                      Evidence-Grounded AI Analyst Recommendation
                    </h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono font-bold">
                    Target Team: {result.llm_report.assigned_team}
                  </span>
                </div>

                <div className="space-y-3 text-xs leading-relaxed">
                  <div>
                    <span className="text-slate-400 font-mono uppercase text-[10px] block">Case Summary:</span>
                    <p className="text-slate-200 mt-0.5">{result.llm_report.case_summary}</p>
                  </div>

                  <div>
                    <span className="text-slate-400 font-mono uppercase text-[10px] block">Ground Investigation Evidence:</span>
                    <ul className="list-disc list-inside space-y-0.5 text-slate-300 mt-0.5">
                      {result.llm_report.investigation_facts.map((fact, fIdx) => (
                        <li key={fIdx}>{fact}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950/80 border border-amber-500/30">
                    <span className="text-amber-400 font-mono uppercase text-[10px] font-bold block">
                      Recommended Operational Action:
                    </span>
                    <p className="text-white font-medium mt-1 text-sm">
                      {result.llm_report.recommended_action}
                    </p>
                  </div>

                  <div>
                    <span className="text-slate-400 font-mono uppercase text-[10px] block">Reasoning Trace:</span>
                    <p className="text-slate-400 text-[11px] mt-0.5">{result.llm_report.reasoning}</p>
                  </div>
                </div>

                {/* Operator Human-in-the-Loop Action Bar (Phase 15) */}
                <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs text-slate-400 font-mono">
                    Human Oversight: Officer Tariq
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowOverrideModal(true)}
                      className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
                    >
                      [✗ Incorrect / Override]
                    </button>
                    <button
                      onClick={handleAcceptRouting}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold shadow-lg shadow-amber-500/20 transition-all hover:scale-105"
                    >
                      <CheckCircle2 className="w-4 h-4 fill-slate-950" />
                      <span>[✓ Accept & Route Case]</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Human-in-the-Loop Feedback / Override Modal (Phase 15) */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-amber-400" />
                Human-in-the-Loop Feedback & Correction
              </h3>
              <button
                onClick={() => setShowOverrideModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Provide operator correction. This will be stored in the feedback loop table to continuously retrain and improve future model accuracy.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-mono">Actual Correct Root Cause:</label>
                <select
                  value={overrideRootCause}
                  onChange={(e) => setOverrideRootCause(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono focus:border-amber-500 focus:outline-none"
                >
                  <option value="MERCHANT_ACK_FAILURE">MERCHANT_ACK_FAILURE</option>
                  <option value="MISSING_REVERSAL">MISSING_REVERSAL</option>
                  <option value="STATUS_SYNC_DELAY">STATUS_SYNC_DELAY</option>
                  <option value="DUPLICATE_TRANSACTION">DUPLICATE_TRANSACTION</option>
                  <option value="NETWORK_TIMEOUT">NETWORK_TIMEOUT</option>
                  <option value="INSUFFICIENT_BALANCE">INSUFFICIENT_BALANCE</option>
                  <option value="SUSPICIOUS_ACTIVITY">SUSPICIOUS_ACTIVITY</option>
                  <option value="SUCCESS">SUCCESS</option>
                  <option value="UNKNOWN_FAILURE">UNKNOWN_FAILURE</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Actual Team to Route:</label>
                <select
                  value={overrideTeam}
                  onChange={(e) => setOverrideTeam(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono focus:border-amber-500 focus:outline-none"
                >
                  <option value="Reconciliation">Reconciliation</option>
                  <option value="Merchant Operations">Merchant Operations</option>
                  <option value="Fraud & Security">Fraud & Security</option>
                  <option value="Network & Core Banking">Network & Core Banking</option>
                  <option value="Customer Care Tier 2">Customer Care Tier 2</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Operator Notes / Rationale:</label>
                <textarea
                  rows="3"
                  value={overrideNotes}
                  onChange={(e) => setOverrideNotes(e.target.value)}
                  placeholder="Explain why the prediction was overridden based on manual logs..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder:text-slate-600 focus:border-amber-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
              <button
                onClick={() => setShowOverrideModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={() => handleFeedbackSubmit('CORRECTED')}
                className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs"
              >
                Submit Correction & Retrain Loop
              </button>
            </div>
          </div>
        </div>
      )}

      {/* What-If Causal Counterfactual Simulation Modal */}
      {showWhatIfModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl max-w-2xl w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white font-mono">
                  Causal Counterfactual "What-If" Reasoning Simulator
                </h3>
              </div>
              <button onClick={() => setShowWhatIfModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <p className="text-xs text-slate-300">
              Test hypothetical mutations on the event graph. Recalculates the causal consensus and shows whether the failure would resolve or shift to an alternate pathway.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <label className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition-colors">
                <input
                  type="checkbox"
                  checked={whatIfHypotheses.merchant_ack_received}
                  onChange={(e) => setWhatIfHypotheses({ ...whatIfHypotheses, merchant_ack_received: e.target.checked })}
                  className="mt-0.5 rounded text-amber-500 focus:ring-0"
                />
                <div>
                  <div className="text-white font-semibold">Merchant ACK Received</div>
                  <div className="text-slate-400 text-[11px]">Simulates POS gateway responding HTTP 200 within timeout</div>
                </div>
              </label>

              <label className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition-colors">
                <input
                  type="checkbox"
                  checked={whatIfHypotheses.reversal_succeeded}
                  onChange={(e) => setWhatIfHypotheses({ ...whatIfHypotheses, reversal_succeeded: e.target.checked })}
                  className="mt-0.5 rounded text-amber-500 focus:ring-0"
                />
                <div>
                  <div className="text-white font-semibold">Automated Reversal Succeeded</div>
                  <div className="text-slate-400 text-[11px]">Simulates core banking rollback worker executing in ledger</div>
                </div>
              </label>

              <label className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition-colors">
                <input
                  type="checkbox"
                  checked={whatIfHypotheses.balance_sufficient}
                  onChange={(e) => setWhatIfHypotheses({ ...whatIfHypotheses, balance_sufficient: e.target.checked })}
                  className="mt-0.5 rounded text-amber-500 focus:ring-0"
                />
                <div>
                  <div className="text-white font-semibold">Balance Validated</div>
                  <div className="text-slate-400 text-[11px]">Simulates customer having sufficient balance + VAT fees</div>
                </div>
              </label>

              <label className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-3 cursor-pointer hover:border-slate-700 transition-colors">
                <input
                  type="checkbox"
                  checked={whatIfHypotheses.network_timeout_cleared}
                  onChange={(e) => setWhatIfHypotheses({ ...whatIfHypotheses, network_timeout_cleared: e.target.checked })}
                  className="mt-0.5 rounded text-amber-500 focus:ring-0"
                />
                <div>
                  <div className="text-white font-semibold">Network Latency Cleared</div>
                  <div className="text-slate-400 text-[11px]">Simulates telecom switch latency remaining under 1,500ms</div>
                </div>
              </label>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleRunWhatIf}
                disabled={whatIfLoading}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-400 hover:to-purple-500 text-white font-bold text-xs font-mono shadow-lg transition-all"
              >
                {whatIfLoading ? 'Simulating Causal Graph...' : 'Execute What-If Simulation ⚡'}
              </button>
            </div>

            {whatIfResult && (
              <div className="p-4 rounded-2xl bg-purple-950/30 border border-purple-500/40 space-y-3 animate-in fade-in">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Simulation Causal Shift:</span>
                  <span className="font-extrabold text-purple-300 px-2.5 py-0.5 rounded-full bg-purple-500/20 border border-purple-500/30">
                    {whatIfResult.causal_outcome}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-slate-500 text-[11px]">Original Root Cause:</div>
                    <div className="text-rose-400 font-bold text-sm mt-0.5">{whatIfResult.original_root_cause}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-slate-500 text-[11px]">Counterfactual Root Cause:</div>
                    <div className="text-emerald-400 font-bold text-sm mt-0.5">{whatIfResult.counterfactual_root_cause}</div>
                  </div>
                </div>
                <p className="text-xs text-slate-200 font-mono bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  💡 {whatIfResult.explanation}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Exportable Dispute Audit Dossier Modal */}
      {showDossierModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl max-w-3xl w-full p-6 space-y-4 shadow-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white font-mono">
                  Dispute Audit Dossier (Bangladesh Bank Compliance Packet)
                </h3>
              </div>
              <button onClick={() => setShowDossierModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {dossierLoading ? (
              <div className="py-12 text-center text-slate-400 font-mono text-xs">Generating verifiable cryptographic dossier...</div>
            ) : dossierData ? (
              <div className="flex-1 overflow-y-auto space-y-4 text-xs font-mono">
                {/* Fingerprint Header */}
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Dossier ID: <strong className="text-white">{dossierData.dossier_id}</strong></span>
                    <span className="text-emerald-400 font-bold">Regulatory Target: {dossierData.sla_resolution_target_days} Days SLA</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Framework: <span className="text-amber-300">{dossierData.regulatory_framework}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 break-all">
                    SHA-256 Fingerprint: <span className="text-amber-400">{dossierData.cryptographic_fingerprint_sha256}</span>
                  </div>
                </div>

                {/* Consensus Findings */}
                <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
                  <div className="text-xs font-bold text-white uppercase tracking-wider">Investigative Determination</div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400">Primary Root Cause:</span>
                      <div className="text-amber-300 font-bold text-sm mt-0.5">{dossierData.consensus_determination.primary_root_cause}</div>
                    </div>
                    <div>
                      <span className="text-slate-400">Assigned Team:</span>
                      <div className="text-emerald-300 font-bold text-sm mt-0.5">{dossierData.consensus_determination.assigned_department}</div>
                    </div>
                  </div>
                </div>

                {/* Event Audit Trail */}
                <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
                  <div className="text-xs font-bold text-white uppercase tracking-wider">Chronological Ledger Telemetry ({dossierData.chronological_event_audit.length} events)</div>
                  <div className="space-y-1 max-h-36 overflow-y-auto">
                    {dossierData.chronological_event_audit.map((ev, i) => (
                      <div key={i} className="flex items-center justify-between text-[11px] py-1 border-b border-slate-900">
                        <span className="text-slate-400">{ev.timestamp} • {ev.event_type}</span>
                        <span className={`font-bold ${ev.event_status === 'SUCCESS' ? 'text-emerald-400' : 'text-rose-400'}`}>{ev.event_status}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Compliance Signoff */}
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-[11px] flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 flex-shrink-0 text-emerald-400" />
                  <span>Verified: Immutable audit log entry generated. Ready for Bangladesh Bank compliance filing or inter-bank settlement.</span>
                </div>
              </div>
            ) : null}

            <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs font-mono"
              >
                Print / Save PDF Dossier 🖨️
              </button>
              <button
                onClick={() => setShowDossierModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
