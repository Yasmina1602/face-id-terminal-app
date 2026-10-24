import React from 'react';
import {
  LayoutDashboard,
  CalendarCheck,
  Users,
  FileSpreadsheet,
  Settings,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export type NavTab = 'dashboard' | 'attendance' | 'employees' | 'reports' | 'settings';

interface SidebarProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange }) => {
  const { isAdmin } = useAuth();

  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'attendance' as NavTab, label: 'Davomat', icon: CalendarCheck },
    { id: 'employees' as NavTab, label: 'Xodimlar', icon: Users },
    { id: 'reports' as NavTab, label: 'Hisobotlar', icon: FileSpreadsheet },
    ...(isAdmin ? [{ id: 'settings' as NavTab, label: 'Sozlamalar', icon: Settings }] : []),
  ];

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between p-4 shrink-0 hidden md:flex">
      <nav className="space-y-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? 'bg-brand-500 text-white shadow-md shadow-brand-500/25 dark:shadow-none'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="pt-4 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-400 dark:text-slate-500 text-center">
        Davomat Tizimi v1.0
      </div>
    </aside>
  );
};
