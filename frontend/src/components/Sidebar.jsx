import React from 'react';
import {
  LayoutDashboard,
  Search,
  FolderCheck,
  BarChart3,
  ShieldCheck,
  Activity,
  Cpu,
  Layers,
  Sparkles,
  ChevronRight,
  Database,
  Radio,
  UserCheck
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, openCasesCount = 124, anomaliesCount = 7 }) {
  const mainNavItems = [
    {
      id: 'dashboard',
      label: 'Operations Dashboard',
      icon: LayoutDashboard,
      badge: `${openCasesCount} Open`,
      badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
    },
    {
      id: 'investigation',
      label: 'Dispute Investigator',
      icon: Search,
      badge: 'AI Core',
      badgeColor: 'bg-amber-500/15 text-amber-300 border-amber-500/30'
    },
    {
      id: 'cases',
      label: 'Case Management',
      icon: FolderCheck,
      badge: 'HITL Feedback',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    },
    {
      id: 'metrics',
      label: 'Impact & ROI Metrics',
      icon: BarChart3,
      badge: 'Benchmark',
      badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
    }
  ];

  return (
    <aside className="w-72 bg-slate-900/95 border-r border-slate-800 flex flex-col h-screen sticky top-0 select-none z-40 backdrop-blur-xl">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-amber-500 via-amber-400 to-amber-300 flex items-center justify-center shadow-lg shadow-amber-500/25 text-slate-950 font-black text-2xl tracking-tighter ring-2 ring-amber-400/30">
            u
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight text-white">
                upay <span className="text-amber-400 font-bold">Ops</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 font-semibold">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Dispute Intelligence Cockpit
            </p>
          </div>
        </div>

        <div className="mt-4 px-3 py-1.5 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Switch Live
          </span>
          <span className="text-slate-500">Track 06 • MFS Ops</span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 px-4 py-5 space-y-6 overflow-y-auto">
        <div>
          <div className="px-3 mb-2.5 text-[10px] font-mono font-bold tracking-wider uppercase text-slate-500">
            Core Operations
          </div>
          <nav className="space-y-1.5">
            {mainNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-amber-500 text-slate-950 font-bold shadow-lg shadow-amber-500/20'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${isActive ? 'text-slate-950' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-md border font-semibold ${
                        isActive
                          ? 'bg-slate-950 text-amber-300 border-amber-400/40'
                          : item.badgeColor
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Live Systems Telemetry Widget */}
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 font-semibold border-b border-slate-800/60 pb-2">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-amber-400" />
              Engine Telemetry
            </span>
            <span className="text-emerald-400">Normal</span>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between text-slate-400">
              <span>ML Classifier</span>
              <span className="text-emerald-400 font-bold">100 Trees • Active</span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span>Rule Baseline</span>
              <span className="text-slate-300">8 Logic Gates</span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span>Isolation Forest</span>
              <span className="text-rose-400">5% Outlier Scan</span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span>Historical RAG</span>
              <span className="text-blue-400">Indexed (Precedents)</span>
            </div>
            <div className="flex items-center justify-between text-slate-400 pt-1.5 border-t border-slate-900">
              <span className="flex items-center gap-1.5 text-slate-300">
                <Database className="w-3 h-3 text-emerald-400" />
                Supabase
              </span>
              <span className="text-emerald-400 font-bold">Connected</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operator Profile Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-800 to-slate-700 border border-slate-700 flex items-center justify-center font-bold text-amber-400 font-mono text-sm shadow">
            OT
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white truncate">Officer Tariq</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono truncate">
              Lead Dispute Officer (T2)
            </p>
            <p className="text-[10px] text-slate-500 font-mono">
              Dhaka Core Hub
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
