import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  color: 'emerald' | 'amber' | 'rose' | 'indigo' | 'blue';
}

const colorStyles = {
  emerald: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    border: 'border-emerald-200 dark:border-emerald-900',
    iconBg: 'bg-emerald-500 text-white',
    text: 'text-emerald-700 dark:text-emerald-300',
  },
  amber: {
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    border: 'border-amber-200 dark:border-amber-900',
    iconBg: 'bg-amber-500 text-white',
    text: 'text-amber-700 dark:text-amber-300',
  },
  rose: {
    bg: 'bg-rose-50 dark:bg-rose-950/40',
    border: 'border-rose-200 dark:border-rose-900',
    iconBg: 'bg-rose-500 text-white',
    text: 'text-rose-700 dark:text-rose-300',
  },
  indigo: {
    bg: 'bg-indigo-50 dark:bg-indigo-950/40',
    border: 'border-indigo-200 dark:border-indigo-900',
    iconBg: 'bg-indigo-500 text-white',
    text: 'text-indigo-700 dark:text-indigo-300',
  },
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    border: 'border-blue-200 dark:border-blue-900',
    iconBg: 'bg-blue-500 text-white',
    text: 'text-blue-700 dark:text-blue-300',
  },
};

export const KPICard: React.FC<KPICardProps> = ({ title, value, subtext, icon: Icon, color }) => {
  const styles = colorStyles[color];

  return (
    <div className={`p-5 rounded-2xl border ${styles.border} ${styles.bg} transition-all hover:shadow-lg hover:-translate-y-0.5`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-600 dark:text-slate-400">{title}</span>
        <div className={`w-10 h-10 rounded-xl ${styles.iconBg} flex items-center justify-center shadow-sm`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">{value}</span>
        {subtext && <span className={`text-xs font-semibold ${styles.text}`}>{subtext}</span>}
      </div>
    </div>
  );
};
