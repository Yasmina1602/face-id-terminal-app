import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calendar, Search, Filter, Edit3, RefreshCw, AlertCircle, CheckCircle, Clock, X
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const Attendance: React.FC = () => {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();

  const todayStr = new Date().toISOString().split('T')[0];
  const [dateFrom, setDateFrom] = useState<string>(todayStr);
  const [dateTo, setDateTo] = useState<string>(todayStr);
  const [searchEmp, setSearchEmp] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);

  // Modal holati
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [overrideStatus, setOverrideStatus] = useState<string>('');
  const [newFirstIn, setNewFirstIn] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [fineAmount, setFineAmount] = useState<string>('0');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['attendance', dateFrom, dateTo, searchEmp, statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (dateFrom) params.append('from', dateFrom);
      if (dateTo) params.append('to', dateTo);
      if (searchEmp) params.append('emp_no', searchEmp);
      if (statusFilter) params.append('status', statusFilter);
      params.append('page', String(page));
      params.append('limit', '50');

      const res = await api.get(`/attendance?${params.toString()}`);
      return res.data;
    },
    refetchInterval: 5000, // Har 5 soniyada real-time yangilash
  });

  const adjustmentMutation = useMutation({
    mutationFn: async (payload: any) => {
      await api.put(`/attendance/${payload.emp_no}/${payload.day}/adjustment`, {
        status_override: payload.status_override || null,
        new_first_in: payload.new_first_in || null,
        reason: payload.reason || null,
        fine_amount: Number(payload.fine_amount) || 0,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance'] });
      queryClient.invalidateQueries({ queryKey: ['overview'] });
      setSelectedRecord(null);
    },
  });

  const rebuildMutation = useMutation({
    mutationFn: async () => {
      await api.post('/attendance/rebuild', { day_from: dateFrom, day_to: dateTo });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance'] });
      queryClient.invalidateQueries({ queryKey: ['overview'] });
      alert('Davomat muvaffaqiyatli qayta hisoblandi!');
    },
  });

  const openAdjustmentModal = (rec: any) => {
    setSelectedRecord(rec);
    setOverrideStatus(rec.status);
    setNewFirstIn(rec.first_in ? rec.first_in.substring(0, 5) : '');
    setReason(rec.adjustment_reason || '');
    setFineAmount(String(rec.fine_amount || 0));
  };

  const saveAdjustment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecord) return;
    adjustmentMutation.mutate({
      emp_no: selectedRecord.emp_no,
      day: selectedRecord.day,
      status_override: overrideStatus,
      new_first_in: newFirstIn,
      reason,
      fine_amount: fineAmount,
    });
  };

  const getStatusBadge = (status: string, late: number) => {
    switch (status) {
      case 'present':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle className="w-3 h-3" /> Vaqtida keldi
          </span>
        );
      case 'late':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
            <AlertCircle className="w-3 h-3" /> Kech ({late} daq)
          </span>
        );
      case 'absent':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
            <Clock className="w-3 h-3" /> Kelmadi
          </span>
        );
      case 'weekend':
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-500">Dam olish</span>;
      case 'holiday':
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-50 dark:bg-purple-950 text-purple-600">Bayram</span>;
      case 'leave':
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-950 text-blue-600">Ta'tilda</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-500">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Yuqori panel: Qidiruv va Filtrlar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Kunlik Davomat Jadvali</h2>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                Real-vaqt (Jonli)
              </span>
            </div>
            <p className="text-xs text-slate-500">Xodimlar o'tishlari avtomatik real-vaqt rejimida yangilanadi</p>
          </div>

          {isAdmin && (
            <button
              onClick={() => rebuildMutation.mutate()}
              disabled={rebuildMutation.isPending}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-brand-50 hover:bg-brand-100 text-brand-700 dark:bg-brand-950 dark:hover:bg-brand-900 dark:text-brand-300 border border-brand-200 dark:border-brand-800 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${rebuildMutation.isPending ? 'animate-spin' : ''}`} />
              Qayta hisoblash
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Sanadan:</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Sanagacha:</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Xodim ID:</label>
            <input
              type="text"
              placeholder="Masalan: 00000001"
              value={searchEmp}
              onChange={(e) => setSearchEmp(e.target.value)}
              className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Holat:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">Barchasi</option>
              <option value="present">Vaqtida kelgan</option>
              <option value="late">Kech qolgan</option>
              <option value="absent">Kelmagan</option>
              <option value="weekend">Dam olish</option>
              <option value="holiday">Bayram</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => refetch()}
              className="w-full text-xs font-semibold px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl shadow-sm transition-colors"
            >
              Qidirish
            </button>
          </div>
        </div>
      </div>

      {/* Jadval */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-slate-500 text-xs font-semibold">
                <th className="py-3 px-4">Sana</th>
                <th className="py-3 px-4">Xodim</th>
                <th className="py-3 px-4">Bo'lim</th>
                <th className="py-3 px-4">Keldi</th>
                <th className="py-3 px-4">Ketdi</th>
                <th className="py-3 px-4">Ish vaqti</th>
                <th className="py-3 px-4">Holat</th>
                <th className="py-3 px-4">Tuzatish / Sabab</th>
                {isAdmin && <th className="py-3 px-4 text-right">Amal</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
              {isLoading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400 text-sm">
                    Yuklanmoqda...
                  </td>
                </tr>
              ) : data?.items?.length > 0 ? (
                data.items.map((row: any) => (
                  <tr key={`${row.emp_no}_${row.day}`} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-700 dark:text-slate-300">{row.day}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                      {row.employee_name}
                      <span className="block text-[11px] font-normal text-slate-400">ID: {row.emp_no}</span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">{row.department || '-'}</td>
                    <td className="py-3 px-4 text-xs font-medium text-slate-800 dark:text-slate-200">
                      {row.first_in ? row.first_in.substring(0, 5) : '-'}
                    </td>
                    <td className="py-3 px-4 text-xs font-medium text-slate-800 dark:text-slate-200">
                      {row.last_out ? row.last_out.substring(0, 5) : '-'}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600 dark:text-slate-400">
                      {row.worked_minutes ? `${Math.floor(row.worked_minutes / 60)}s ${row.worked_minutes % 60}d` : '-'}
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(row.status, row.late_minutes)}</td>
                    <td className="py-3 px-4 text-xs">
                      {row.has_adjustment ? (
                        <div>
                          <span className="font-semibold text-brand-600 dark:text-brand-400">Tuzatilgan</span>
                          {row.adjustment_reason && <p className="text-[11px] text-slate-400">{row.adjustment_reason}</p>}
                        </div>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    {isAdmin && (
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => openAdjustmentModal(row)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950 transition-colors"
                          title="Qo'lda tuzatish kiritish"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400 text-sm">
                    Davomat yozuvlari topilmadi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Qo'lda tuzatish kiritish */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Davomatga Tuzatish Kiritish</h3>
                <p className="text-xs text-slate-500">
                  {selectedRecord.employee_name} ({selectedRecord.day})
                </p>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={saveAdjustment} className="space-y-3.5 text-xs">
              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Yangi Holat (Status Override):</label>
                <select
                  value={overrideStatus}
                  onChange={(e) => setOverrideStatus(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200"
                >
                  <option value="present">Vaqtida keldi (Present)</option>
                  <option value="late">Kechikkan (Late)</option>
                  <option value="absent">Kelmagan (Absent)</option>
                  <option value="leave">Ta'tilda / Sababli (Leave)</option>
                  <option value="weekend">Dam olish (Weekend)</option>
                  <option value="holiday">Bayram (Holiday)</option>
                </select>
              </div>

              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Kelgan vaqti (agar bo'lsa):</label>
                <input
                  type="time"
                  value={newFirstIn}
                  onChange={(e) => setNewFirstIn(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200"
                />
              </div>

              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Tuzatish sababi / Izoh:</label>
                <textarea
                  rows={2}
                  placeholder="Sababini kiriting (masalan: topshiriq bilan borgan)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200"
                />
              </div>

              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Jarima miqdori (so'm):</label>
                <input
                  type="number"
                  value={fineAmount}
                  onChange={(e) => setFineAmount(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedRecord(null)}
                  className="flex-1 py-2 font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-xl"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={adjustmentMutation.isPending}
                  className="flex-1 py-2 font-semibold text-white bg-brand-500 hover:bg-brand-600 rounded-xl shadow-md transition-colors"
                >
                  {adjustmentMutation.isPending ? 'Saqlanmoqda...' : 'Saqlash'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
