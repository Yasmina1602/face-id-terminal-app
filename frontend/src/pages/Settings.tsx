import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Shield, MessageSquare, Calendar, Sliders, History, Plus, Trash2, Check, AlertTriangle
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const Settings: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'admins' | 'chats' | 'calendar' | 'general' | 'audit'>('admins');

  // Admin qo'shish formasi
  const [newAdminTgId, setNewAdminTgId] = useState<string>('');
  const [newAdminName, setNewAdminName] = useState<string>('');
  const [newAdminUsername, setNewAdminUsername] = useState<string>('');
  const [newAdminPassword, setNewAdminPassword] = useState<string>('');
  const [newAdminRole, setNewAdminRole] = useState<'admin' | 'viewer'>('viewer');

  // Bayram qo'shish formasi
  const [calDay, setCalDay] = useState<string>('');
  const [calIsWorkday, setCalIsWorkday] = useState<boolean>(false);
  const [calNote, setCalNote] = useState<string>('');

  // 1. Adminlar
  const { data: admins } = useQuery({
    queryKey: ['adminsList'],
    queryFn: async () => (await api.get('/admins')).data,
    enabled: activeTab === 'admins',
  });

  // 2. Chatlar
  const { data: chats } = useQuery({
    queryKey: ['chatsList'],
    queryFn: async () => (await api.get('/chats')).data,
    enabled: activeTab === 'chats',
  });

  // 3. Taqvim
  const { data: calendarDays } = useQuery({
    queryKey: ['calendarDays'],
    queryFn: async () => (await api.get('/calendar')).data,
    enabled: activeTab === 'calendar',
  });

  // 4. Sozlamalar
  const { data: appSettings } = useQuery({
    queryKey: ['appSettings'],
    queryFn: async () => (await api.get('/settings')).data,
    enabled: activeTab === 'general',
  });

  // 5. Audit
  const { data: auditLogs } = useQuery({
    queryKey: ['auditLogs'],
    queryFn: async () => (await api.get('/audit?limit=50')).data,
    enabled: activeTab === 'audit',
  });

  const addAdminMutation = useMutation({
    mutationFn: async () => {
      await api.post('/admins', {
        tg_id: Number(newAdminTgId),
        name: newAdminName,
        username: newAdminUsername || null,
        password: newAdminPassword || null,
        role: newAdminRole,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminsList'] });
      setNewAdminTgId('');
      setNewAdminName('');
      setNewAdminUsername('');
      setNewAdminPassword('');
    },
    onError: (err: any) => alert(err.response?.data?.detail || 'Xato'),
  });

  const deleteAdminMutation = useMutation({
    mutationFn: async (tgId: number) => {
      await api.delete(`/admins/${tgId}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['adminsList'] }),
    onError: (err: any) => alert(err.response?.data?.detail || 'Xato'),
  });

  const deleteChatMutation = useMutation({
    mutationFn: async (chatId: number) => {
      await api.delete(`/chats/${chatId}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['chatsList'] }),
  });

  const saveCalendarDayMutation = useMutation({
    mutationFn: async () => {
      await api.put('/calendar', {
        day: calDay,
        is_workday: calIsWorkday,
        note: calNote || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendarDays'] });
      setCalDay('');
      setCalNote('');
    },
  });

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Tizim Sozlamalari</h2>
        <p className="text-xs text-slate-500">Adminlar, Telegram guruhlari, bayramlar va xavfsizlik audit jurnali</p>

        {/* Tab tugmalari */}
        <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
          {[
            { id: 'admins', label: 'Adminlar va Rollar', icon: Shield },
            { id: 'chats', label: 'Telegram Guruhlar', icon: MessageSquare },
            { id: 'calendar', label: 'Bayramlar Taqvimi', icon: Calendar },
            { id: 'general', label: 'Umumiy Sozlamalar', icon: Sliders },
            { id: 'audit', label: 'Audit Jurnali', icon: History },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                  active
                    ? 'bg-brand-500 text-white shadow-sm'
                    : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 1. Adminlar */}
      {activeTab === 'admins' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 dark:text-white mb-3">Adminlar Ro'yxati</h3>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {admins?.map((a: any) => (
                <div key={a.tg_id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-slate-800 dark:text-slate-200">{a.name || 'Ismsiz'}</span>
                    <p className="text-slate-400">ID: {a.tg_id} {a.username ? `(@${a.username})` : ''}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-0.5 rounded-full font-semibold ${
                      a.role === 'admin'
                        ? 'bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 border border-brand-200'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                    }`}>
                      {a.role === 'admin' ? 'Administrator' : 'Ko\'ruvchi'}
                    </span>
                    {Number(user?.id) !== a.tg_id && (
                      <button
                        onClick={() => deleteAdminMutation.mutate(a.tg_id)}
                        className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                        title="Adminni o'chirish"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Admin Qo'shish</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                addAdminMutation.mutate();
              }}
              className="space-y-2.5 text-xs"
            >
              <div>
                <label className="font-medium text-slate-500 mb-1 block">Telegram ID yoki Yangi ID:</label>
                <input
                  type="number"
                  required
                  placeholder="Masalan: 12345678"
                  value={newAdminTgId}
                  onChange={(e) => setNewAdminTgId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <div>
                <label className="font-medium text-slate-500 mb-1 block">Ism:</label>
                <input
                  type="text"
                  required
                  placeholder="Admin ismi"
                  value={newAdminName}
                  onChange={(e) => setNewAdminName(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <div>
                <label className="font-medium text-slate-500 mb-1 block">Web Login (username):</label>
                <input
                  type="text"
                  placeholder="masalan: bosh_admin"
                  value={newAdminUsername}
                  onChange={(e) => setNewAdminUsername(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <div>
                <label className="font-medium text-slate-500 mb-1 block">Parol (Web kirish uchun):</label>
                <input
                  type="password"
                  placeholder="Parol kiriting"
                  value={newAdminPassword}
                  onChange={(e) => setNewAdminPassword(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <div>
                <label className="font-medium text-slate-500 mb-1 block">Rol:</label>
                <select
                  value={newAdminRole}
                  onChange={(e) => setNewAdminRole(e.target.value as any)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                >
                  <option value="viewer">Ko'ruvchi (Faqat ko'rish huquqi)</option>
                  <option value="admin">Administrator (To'liq boshqaruv)</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={addAdminMutation.isPending}
                className="w-full py-2.5 rounded-xl font-semibold text-white bg-brand-500 hover:bg-brand-600 transition-colors shadow-sm mt-2"
              >
                {addAdminMutation.isPending ? 'Qo\'shilmoqda...' : 'Admin Qo\'shish'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* 2. Chatlar */}
      {activeTab === 'chats' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Ulangan Telegram Guruhlar</h3>
          <p className="text-xs text-slate-500">
            Bot xodimlar davomati va rasmlarni ushbu guruhlarga yuboradi. Botni guruhga qo'shib, /start bosilsa avtomatik qo'shiladi.
          </p>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {chats?.length > 0 ? (
              chats.map((c: any) => (
                <div key={c.chat_id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-slate-800 dark:text-slate-200">{c.title || 'Nomsiz guruh'}</p>
                    <p className="text-slate-400">Chat ID: {c.chat_id}</p>
                  </div>
                  <button
                    onClick={() => deleteChatMutation.mutate(c.chat_id)}
                    className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                    title="Guruhni uzish"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <p className="py-8 text-center text-slate-400 text-xs">Hozircha ulangan guruhlar yo'q</p>
            )}
          </div>
        </div>
      )}

      {/* 3. Taqvim */}
      {activeTab === 'calendar' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 dark:text-white mb-3">Taqvim Istisnolari</h3>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {calendarDays?.length > 0 ? (
                calendarDays.map((cd: any) => (
                  <div key={cd.day} className="py-2.5 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-slate-800 dark:text-slate-200">{cd.day}</span>
                      <p className="text-slate-400">{cd.note || 'Izohsiz'}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full font-semibold ${
                      cd.is_workday ? 'bg-emerald-50 text-emerald-600' : 'bg-purple-50 text-purple-600'
                    }`}>
                      {cd.is_workday ? 'Ish kuni' : 'Bayram / Dam olish'}
                    </span>
                  </div>
                ))
              ) : (
                <p className="py-6 text-center text-slate-400 text-xs">Maxsus bayram kunlari belgilanmagan</p>
              )}
            </div>
          </div>

          <div className="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Kuni Belgilash</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                saveCalendarDayMutation.mutate();
              }}
              className="space-y-3 text-xs"
            >
              <div>
                <label className="font-medium text-slate-500 mb-1 block">Sana:</label>
                <input
                  type="date"
                  required
                  value={calDay}
                  onChange={(e) => setCalDay(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="isWorkday"
                  checked={calIsWorkday}
                  onChange={(e) => setCalIsWorkday(e.target.checked)}
                  className="w-4 h-4 rounded text-brand-600"
                />
                <label htmlFor="isWorkday" className="text-slate-700 dark:text-slate-300 font-medium">
                  Ish kuni qilib belgilash (Shanba/Yakshanba bo'lsa ham)
                </label>
              </div>
              <div>
                <label className="font-medium text-slate-500 mb-1 block">Izoh (bayram nomi):</label>
                <input
                  type="text"
                  placeholder="Navro'z, Mustaqillik kuni..."
                  value={calNote}
                  onChange={(e) => setCalNote(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 rounded-xl font-semibold text-white bg-brand-500 hover:bg-brand-600 shadow-sm"
              >
                Saqlash
              </button>
            </form>
          </div>
        </div>
      )}

      {/* 4. Umumiy sozlamalar */}
      {activeTab === 'general' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm max-w-xl space-y-4">
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Asosiy Parametrlar</h3>
          <div className="space-y-3 text-xs text-slate-600 dark:text-slate-400">
            <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
              <span>Standart ish boshlanish vaqti:</span>
              <span className="font-semibold text-slate-900 dark:text-white">
                {appSettings?.general?.work_start || '09:00'}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
              <span>Kechikish uchun imtiyoz daqiqasi:</span>
              <span className="font-semibold text-slate-900 dark:text-white">
                {appSettings?.general?.grace_minutes ?? 0} daqiqa
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
              <span>Xom attendance yozuvlarini saqlash muddati:</span>
              <span className="font-semibold text-slate-900 dark:text-white">
                {appSettings?.general?.retention_days ?? 180} kun
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800">
              <span>Haftalik dam olish kuni:</span>
              <span className="font-semibold text-slate-900 dark:text-white">Yakshanba</span>
            </div>
          </div>
        </div>
      )}

      {/* 5. Audit jurnali */}
      {activeTab === 'audit' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-slate-500 font-semibold">
                  <th className="py-3 px-4">Vaqt</th>
                  <th className="py-3 px-4">Foydalanuvchi</th>
                  <th className="py-3 px-4">Amal</th>
                  <th className="py-3 px-4">Obyekt</th>
                  <th className="py-3 px-4">Tafsilotlar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {auditLogs?.items?.map((log: any) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 text-slate-500">{new Date(log.at).toLocaleString('uz-UZ')}</td>
                    <td className="py-2.5 px-4 font-semibold text-slate-800 dark:text-slate-200">{log.actor || 'Tizim'}</td>
                    <td className="py-2.5 px-4 font-mono text-brand-600 dark:text-brand-400">{log.action}</td>
                    <td className="py-2.5 px-4">{log.target || '-'}</td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-400">
                      {log.details ? JSON.stringify(log.details) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
