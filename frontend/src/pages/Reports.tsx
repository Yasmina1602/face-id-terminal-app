import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileSpreadsheet, Download, User, Users, Calendar, AlertCircle } from 'lucide-react';
import { api } from '../api/client';

export const Reports: React.FC = () => {
  const todayStr = new Date().toISOString().split('T')[0];
  const firstDayOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
    .toISOString()
    .split('T')[0];

  const [dateFrom, setDateFrom] = useState<string>(firstDayOfMonth);
  const [dateTo, setDateTo] = useState<string>(todayStr);
  const [selectedEmp, setSelectedEmp] = useState<string>('');
  const [downloadingSingle, setDownloadingSingle] = useState<boolean>(false);
  const [downloadingSummary, setDownloadingSummary] = useState<boolean>(false);

  const { data: employees } = useQuery({
    queryKey: ['employeesListForReports'],
    queryFn: async () => {
      const res = await api.get('/employees?limit=100');
      return res.data.items || [];
    },
  });

  const downloadSingleExcel = async () => {
    if (!selectedEmp) {
      alert('Iltimos, xodimni tanlang!');
      return;
    }
    setDownloadingSingle(true);
    try {
      const response = await api.get(`/reports/employee/${selectedEmp}/export?from=${dateFrom}&to=${dateTo}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `davomat_xodim_${selectedEmp}_${dateFrom}_${dateTo}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Faylni yuklab olishda xatolik yuz berdi");
    } finally {
      setDownloadingSingle(false);
    }
  };

  const downloadSummaryExcel = async () => {
    setDownloadingSummary(true);
    try {
      const response = await api.get(`/reports/summary/export?from=${dateFrom}&to=${dateTo}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `davomat_barcha_xodimlar_${dateFrom}_${dateTo}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Umumiy hisobotni yuklab olishda xatolik yuz berdi");
    } finally {
      setDownloadingSummary(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Excel Hisobotlar Eksporti</h2>
        <p className="text-xs text-slate-500">
          Telegram bot hisoboti formatida to'liq rasmiy Excel jadvallarini yuklab olish
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Bitta xodim hisoboti */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Bitta Xodim Davomati</h3>
              <p className="text-xs text-slate-500">Har kunlik keldi/ketdi vaqtlari, kechikish va JAMI qatori</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div>
              <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Xodimni tanlang:</label>
              <select
                value={selectedEmp}
                onChange={(e) => setSelectedEmp(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2.5 text-slate-800 dark:text-slate-200"
              >
                <option value="">-- Xodimni tanlang --</option>
                {employees?.map((emp: any) => (
                  <option key={emp.emp_no} value={emp.emp_no}>
                    {emp.name} (ID: {emp.emp_no})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Sanadan:</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Sanagacha:</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
            </div>

            <button
              onClick={downloadSingleExcel}
              disabled={downloadingSingle || !selectedEmp}
              className="w-full mt-4 flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              <Download className="w-4 h-4" />
              {downloadingSingle ? 'Yuklanmoqda...' : 'Excel Yuklab Olish'}
            </button>
          </div>
        </div>

        {/* 2. Barcha xodimlar umumiy tabeli */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Barcha Xodimlar Tabeli</h3>
              <p className="text-xs text-slate-500">"Umumiy", "Kunlik" va "Tabel" matritsasi bilan 3 ta varaq</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Sanadan:</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Sanagacha:</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 space-y-1">
              <p className="font-medium text-slate-700 dark:text-slate-300">Tabel ichidagi qisqartmalar:</p>
              <p>• <b>V</b> - Vaqtida kelgan</p>
              <p>• <b>K (daq)</b> - Kechikkan vaqt</p>
              <p>• <b>X</b> - Kelmagan (absent)</p>
              <p>• <b>D / B</b> - Dam olish / Bayram</p>
            </div>

            <button
              onClick={downloadSummaryExcel}
              disabled={downloadingSummary}
              className="w-full mt-4 flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              <Download className="w-4 h-4" />
              {downloadingSummary ? 'Yuklanmoqda...' : 'Umumiy Tabelni Yuklab Olish'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
