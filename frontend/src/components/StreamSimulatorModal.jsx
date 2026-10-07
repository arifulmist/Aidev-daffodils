import React, { useState, useEffect } from 'react';
import { Radio, Activity, Zap, X, ArrowUpRight, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function StreamSimulatorModal({ isOpen, onClose, onSelectTransaction }) {
  const [streamEvents, setStreamEvents] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [lastBurstTx, setLastBurstTx] = useState(null);

  const fetchFeed = () => {
    fetch('/api/stream/feed?limit=15')
      .then((r) => r.json())
      .then((data) => {
        if (data && data.events) {
          setStreamEvents(data.events);
        }
      })
      .catch((e) => console.error(e));
  };

  useEffect(() => {
    if (isOpen) {
      fetchFeed();
      const interval = setInterval(fetchFeed, 3000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const handleSimulateBurst = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch('/api/stream/simulate-burst', { method: 'POST' });
      const data = await res.json();
      if (data && data.generated_transaction) {
        setLastBurstTx(data.generated_transaction);
        fetchFeed();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-4xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-extrabold text-white font-mono">
                  Live Event Stream Ingestion Adapter
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono font-bold">
                  Kafka / Webhook Consumer Active
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Real-time transaction event ingestion simulating CBS, NPSB switch, and merchant gateway webhooks.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Controls & Banner */}
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-xs text-slate-300 font-mono">
            <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              Live Feed Connected
            </span>
            <span>• Buffer: {streamEvents.length} events</span>
            {lastBurstTx && (
              <span className="text-amber-400">
                Latest Ingested: <span className="font-bold underline cursor-pointer" onClick={() => onSelectTransaction(lastBurstTx)}>{lastBurstTx}</span>
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSimulateBurst}
              disabled={isSimulating}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs font-mono flex items-center gap-2 shadow-lg shadow-amber-500/20 transition-all disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              {isSimulating ? 'Ingesting Burst...' : 'Simulate Gateway Burst ⚡'}
            </button>
          </div>
        </div>

        {/* Streaming Event Feed Table */}
        <div className="flex-1 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-950/60 divide-y divide-slate-800/60">
          {streamEvents.length === 0 ? (
            <div className="p-8 text-center text-slate-500 font-mono text-xs">
              Listening on telemetry stream topic <code className="text-amber-400">upay.core.events.v1</code>...
            </div>
          ) : (
            streamEvents.map((evt, idx) => (
              <div
                key={idx}
                className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-900/60 transition-colors text-xs font-mono"
              >
                <div className="flex items-center gap-3">
                  <span className="text-[11px] text-slate-500">{evt.timestamp}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    evt.source === 'CBS_LEDGER'
                      ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      : evt.source === 'MERCHANT_WEBHOOK'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                      : evt.source === 'REVERSAL_WORKER'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}>
                    {evt.source}
                  </span>
                  <button
                    onClick={() => {
                      if (onSelectTransaction) {
                        onSelectTransaction(evt.transaction_id);
                        onClose();
                      }
                    }}
                    className="font-bold text-white hover:text-amber-400 transition-colors flex items-center gap-1 group"
                  >
                    <span>{evt.transaction_id}</span>
                    <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                  <span className="text-slate-400 font-semibold">{evt.event_type}</span>
                </div>

                <div className="flex items-center gap-4 text-[11px]">
                  {evt.amount > 0 && (
                    <span className="text-amber-300 font-bold">৳{evt.amount.toLocaleString()}</span>
                  )}
                  <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                    evt.status === 'SUCCESS'
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : evt.status === 'TIMEOUT' || evt.status === 'FAILED'
                      ? 'bg-rose-500/20 text-rose-300'
                      : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    {evt.status}
                  </span>
                  <span className="text-slate-500 text-[10px]">{evt.latency_ms}ms</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>High-Throughput Asynchronous Non-Blocking Pipeline</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
