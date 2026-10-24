import React from 'react';

interface HistSlot {
  slot: string;
  count: number;
}

interface HistogramChartProps {
  data: HistSlot[];
}

export const HistogramChart: React.FC<HistogramChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="h-48 flex items-center justify-center text-slate-400 text-sm">Ma'lumot yo'q</div>;
  }

  const maxVal = Math.max(1, ...data.map((d) => d.count));

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">Kelish Vaqti Taqsimoti</h3>
        <p className="text-xs text-slate-500">Xodimlarning kelish vaqti intervallari</p>
      </div>

      <div className="space-y-2.5">
        {data.map((item) => {
          const pct = Math.round((item.count / maxVal) * 100);
          return (
            <div key={item.slot} className="space-y-1">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-slate-600 dark:text-slate-400">{item.slot}</span>
                <span className="text-slate-900 dark:text-white font-semibold">{item.count} kishi</span>
              </div>
              <div className="h-2.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-indigo-600 rounded-full transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
