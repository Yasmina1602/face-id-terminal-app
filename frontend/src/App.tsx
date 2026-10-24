import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar, NavTab } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Attendance } from './pages/Attendance';
import { Employees } from './pages/Employees';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { Login } from './pages/Login';

export const App: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'attendance':
        return <Attendance />;
      case 'employees':
        return <Employees />;
      case 'reports':
        return <Reports />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentTab={currentTab} onTabChange={setCurrentTab} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {renderContent()}
        </main>
      </div>

      {/* Mobil pastki navigatsiya */}
      <nav className="md:hidden sticky bottom-0 z-20 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 flex justify-around text-xs">
        {[
          { id: 'dashboard' as NavTab, label: 'Bosh sahifa' },
          { id: 'attendance' as NavTab, label: 'Davomat' },
          { id: 'employees' as NavTab, label: 'Xodimlar' },
          { id: 'reports' as NavTab, label: 'Hisobot' },
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => setCurrentTab(item.id)}
            className={`py-1.5 px-3 rounded-xl font-medium transition-colors ${
              currentTab === item.id
                ? 'bg-brand-500 text-white'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default App;
