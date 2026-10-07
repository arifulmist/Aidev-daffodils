import React, { useState, useEffect } from 'react';
import { Radio, Activity, Zap, X, ArrowUpRight, CheckCircle2, AlertTriangle, ShieldCheck, Layers, Cpu, Server, Network } from 'lucide-react';

export default function StreamSimulatorModal({ isOpen, onClose, onSelectTransaction }) {
  const [streamEvents, setStreamEvents] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [lastBurstTx, setLastBurstTx] = useState(null);
  const [activeView, setActiveView] = useState('stream'); // 'stream' | 'topology'
  const [topology, setTopology] = useState(null);

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

  const fetchTopology = () => {
    fetch('/api/stream/topology')
      .then((r) => r.json())
      .then((data) => setTopology(data))
      .catch((e) => console.error(e));
  };

  useEffect(() => {
    if (isOpen) {
      fetchFeed();
      fetchTopology();
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
                  Event Stream & Microservices Architecture
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono font-bold">
                  Kafka / AMQP Stream Adapter
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Decoupled microservices topology & real-time message queue event stream for MFS core banking.
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

        {/* View Toggle Tabs */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-950/80 border border-slate-800">
            <button
              onClick={() => setActiveView('stream')}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                activeView === 'stream'
                  ? 'bg-amber-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              🔴 Live Event Queue Feed
            </button>
            <button
              onClick={() => setActiveView('topology')}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                activeView === 'topology'
                  ? 'bg-amber-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              🏗️ Microservices & Queue Topology
            </button>
          </div>

          {activeView === 'stream' && (
            <button
              onClick={handleSimulateBurst}
              disabled={isSimulating}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs font-mono flex items-center gap-2 shadow-lg shadow-amber-500/20 transition-all disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              {isSimulating ? 'Ingesting...' : 'Simulate Gateway Burst ⚡'}
            </button>
          )}
        </div>

        {/* VIEW 1: Streaming Event Feed Table */}
        {activeView === 'stream' ? (
          <div className="flex-1 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-950/60 divide-y divide-slate-800/60">
            {streamEvents.length === 0 ? (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                Listening on telemetry stream topic <code className="text-amber-400">cbs.ledger.events.v1</code>...
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
        ) : (
          /* VIEW 2: Microservices & Message Broker Architecture Topology */
          <div className="flex-1 overflow-y-auto space-y-4">
            {/* Broker & Topics Card */}
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-mono font-bold text-white uppercase">
                    Message Broker: {topology?.message_broker?.type || 'Apache Kafka Cluster'}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                  Consumer Group: {topology?.message_broker?.consumer_group || 'upay-ops-dispute'}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                {topology?.message_broker?.active_topics?.map((top, idx) => (
                  <div key={idx} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="text-amber-300 font-bold text-[11px]">{top.topic}</div>
                      <div className="text-[10px] text-slate-500">{top.throughput} • {top.partition_count} Partitions</div>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      Retention: {top.retention}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Microservices Grid */}
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                <Server className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono font-bold text-white uppercase">
                  9 Decoupled Domain Microservices
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs font-mono">
                {topology?.microservices?.map((svc, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-200 text-[11px]">{svc.service}</span>
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    </div>
                    <div className="text-[10px] text-slate-500 truncate" title={svc.protocol}>
                      {svc.protocol}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Event-Driven Microservices Architecture (EDA)</span>
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
