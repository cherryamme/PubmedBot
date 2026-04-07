import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppHeader from './components/layout/AppHeader';
import Sidebar from './components/layout/Sidebar';
import SettingsModal from './components/settings/SettingsModal';
import HomePage from './pages/HomePage';
import PaperPage from './pages/PaperPage';

export default function App() {
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col bg-gray-50">
        <AppHeader onOpenSettings={() => setShowSettings(true)} />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/paper/:id" element={<PaperPage />} />
              </Routes>
            </div>
          </main>
        </div>
        <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
      </div>
    </BrowserRouter>
  );
}
