import React from 'react';

interface HeatmapChartProps {
  data: number[][]; // [weekday (0-6), hour (0-23), count]
}

const WEEKDAYS = ["Du", "Se", "Cho", "Pay", "Ju", "Sha", "Ya"];
const DISPLAY_HOURS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19];

export const HeatmapChart: React.FC<HeatmapChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="h-48 flex items-center justify-center text-slate-400 text-sm">Ma'lumot yo'q</div>;
  }

  const lookup: { [key: string]: number } = {};
  let maxCount = 1;
  data.forEach(([dow, hour, count]) => {
    lookup[`${dow}_${hour}`] = count;
    if (count > maxCount) maxCount = count;
  });

  const getColor = (count: number) => {
    if (!count) return 'bg-slate-100 dark:bg-slate-800/60';
    const intensity = count / maxCount;
    if (intensity < 0.25) return 'bg-brand-200 dark:bg-brand-950 text-brand-900 dark:text-brand-200';
    if (intensity < 0.5) return 'bg-brand-400 dark:bg-brand-800 text-white';
    if (intensity < 0.75) return 'bg-brand-600 dark:bg-brand-600 text-white';
    return 'bg-brand-700 dark:bg-brand-500 text-white';
  };

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">Haftalik Issiqlik Xaritasi</h3>
        <p className="text-xs text-slate-500">Hafta kuni x Soat kesimida o'tishlar zichligi</p>
      </div>

      <div className="overflow-x-auto pb-2">
        <div className="min-w-[450px]">
          {/* Header hours */}
          <div className="grid grid-cols-[40px_repeat(13,1fr)] gap-1 text-[11px] text-slate-400 mb-1 font-medium text-center">
            <div></div>
            {DISPLAY_HOURS.map((h) => (
              <div key={h}>{h}:00</div>
            ))}
          </div>

          {/* Weekday rows */}
          <div className="space-y-1">
            {WEEKDAYS.map((wd, dow) => (
              <div key={wd} className="grid grid-cols-[40px_repeat(13,1fr)] gap-1 items-center">
                <span className="text-xs font-semibold text-slate-500">{wd}</span>
                {DISPLAY_HOURS.map((h) => {
                  const count = lookup[`${dow}_${h}`] || 0;
                  return (
                    <div
                      key={h}
                      title={`${wd}, ${h}:00 - ${count} ta o'tish`}
                      className={`h-7 rounded-md flex items-center justify-center text-[10px] font-bold transition-all hover:scale-105 cursor-pointer ${getColor(
                        count
                      )}`}
                    >
                      {count > 0 ? count : ''}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
