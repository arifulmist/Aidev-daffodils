import React, { useEffect, useState } from 'react';
import { FolderCheck, CheckCircle2, AlertTriangle, RefreshCw, Clock, ArrowRight, UserCheck, ShieldCheck } from 'lucide-react';

export default function CasesTab() {
  const [cases, setCases] = useState([]);
  const [feedbackHistory, setFeedbackHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [casesRes, fbRes] = await Promise.all([
        fetch('/api/cases'),
        fetch('/api/cases/feedback/history')
      ]);
      if (casesRes.ok) setCases(await casesRes.json());
      if (fbRes.ok) setFeedbackHistory(await fbRes.json());
    } catch (e) {
      console.error('Failed to fetch cases:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 text-xs font-mono font-semibold">
              OPERATIONAL AUDIT & DISPATCH
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">
            Case Management & Continuous Model Feedback Loop
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Operations officer audit log, team dispatch tracking, and retraining dataset curation.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="mt-3 sm:mt-0 flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Records</span>
        </button>
      </div>

      {/* Active Dispute Cases Table */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FolderCheck className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Active Dispatched Dispute Cases
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">{cases.length} Logged Cases</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 font-mono uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Case ID</th>
                <th className="px-5 py-3">Transaction</th>
                <th className="px-5 py-3">Predicted Root Cause</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Assigned Team</th>
                <th className="px-5 py-3">Priority</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {cases.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-5 py-8 text-center text-slate-500 font-sans">
                    No active dispute cases logged yet. Run an investigation from the Dispute Investigator tab!
                  </td>
                </tr>
              ) : (
                cases.map((c) => (
                  <tr key={c.case_id} className="hover:bg-slate-800/40">
                    <td className="px-5 py-3 text-amber-400 font-bold">{c.case_id}</td>
                    <td className="px-5 py-3 text-slate-200">{c.transaction_id}</td>
                    <td className="px-5 py-3 text-white font-semibold">{c.root_cause}</td>
                    <td className="px-5 py-3 text-slate-300">{(c.confidence * 100).toFixed(1)}%</td>
                    <td className="px-5 py-3">
                      <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {c.assigned_team}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded ${
                        c.priority === 'HIGH' || c.priority === 'CRITICAL'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full ${
                        c.status === 'RESOLVED'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : 'bg-amber-500/10 text-amber-400'
                      }`}>
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Human-in-the-Loop Feedback / Continuous Improvement Audit Table (Phase 15) */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Continuous Improvement Feedback Loop (Retraining Dataset)
            </h3>
          </div>
          <span className="text-xs font-mono text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
            Active Learning Enabled
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 font-mono uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Feedback ID</th>
                <th className="px-5 py-3">Case ID</th>
                <th className="px-5 py-3">Predicted Cause</th>
                <th className="px-5 py-3">Actual / Confirmed Cause</th>
                <th className="px-5 py-3">Operator Action</th>
                <th className="px-5 py-3">Officer</th>
                <th className="px-5 py-3">Audit Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {feedbackHistory.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-5 py-8 text-center text-slate-500 font-sans">
                    No operator feedback submitted yet.
                  </td>
                </tr>
              ) : (
                feedbackHistory.map((fb) => (
                  <tr key={fb.id} className="hover:bg-slate-800/40">
                    <td className="px-5 py-3 text-slate-400">FB-#{fb.id}</td>
                    <td className="px-5 py-3 text-amber-400">{fb.case_id}</td>
                    <td className="px-5 py-3 text-slate-300">{fb.predicted_root_cause}</td>
                    <td className="px-5 py-3 text-emerald-400 font-bold">{fb.actual_root_cause}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded ${
                        fb.operator_action === 'ACCEPTED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                      }`}>
                        {fb.operator_action}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-300">{fb.resolved_by}</td>
                    <td className="px-5 py-3 font-sans text-slate-400 max-w-xs truncate" title={fb.resolution_notes}>
                      {fb.resolution_notes || 'Confirmed without extra remarks.'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
