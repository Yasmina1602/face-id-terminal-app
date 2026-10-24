import React from 'react';
import { ArrowDownLeft, ArrowUpRight, Clock, AlertTriangle, CheckCircle } from 'lucide-react';

export interface RecentEvent {
  id: number;
  emp_no: string;
  employee_name: string;
  event_type: 'checkIn' | 'checkOut';
  event_time: string;
  late_minutes: number;
  serial_no: number | null;
}

interface RecentEventsStreamProps {
  events: RecentEvent[];
}

export const RecentEventsStream: React.FC<RecentEventsStreamProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-sm">
        <Clock className="w-8 h-8 mb-2 opacity-40 animate-pulse" />
        Hozircha o'tishlar qayd etilmagan
      </div>
    );
  }

  const formatTime = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return iso;
    }
  };

  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-800/80 max-h-[380px] overflow-y-auto pr-1">
      {events.map((ev) => {
        const isCheckIn = ev.event_type === 'checkIn';
        const isLate = ev.late_minutes > 0;

        return (
          <div key={ev.id} className="py-2.5 flex items-center justify-between hover:bg-slate-50/50 dark:hover:bg-slate-800/40 px-2 rounded-lg transition-colors">
            <div className="flex items-center gap-3">
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                  isCheckIn
                    ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                }`}
              >
                {isCheckIn ? <ArrowDownLeft className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-tight">
                  {ev.employee_name}
                </p>
                <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                  <span>ID: {ev.emp_no}</span>
                  <span>•</span>
                  <span>{formatTime(ev.event_time)}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isCheckIn && (
                isLate ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                    <AlertTriangle className="w-3 h-3" />
                    +{ev.late_minutes} daq
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                    <CheckCircle className="w-3 h-3" />
                    Vaqtida
                  </span>
                )
              )}
              {!isCheckIn && (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                  Ketdi
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
