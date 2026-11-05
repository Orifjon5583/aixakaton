import React, { useState, useEffect } from 'react';
import { Clock, Search, Download, Trash2, ArrowUpRight, CheckCircle2, AlertCircle, Copy, CheckCheck } from 'lucide-react';
import { soundEffects } from './SoundEffects';

export default function QueryHistoryTab({ lang = 'uz', onRerunQuery }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/history?limit=100');
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Error fetching history:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleClear = async () => {
    if (!window.confirm(lang === 'uz' ? "Savollar tarixini tozalashni tasdiqlaysizmi?" : "Очистить историю запросов?")) return;
    soundEffects.playClick();
    try {
      await fetch('/api/history', { method: 'DELETE' });
      setHistory([]);
    } catch (e) {
      console.error(e);
    }
  };

  const copySQL = (id, sql) => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    soundEffects.playClick();
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filtered = history.filter(item => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return item.question?.toLowerCase().includes(s) || item.answer?.toLowerCase().includes(s);
  });

  return (
    <div className="space-y-6 text-left animate-fadeIn select-none">
      
      {/* Top Header & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#1b2b1b]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-[#8aa587] uppercase tracking-wider">
            <Clock className="w-4 h-4 text-[#C8EA4A]" />
            <span>{lang === 'uz' ? 'Audit Jurnali & Doimiy Saqlash' : 'Журнал Аудита и История Запросов'}</span>
          </div>
          <h2 className="text-xl font-bold font-mono text-white mt-1">
            {lang === 'uz' ? 'Berilgan Barcha Savollar Tarixi' : 'История Заданных Вопросов'}
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={lang === 'uz' ? "Savollardan qidirish..." : "Поиск по истории..."}
              className="w-56 sm:w-72 px-3 py-1.5 rounded-lg bg-[#111c11] border border-[#243a24] text-xs font-mono text-white placeholder-[#5a7357] focus:outline-none focus:border-[#C8EA4A]"
            />
          </div>

          {/* Export CSV */}
          <a
            href="/api/history/export"
            download="uzex_query_history.csv"
            onClick={() => soundEffects.playSuccess()}
            className="px-3 py-1.5 rounded-lg bg-[#162416] hover:bg-[#203420] border border-[#2b442b] text-xs font-mono text-[#C8EA4A] flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>CSV</span>
          </a>

          {/* Clear */}
          {history.length > 0 && (
            <button
              onClick={handleClear}
              className="px-2.5 py-1.5 rounded-lg bg-[#1e1212] hover:bg-[#2e1818] border border-rose-500/30 text-rose-400 hover:text-rose-300 text-xs font-mono flex items-center gap-1 transition-colors"
              title="Tarixni tozalash"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* History Items List */}
      <div className="space-y-3 font-mono text-xs">
        {loading ? (
          <div className="p-12 text-center text-[#708c6d] animate-pulse">
            {lang === 'uz' ? 'Savollar tarixi yuklanmoqda...' : 'Загрузка истории запросов...'}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-[#708c6d] rounded-2xl bg-[#090E09] border border-[#1b2b1b]">
            {search ? (
              <span>Hech narsa topilmadi.</span>
            ) : (
              <span>{lang === 'uz' ? 'Hozircha saqlangan savollar mavjud emas. AI Terminalida birinchi savolingizni bering!' : 'Пока нет сохраненных запросов. Задайте первый вопрос в AI-Терминале!'}</span>
            )}
          </div>
        ) : (
          filtered.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <div
                key={item.id}
                className="rounded-xl bg-[#0a120a] border border-[#1f331f] hover:border-[#2f4f2f] transition-all p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="space-y-1 max-w-2xl">
                    <div className="flex items-center gap-2 text-[10px] text-[#6d8869]">
                      <span>#{item.id}</span>
                      <span>•</span>
                      <span>{item.created_at}</span>
                      <span>•</span>
                      <span className="uppercase text-[#C8EA4A] font-bold">{item.detected_lang}</span>
                      {item.execution_time_ms > 0 && (
                        <>
                          <span>•</span>
                          <span className="text-[#70FFC2]">⚡ {item.execution_time_ms} ms</span>
                        </>
                      )}
                      <span>•</span>
                      <span className={`px-1.5 py-0.2 rounded text-[9px] ${
                        item.status === 'success'
                          ? 'bg-[#142614] text-[#C8EA4A] border border-[#233f23]'
                          : 'bg-[#261414] text-rose-300 border border-rose-500/30'
                      }`}>
                        {item.status}
                      </span>
                    </div>

                    <h4 className="text-white font-semibold text-sm leading-snug font-sans">
                      {item.question}
                    </h4>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {onRerunQuery && (
                      <button
                        onClick={() => {
                          soundEffects.playClick();
                          onRerunQuery(item.question);
                        }}
                        className="px-2.5 py-1 rounded bg-[#142214] hover:bg-[#1f361f] border border-[#274227] text-[#C8EA4A] text-xs flex items-center gap-1 transition-colors"
                        title="Savolni qayta berish"
                      >
                        <span>Qayta berish</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </button>
                    )}

                    <button
                      onClick={() => {
                        soundEffects.playClick();
                        setExpandedId(isExpanded ? null : item.id);
                      }}
                      className="px-2 py-1 rounded bg-[#101910] text-[#708c6d] hover:text-white border border-[#203220] text-xs transition-colors"
                    >
                      {isExpanded ? 'Yopish' : 'Batafsil'}
                    </button>
                  </div>
                </div>

                {/* Expanded Details: Answer & SQL */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-[#182618] space-y-3 animate-fadeIn text-xs">
                    <div>
                      <div className="text-[10px] uppercase text-[#6d8869] mb-1">Javob:</div>
                      <div className="p-3 rounded-lg bg-[#0e170e] border border-[#1b2b1b] text-[#d4e4d2] font-sans whitespace-pre-line leading-relaxed">
                        {item.answer}
                      </div>
                    </div>

                    {item.executed_sql && (
                      <div>
                        <div className="flex items-center justify-between text-[10px] uppercase text-[#6d8869] mb-1">
                          <span>DuckDB SQL so‘rovi:</span>
                          <button
                            onClick={() => copySQL(item.id, item.executed_sql)}
                            className="text-[#C8EA4A] hover:underline flex items-center gap-1 lowercase"
                          >
                            {copiedId === item.id ? <CheckCheck className="w-3 h-3 text-[#70FFC2]" /> : <Copy className="w-3 h-3" />}
                            <span>{copiedId === item.id ? 'nusxalandi' : 'nusxa olish'}</span>
                          </button>
                        </div>
                        <pre className="p-3 rounded-lg bg-black/80 border border-[#203620] text-[#C8EA4A] text-[11px] overflow-x-auto whitespace-pre-wrap leading-relaxed">
                          {item.executed_sql}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
