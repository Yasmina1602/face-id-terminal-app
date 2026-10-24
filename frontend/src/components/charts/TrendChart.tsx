import React from 'react';

interface TrendItem {
  day: string;
  total: number;
  late_count: number;
  late_percentage: number;
  avg_arrival_time: string | null;
}

interface TrendChartProps {
  data: TrendItem[];
}

export const TrendChart: React.FC<TrendChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
        Ma'lumotlar mavjud emas
      </div>
    );
  }

  const height = 220;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };

  const maxVal = Math.max(50, ...data.map((d) => d.late_percentage || 0));
  const minVal = 0;

  const points = data.map((d, index) => {
    const x = padding.left + (index / (data.length - 1 || 1)) * (500 - padding.left - padding.right);
    const y = padding.top + (1 - (d.late_percentage - minVal) / (maxVal - minVal || 1)) * (height - padding.top - padding.bottom);
    return { x, y, ...d };
  });

  const pathD = points.reduce((acc, p, i) => {
    return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  const areaD = `${pathD} L ${points[points.length - 1].x} ${height - padding.bottom} L ${points[0].x} ${height - padding.bottom} Z`;

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">Kechikish Trendi</h3>
          <p className="text-xs text-slate-500">Kunlik kechikish foizi (%)</p>
        </div>
      </div>

      <div className="relative overflow-hidden w-full">
        <svg viewBox={`0 0 500 ${height}`} className="w-full h-56 overflow-visible">
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 25, 50].map((level) => {
            const y = padding.top + (1 - level / maxVal) * (height - padding.top - padding.bottom);
            return (
              <g key={level}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={500 - padding.right}
                  y2={y}
                  stroke="currentColor"
                  className="text-slate-200 dark:text-slate-800"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="text-[10px] fill-slate-400"
                >
                  {level}%
                </text>
              </g>
            );
          })}

          {/* Area under curve */}
          <path d={areaD} fill="url(#trendGradient)" />

          {/* Line */}
          <path
            d={pathD}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Points */}
          {points.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="3.5"
              className="fill-amber-500 stroke-white dark:stroke-slate-900 stroke-2 hover:r-5 transition-all cursor-pointer"
            >
              <title>{`${p.day}: ${p.late_percentage}% (${p.late_count} ta)`}</title>
            </circle>
          ))}
        </svg>

        <div className="flex justify-between text-[11px] text-slate-400 mt-1 px-4">
          <span>{data[0]?.day}</span>
          <span>{data[Math.floor(data.length / 2)]?.day}</span>
          <span>{data[data.length - 1]?.day}</span>
        </div>
      </div>
    </div>
  );
};
