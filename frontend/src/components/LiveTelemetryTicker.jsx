import React from 'react';
import { Database, Zap, Shield, TrendingUp, Users, Building, Activity, Globe } from 'lucide-react';

export default function LiveTelemetryTicker({ lang = 'uz', totalDeals = 500000, totalTurnover = "220.48 Trln" }) {
  const items = [
    {
      icon: Activity,
      label: lang === 'uz' ? "JONLI REJIM" : "ЖИВОЙ РЕЖИМ",
      value: "UZEX SPOT EXCHANGE",
      color: "text-emerald-400"
    },
    {
      icon: Database,
      label: lang === 'uz' ? "DUCKDB IN-MEMORY" : "DUCKDB В ПАМЯТИ",
      value: `${(totalDeals || 500000).toLocaleString()} ${lang === 'uz' ? 'BITIM' : 'СДЕЛОК'}`,
      color: "text-cyan-400"
    },
    {
      icon: Zap,
      label: lang === 'uz' ? "O'RTACHA TEZLIK" : "СКОРОСТЬ ЗАПРОСА",
      value: "~3.2 ms (DuckDB Engine)",
      color: "text-yellow-400"
    },
    {
      icon: TrendingUp,
      label: lang === 'uz' ? "UMUMIY AYLANMA" : "ОБЩИЙ ОБОРОТ",
      value: `${totalTurnover} ${lang === 'uz' ? "so'm" : "сум"}`,
      color: "text-emerald-400"
    },
    {
      icon: Shield,
      label: lang === 'uz' ? "ANTI-HALLUCINATION" : "АНТИ-ГАЛЛЮЦИНАЦИЯ",
      value: "100% FACTUAL ONLY",
      color: "text-purple-400"
    },
    {
      icon: Users,
      label: lang === 'uz' ? "ISHTIROKCHILAR" : "УЧАСТНИКИ",
      value: "14 392 REYESTR",
      color: "text-cyan-400"
    },
    {
      icon: Building,
      label: lang === 'uz' ? "BROKERLAR" : "БРОКЕРЫ",
      value: "120 O'RIN (BK001-BK120)",
      color: "text-blue-400"
    },
    {
      icon: Globe,
      label: lang === 'uz' ? "QAMROV" : "ОХВАТ",
      value: "2022-01-03 — 2026-10-30",
      color: "text-slate-300"
    }
  ];

  // Repeat for continuous seamless marquee
  const tickerItems = [...items, ...items];

  return (
    <div className="w-full bg-slate-950/80 border-b border-cyan-500/20 backdrop-blur-md overflow-hidden py-1.5 z-40 select-none">
      <div className="animate-ticker flex items-center gap-8 text-[11px] font-mono">
        {tickerItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} className="flex items-center gap-2 flex-shrink-0 opacity-90 hover:opacity-100 transition-opacity">
              <Icon className={`w-3.5 h-3.5 ${item.color}`} />
              <span className="text-slate-400 font-semibold uppercase tracking-wider">{item.label}:</span>
              <span className="text-white font-bold bg-white/5 px-2 py-0.5 rounded border border-white/10">{item.value}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
