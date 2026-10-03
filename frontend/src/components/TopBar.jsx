import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Bell,
  Clock,
  ShieldCheck,
  Activity,
  Sun,
  Moon,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  CheckCircle2,
  X,
  ExternalLink,
  Layers
} from 'lucide-react';

export default function TopBar({
  activeTab,
  onQuickSearch,
  theme,
  setTheme,
  onNavigateToAlert
}) {
  const [searchInput, setSearchInput] = useState('');
  const [timeStr, setTimeStr] = useState('');
  const [showAlerts, setShowAlerts] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [unreadCount, setUnreadCount] = useState(5);
  const dropdownRef = useRef(null);

  // Fetch live alerts
  useEffect(() => {
    fetch('/api/alerts')
      .then((r) => r.json())
      .then((data) => {
        if (data.alerts) {
          setAlerts(data.alerts);
          setUnreadCount(data.alerts.length);
        }
      })
      .catch((e) => console.error('Failed to fetch alerts:', e));
  }, []);

  // Live Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }) + ' BST'
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowAlerts(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const tabTitles = {
    dashboard: {
      title: 'Operations Overview & Live Dispute Queue',
      subtitle: 'Real-time telemetry, transaction dispute stream, and operational KPI monitors'
    },
    investigation: {
      title: 'Automated Dispute Investigator & Root-Cause Engine',
      subtitle: 'Event timeline reconstruction, multi-model consensus, RAG precedents, and evidence-grounded action'
    },
    cases: {
      title: 'Case Management & Human-in-the-Loop Feedback Loop',
      subtitle: 'Dispatched dispute cases, operator audit log, and continuous model retraining dataset'
    },
    metrics: {
      title: 'Measurable Operational Impact & Benchmark ROI',
      subtitle: 'Measured 78.6% speedup, 66.7% fewer manual steps, and ML model validation metrics'
    }
  };

  const currentInfo = tabTitles[activeTab] || tabTitles.dashboard;

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchInput.trim() && onQuickSearch) {
      onQuickSearch(searchInput.trim());
    }
  };

  const handleAlertClick = (alertItem) => {
    setShowAlerts(false);
    if (onNavigateToAlert) {
      onNavigateToAlert(alertItem.target_tab, alertItem.transaction_id, alertItem.complaint_text);
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-xl px-8 py-5 sticky top-0 z-30 transition-colors">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Left: Clean Breadcrumbs & Arranged Header Titles */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <span className="text-amber-400 font-semibold">upay Central Ops</span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-300 capitalize">{activeTab}</span>
            <span className="text-slate-600">/</span>
            <span className="text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              Live Core
            </span>
          </div>
          <h1 className="text-xl lg:text-2xl font-black text-white tracking-tight">
            {currentInfo.title}
          </h1>
          <p className="text-xs text-slate-400 max-w-2xl font-normal">
            {currentInfo.subtitle}
          </p>
        </div>

        {/* Right: Quick Action Controls, Live Status, Search Bar, Theme Toggle, Alerts */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Quick Search Bar */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search TX10082 or text..."
              className="w-56 sm:w-64 pl-9 pr-3.5 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-white placeholder:text-slate-500 font-mono focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all shadow-inner"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3 pointer-events-none" />
          </form>

          {/* Dark / Light Mode Toggle Button */}
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-amber-500/50 text-slate-300 hover:text-amber-400 text-xs font-mono transition-all shadow-sm"
          >
            {theme === 'dark' ? (
              <>
                <Sun className="w-4 h-4 text-amber-400" />
                <span className="hidden sm:inline">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4 text-indigo-400" />
                <span className="hidden sm:inline">Dark</span>
              </>
            )}
          </button>

          {/* Live Clock Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs font-mono text-amber-300 font-medium">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>{timeStr || '14:32:08 BST'}</span>
          </div>

          {/* Interactive Alerts Bell with Dropdown Menu */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowAlerts(!showAlerts)}
              title="Click to view Active Operational Issues"
              className={`p-2 rounded-xl border transition-all relative flex items-center justify-center ${
                showAlerts
                  ? 'bg-amber-500/20 border-amber-500 text-amber-300 ring-2 ring-amber-500/30'
                  : 'bg-slate-950/70 border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white'
              }`}
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-[9px] font-mono font-bold flex items-center justify-center text-white ring-2 ring-slate-900 animate-pulse">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Interactive Alert Dropdown Drawer */}
            {showAlerts && (
              <div className="absolute right-0 mt-2 w-96 sm:w-[440px] rounded-2xl bg-slate-900/95 border border-slate-700 shadow-2xl z-50 overflow-hidden backdrop-blur-2xl animate-in fade-in slide-in-from-top-2 duration-150">
                {/* Drawer Header */}
                <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    <div>
                      <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Active Operational Issues & Alerts
                      </h3>
                      <p className="text-[10px] text-slate-400">
                        {alerts.length} pending anomalies & dispute SLA triggers
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowAlerts(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Alerts List */}
                <div className="max-h-[380px] overflow-y-auto divide-y divide-slate-800/80 p-2 space-y-1.5">
                  {alerts.map((alt) => {
                    const isCritical = alt.severity === 'CRITICAL';
                    const isHigh = alt.severity === 'HIGH';
                    const isMedium = alt.severity === 'MEDIUM';

                    return (
                      <div
                        key={alt.id}
                        onClick={() => handleAlertClick(alt)}
                        className="p-3 rounded-xl bg-slate-950/70 hover:bg-slate-850 border border-slate-800/80 hover:border-amber-500/40 transition-all cursor-pointer group space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[9px] font-mono uppercase font-bold px-1.5 py-0.5 rounded ${
                                isCritical
                                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                  : isHigh
                                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                  : isMedium
                                  ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              }`}
                            >
                              {alt.severity}
                            </span>
                            {alt.transaction_id && (
                              <span className="text-[10px] font-mono font-bold text-amber-400 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                                {alt.transaction_id}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {alt.time}
                          </span>
                        </div>

                        <h4 className="text-xs font-bold text-white group-hover:text-amber-300 transition-colors">
                          {alt.title}
                        </h4>

                        <p className="text-[11px] text-slate-300 line-clamp-2 leading-relaxed">
                          {alt.description}
                        </p>

                        <div className="pt-1 flex items-center justify-between text-[10px] font-mono">
                          <span className="text-slate-400 flex items-center gap-1">
                            <span>Location:</span>
                            <span className="text-slate-300 font-medium">{alt.location}</span>
                          </span>
                          <span className="text-amber-400 font-bold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                            <span>Investigate Issue</span>
                            <ArrowRight className="w-3 h-3" />
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Drawer Footer */}
                <div className="p-3 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>Click alert to navigate & investigate</span>
                  <button
                    onClick={() => {
                      setUnreadCount(0);
                      setShowAlerts(false);
                    }}
                    className="text-amber-400 hover:text-amber-300 font-semibold"
                  >
                    Clear Badges
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
