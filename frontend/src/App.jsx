import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import DashboardTab from './components/DashboardTab';
import InvestigationTab from './components/InvestigationTab';
import CasesTab from './components/CasesTab';
import MetricsTab from './components/MetricsTab';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedTxId, setSelectedTxId] = useState('TX10082');
  const [selectedComplaintText, setSelectedComplaintText] = useState('');
  const [selectedComplaintId, setSelectedComplaintId] = useState('');
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('upay_theme') || 'dark';
  });

  // Apply theme class to document root
  useEffect(() => {
    document.documentElement.classList.remove('dark', 'light');
    document.documentElement.classList.add(theme);
    localStorage.setItem('upay_theme', theme);
  }, [theme]);

  const handleSelectComplaint = (complaint) => {
    setSelectedTxId(complaint.transaction_id || '');
    setSelectedComplaintText(complaint.complaint_text || '');
    setSelectedComplaintId(complaint.complaint_id || '');
    setActiveTab('investigation');
  };

  const handleSelectTransaction = (txId, text = '', compId = '') => {
    setSelectedTxId(txId);
    setSelectedComplaintText(text);
    setSelectedComplaintId(compId);
    setActiveTab('investigation');
  };

  const handleQuickSearch = (query) => {
    if (query.toUpperCase().startsWith('TX') || /^\d+$/.test(query)) {
      setSelectedTxId(query.toUpperCase().startsWith('TX') ? query.toUpperCase() : `TX${query}`);
      setSelectedComplaintText('');
    } else {
      setSelectedComplaintText(query);
      setSelectedTxId('');
    }
    setActiveTab('investigation');
  };

  const handleNavigateToAlert = (targetTab, txId, text) => {
    if (txId) {
      setSelectedTxId(txId);
      setSelectedComplaintText(text || '');
      setSelectedComplaintId('');
      setActiveTab('investigation');
    } else if (targetTab) {
      setActiveTab(targetTab);
    }
  };

  return (
    <div className={`min-h-screen flex font-sans antialiased selection:bg-amber-500 selection:text-black ${
      theme === 'dark' ? 'dark bg-slate-950 text-slate-100' : 'light bg-slate-50 text-slate-900'
    }`}>
      {/* Left-Side Vertical Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        openCasesCount={124}
        anomaliesCount={7}
      />

      {/* Main Workspace Area (Right of Sidebar) */}
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        {/* Generously padded and well-arranged TopBar */}
        <TopBar
          activeTab={activeTab}
          onQuickSearch={handleQuickSearch}
          theme={theme}
          setTheme={setTheme}
          onNavigateToAlert={handleNavigateToAlert}
        />

        {/* Main Content with generous padding and clean spacing - no overlap */}
        <main className="flex-1 px-6 sm:px-8 lg:px-10 py-8 max-w-7xl w-full mx-auto space-y-8">
          {activeTab === 'dashboard' && (
            <DashboardTab
              onSelectComplaint={handleSelectComplaint}
              onSelectTransaction={handleSelectTransaction}
            />
          )}

          {activeTab === 'investigation' && (
            <InvestigationTab
              initialTransactionId={selectedTxId}
              initialComplaintText={selectedComplaintText}
              initialComplaintId={selectedComplaintId}
              onCaseLogged={() => {}}
            />
          )}

          {activeTab === 'cases' && <CasesTab />}

          {activeTab === 'metrics' && <MetricsTab />}
        </main>

        {/* Clean Enterprise Footer */}
        <footer className="border-t border-slate-900 bg-slate-950/80 px-8 py-4 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 font-mono gap-2 mt-auto">
          <div>upay Ops Intelligence • DIU CPC × upay AI Hackathon 2026 (Track 06)</div>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="text-emerald-400 font-medium">Privacy by Design</span>
            <span>•</span>
            <span className="text-amber-400 font-medium">Zero Hallucinations</span>
            <span>•</span>
            <span className="text-blue-400 font-medium">Human-in-the-Loop Oversight</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
