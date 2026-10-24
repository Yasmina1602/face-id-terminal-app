import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users, UserPlus, Search, Edit2, Calendar as CalendarIcon, Check, X, Shield, Clock
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const Employees: React.FC = () => {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState<string>('');
  const [page, setPage] = useState<number>(1);

  // Xodim qo'shish / tahrirlash modali
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [editingEmp, setEditingEmp] = useState<any | null>(null);
  const [empNo, setEmpNo] = useState<string>('');
  const [empName, setEmpName] = useState<string>('');
  const [workStart, setWorkStart] = useState<string>('09:00');
  const [department, setDepartment] = useState<string>('');
  const [jobTitle, setJobTitle] = useState<string>('');
  const [active, setActive] = useState<boolean>(true);

  // Kalendar ko'rish modali
  const [calendarEmp, setCalendarEmp] = useState<any | null>(null);
  const currentMonth = new Date().toISOString().substring(0, 7); // YYYY-MM
  const [selectedMonth, setSelectedMonth] = useState<string>(currentMonth);

  const { data, isLoading } = useQuery({
    queryKey: ['employees', search, page],
    queryFn: async () => {
      const res = await api.get(`/employees?search=${search}&page=${page}&limit=50`);
      return res.data;
    },
  });

  const { data: calendarData, isLoading: loadingCalendar } = useQuery({
    queryKey: ['employeeCalendar', calendarEmp?.emp_no, selectedMonth],
    queryFn: async () => {
      if (!calendarEmp) return null;
      const res = await api.get(`/employees/${calendarEmp.emp_no}/calendar?month=${selectedMonth}`);
      return res.data;
    },
    enabled: !!calendarEmp,
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (editingEmp) {
        await api.patch(`/employees/${editingEmp.emp_no}`, {
          name: empName,
          work_start: workStart,
          department: department || null,
          job_title: jobTitle || null,
          active,
        });
      } else {
        await api.post('/employees', {
          emp_no: empNo,
          name: empName,
          work_start: workStart,
          department: department || null,
          job_title: jobTitle || null,
          active,
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Xatolik yuz berdi');
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: async ({ emp_no, nextActive }: { emp_no: string; nextActive: boolean }) => {
      await api.patch(`/employees/${emp_no}`, { active: nextActive });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
  });

  const resetForm = () => {
    setEditingEmp(null);
    setEmpNo('');
    setEmpName('');
    setWorkStart('09:00');
    setDepartment('');
    setJobTitle('');
    setActive(true);
  };

  const openEditModal = (emp: any) => {
    setEditingEmp(emp);
    setEmpNo(emp.emp_no);
    setEmpName(emp.name);
    setWorkStart(emp.work_start || '09:00');
    setDepartment(emp.department || '');
    setJobTitle(emp.job_title || '');
    setActive(emp.active);
    setModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Yuqori panel */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Xodimlar Ro'yxati</h2>
          <p className="text-xs text-slate-500">Tizimda ro'yxatdan o'tgan barcha xodimlar va ularning ish vaqtlari</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Qidirish (ism yoki ID)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="text-xs pl-9 pr-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 w-52 sm:w-64 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {isAdmin && (
            <button
              onClick={() => {
                resetForm();
                setModalOpen(true);
              }}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-brand-500 hover:bg-brand-600 text-white shadow-sm transition-colors"
            >
              <UserPlus className="w-4 h-4" />
              Yangi Xodim
            </button>
          )}
        </div>
      </div>

      {/* Xodimlar jadvali */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-slate-500 text-xs font-semibold">
                <th className="py-3 px-4">Xodim ID</th>
                <th className="py-3 px-4">Ism-Familiya</th>
                <th className="py-3 px-4">Bo'lim</th>
                <th className="py-3 px-4">Lavozim</th>
                <th className="py-3 px-4">Ish Boshlanishi</th>
                <th className="py-3 px-4">Holat</th>
                <th className="py-3 px-4 text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 text-sm">
                    Yuklanmoqda...
                  </td>
                </tr>
              ) : data?.items?.length > 0 ? (
                data.items.map((emp: any) => (
                  <tr key={emp.emp_no} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs font-bold text-slate-700 dark:text-slate-300">
                      {emp.emp_no}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">{emp.name}</td>
                    <td className="py-3 px-4 text-xs text-slate-500">{emp.department || '-'}</td>
                    <td className="py-3 px-4 text-xs text-slate-500">{emp.job_title || '-'}</td>
                    <td className="py-3 px-4 text-xs font-medium text-slate-800 dark:text-slate-200">
                      {emp.work_start}
                    </td>
                    <td className="py-3 px-4">
                      {emp.active ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                          Faol
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500">
                          Nofaol
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setCalendarEmp(emp)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950 transition-colors"
                          title="Oylik davomat kalendarini ko'rish"
                        >
                          <CalendarIcon className="w-4 h-4" />
                        </button>
                        {isAdmin && (
                          <button
                            onClick={() => openEditModal(emp)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950 transition-colors"
                            title="Tahrirlash"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 text-sm">
                    Xodimlar topilmadi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Xodim qo'shish / tahrirlash */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                {editingEmp ? 'Xodimni Tahrirlash' : 'Yangi Xodim Qo\'shish'}
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                saveMutation.mutate();
              }}
              className="space-y-3 text-xs"
            >
              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">
                  Xodim ID raqami (Hikvision bilan mos):
                </label>
                <input
                  type="text"
                  required
                  disabled={!!editingEmp}
                  placeholder="00000001"
                  value={empNo}
                  onChange={(e) => setEmpNo(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 font-mono disabled:opacity-60"
                />
              </div>

              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Ism-Familiya:</label>
                <input
                  type="text"
                  required
                  placeholder="Ali Valiyev"
                  value={empName}
                  onChange={(e) => setEmpName(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>

              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Ish boshlanish vaqti:</label>
                <input
                  type="time"
                  required
                  value={workStart}
                  onChange={(e) => setWorkStart(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>

              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Bo'lim (Department):</label>
                <input
                  type="text"
                  placeholder="IT, Buxgalteriya, Savdo..."
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>

              <div>
                <label className="font-medium text-slate-600 dark:text-slate-400 mb-1 block">Lavozim:</label>
                <input
                  type="text"
                  placeholder="Dasturchi, Mutaxassis..."
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="empActive"
                  checked={active}
                  onChange={(e) => setActive(e.target.checked)}
                  className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="empActive" className="text-slate-700 dark:text-slate-300 font-medium">
                  Faol xodim (Davomat qabul qilinadi)
                </label>
              </div>

              <div className="flex gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="flex-1 py-2 font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-xl"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={saveMutation.isPending}
                  className="flex-1 py-2 font-semibold text-white bg-brand-500 hover:bg-brand-600 rounded-xl shadow-md transition-colors"
                >
                  {saveMutation.isPending ? 'Saqlanmoqda...' : 'Saqlash'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Oylik Kalendar Ko'rinishi */}
      {calendarEmp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {calendarEmp.name} - Oylik Davomat Kalendari
                </h3>
                <p className="text-xs text-slate-500">ID: {calendarEmp.emp_no}</p>
              </div>
              <button
                onClick={() => setCalendarEmp(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Oyni tanlang:</span>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 font-medium"
              />
            </div>

            {loadingCalendar ? (
              <div className="py-12 text-center text-slate-400 text-sm">Kalendar yuklanmoqda...</div>
            ) : (
              <div className="grid grid-cols-7 gap-2">
                {['Du', 'Se', 'Cho', 'Pay', 'Ju', 'Sha', 'Ya'].map((d) => (
                  <div key={d} className="text-center text-xs font-bold text-slate-400 py-1">
                    {d}
                  </div>
                ))}
                {calendarData?.days?.map((day: any) => {
                  const dayNum = parseInt(day.day.split('-')[2]);
                  let bg = 'bg-slate-100 dark:bg-slate-800 text-slate-600';
                  if (day.status === 'present') bg = 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-300';
                  if (day.status === 'late') bg = 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300';
                  if (day.status === 'absent') bg = 'bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300';
                  if (day.status === 'weekend') bg = 'bg-slate-200/50 dark:bg-slate-800/40 text-slate-400';

                  return (
                    <div
                      key={day.day}
                      className={`h-16 rounded-xl p-1.5 flex flex-col justify-between text-xs transition-transform hover:scale-105 ${bg}`}
                    >
                      <span className="font-bold">{dayNum}</span>
                      <div className="text-[10px] leading-tight">
                        {day.first_in && <div>In: {day.first_in}</div>}
                        {day.late_minutes > 0 && <div className="font-semibold text-amber-600">+{day.late_minutes}m</div>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
