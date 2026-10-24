import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, Clock, AlertTriangle, CheckCircle2, TrendingUp, Award, Flame } from 'lucide-react';
import { api } from '../api/client';
import { KPICard } from '../components/KPICard';
import { RecentEventsStream } from '../components/RecentEventsStream';
import { TrendChart } from '../components/charts/TrendChart';
import { HistogramChart } from '../components/charts/HistogramChart';
import { HeatmapChart } from '../components/charts/HeatmapChart';

export const Dashboard: React.FC = () => {
  // Har 60 soniyada ma'lumotlarni fonda avtomatik yangilash (tab nofaol bo'lsa to'xtaydi)
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['overview'],
    queryFn: async () => (await api.get('/stats/overview')).data,
    refetchInterval: 60000,
  });

  const { data: recentEvents, isLoading: loadingRecent } = useQuery({
    queryKey: ['recentEvents'],
    queryFn: async () => (await api.get('/events/recent?limit=20')).data,
    refetchInterval: 30000,
  });

  const { data: trend } = useQuery({
    queryKey: ['trend'],
    queryFn: async () => (await api.get('/stats/trend?days=30')).data,
    refetchInterval: 60000,
  });

  const { data: ranking } = useQuery({
    queryKey: ['ranking'],
    queryFn: async () => (await api.get('/stats/ranking')).data,
    refetchInterval: 60000,
  });

  const { data: histogram } = useQuery({
    queryKey: ['histogram'],
    queryFn: async () => (await api.get('/stats/arrival-hist')).data,
    refetchInterval: 60000,
  });

  const { data: heatmap } = useQuery({
    queryKey: ['heatmap'],
    queryFn: async () => (await api.get('/stats/heatmap')).data,
    refetchInterval: 60000,
  });

  return (
    <div className="space-y-6">
      {/* 1. KPI Kartalar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Bugun kelganlar"
          value={overview?.present ?? '-'}
          subtext={`Jami xodimlar: ${overview?.total_employees ?? '-'}`}
          icon={Users}
          color="emerald"
        />
        <KPICard
          title="Vaqtida kelish"
          value={`${overview?.on_time_percentage ?? 0}%`}
          subtext={`${overview?.on_time ?? 0} kishi o'z vaqtida`}
          icon={CheckCircle2}
          color="indigo"
        />
        <KPICard
          title="Kech qolganlar"
          value={overview?.late ?? '-'}
          subtext="Bugungi kechikishlar"
          icon={AlertTriangle}
          color="amber"
        />
        <KPICard
          title="Kelmaganlar"
          value={overview?.absent ?? '-'}
          subtext="Bugun qayd etilmagan"
          icon={Clock}
          color="rose"
        />
      </div>

      {/* 2. Jonli lenta va Trend grafigi */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Jonli lenta (oxirgi 20 o'tish) */}
        <div className="lg:col-span-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
                Jonli O'tishlar Lentasida
              </h2>
              <p className="text-xs text-slate-500">Oxirgi 20 ta yuz tanish hodisasi</p>
            </div>
            <span className="text-xs text-slate-400 font-medium">Har 30s da yangilanadi</span>
          </div>

          <RecentEventsStream events={recentEvents || []} />
        </div>

        {/* 30 kunlik trend */}
        <div className="lg:col-span-7 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <TrendChart data={trend || []} />
        </div>
      </div>

      {/* 3. Reyting (Eng ko'p kechikkanlar va Eng intizomlilar) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Eng ko'p kechikkanlar */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Flame className="w-5 h-5 text-amber-500" />
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Eng Ko'p Kechikkanlar</h3>
              <p className="text-xs text-slate-500">Oxirgi 30 kunlik jamlangan daqiqalar</p>
            </div>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {ranking?.most_late?.length > 0 ? (
              ranking.most_late.map((emp: any, idx: number) => (
                <div key={emp.emp_no} className="py-2.5 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <span className="w-6 text-center text-xs font-bold text-slate-400">{idx + 1}</span>
                    <div>
                      <p className="font-semibold text-slate-800 dark:text-slate-200">{emp.name}</p>
                      <p className="text-xs text-slate-400">{emp.department || `ID: ${emp.emp_no}`}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-amber-600 dark:text-amber-400">{emp.total_late_minutes} daq</span>
                    <p className="text-[11px] text-slate-400">{emp.late_days} kun</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="py-6 text-center text-sm text-slate-400">Kechikkanlar topilmadi</p>
            )}
          </div>
        </div>

        {/* Eng intizomli xodimlar */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Award className="w-5 h-5 text-indigo-500" />
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Eng Intizomli Xodimlar</h3>
              <p className="text-xs text-slate-500">Vaqtida kelish bo'yicha yetakchilar</p>
            </div>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {ranking?.most_punctual?.length > 0 ? (
              ranking.most_punctual.map((emp: any, idx: number) => (
                <div key={emp.emp_no} className="py-2.5 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <span className="w-6 text-center text-xs font-bold text-slate-400">{idx + 1}</span>
                    <div>
                      <p className="font-semibold text-slate-800 dark:text-slate-200">{emp.name}</p>
                      <p className="text-xs text-slate-400">{emp.department || `ID: ${emp.emp_no}`}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">{emp.on_time_days} kun</span>
                    <p className="text-[11px] text-slate-400">vaqtida kelgan</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="py-6 text-center text-sm text-slate-400">Ma'lumot topilmadi</p>
            )}
          </div>
        </div>
      </div>

      {/* 4. Gistogramma va Issiqlik xaritasi */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <HistogramChart data={histogram || []} />
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
          <HeatmapChart data={heatmap || []} />
        </div>
      </div>
    </div>
  );
};
