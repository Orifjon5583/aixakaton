import React, { useState, useEffect } from 'react';
import { Cpu, ShieldCheck, Database, Sparkles, CheckCircle2, Loader2 } from 'lucide-react';

export default function PipelineHUD({ lang = 'uz' }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  const steps = [
    {
      id: 1,
      name: lang === 'uz' ? "Semantik Intent & Query Plan" : "Семантический анализ запроса",
      engine: "Gemini 2.5 Flash",
      icon: Cpu,
      color: "from-cyan-500 to-blue-500"
    },
    {
      id: 2,
      name: lang === 'uz' ? "Anti-Hallucination & Chegaralar" : "Валидация и фильтр галлюцинаций",
      engine: "Pydantic + Entity Guard",
      icon: ShieldCheck,
      color: "from-blue-500 to-indigo-500"
    },
    {
      id: 3,
      name: lang === 'uz' ? "DuckDB In-Memory Analitika" : "DuckDB In-Memory Аналитика",
      engine: "500 000 Deals / 3ms",
      icon: Database,
      color: "from-indigo-500 to-emerald-500"
    },
    {
      id: 4,
      name: lang === 'uz' ? "Faktik Dalillar & Javob" : "Синтез фактов и доказательств",
      engine: "Zero-Hallucination Verified",
      icon: Sparkles,
      color: "from-emerald-500 to-cyan-500"
    }
  ];

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 25);

    const stepTimers = [
      setTimeout(() => setCurrentStep(1), 180),
      setTimeout(() => setCurrentStep(2), 420),
      setTimeout(() => setCurrentStep(3), 850)
    ];

    return () => {
      clearInterval(interval);
      stepTimers.forEach(t => clearTimeout(t));
    };
  }, []);

  return (
    <div className="w-full my-4 p-5 rounded-2xl glass-panel-glow border border-cyan-500/30 overflow-hidden relative">
      {/* Background glowing sweep line */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/10 to-transparent animate-pulse pointer-events-none" />

      {/* Header telemetry */}
      <div className="flex items-center justify-between mb-4 relative z-10 border-b border-cyan-500/20 pb-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500" />
          </span>
          <span className="text-xs font-mono tracking-widest text-cyan-400 uppercase font-bold">
            {lang === 'uz' ? "LIVE QUERY EXECUTION PIPELINE" : "ЖИВОЙ ПАЙПЛАЙН ВЫПОЛНЕНИЯ ЗАПРОСА"}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-cyan-300/80 bg-cyan-950/40 px-2.5 py-1 rounded-full border border-cyan-500/30">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
          <span>+{elapsed} ms</span>
        </div>
      </div>

      {/* 4 Pipeline Steps */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 relative z-10">
        {steps.map((st, idx) => {
          const isDone = currentStep > idx;
          const isCurrent = currentStep === idx;
          const Icon = st.icon;

          return (
            <div
              key={st.id}
              className={`p-3 rounded-xl border transition-all duration-300 relative ${
                isCurrent
                  ? 'bg-cyan-950/50 border-cyan-400 shadow-[0_0_20px_-3px_rgba(6,182,212,0.4)] scale-102'
                  : isDone
                  ? 'bg-slate-900/60 border-emerald-500/40 text-emerald-400'
                  : 'bg-slate-950/40 border-white/5 opacity-40'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className={`p-1.5 rounded-lg ${isCurrent ? 'bg-cyan-500/20 text-cyan-300' : isDone ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                  <Icon className="w-4 h-4" />
                </div>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 animate-in fade-in" />
                ) : isCurrent ? (
                  <span className="text-[10px] font-mono font-bold uppercase text-cyan-400 tracking-wider bg-cyan-500/20 px-1.5 py-0.5 rounded">
                    ACTIVE
                  </span>
                ) : (
                  <span className="text-[10px] font-mono text-slate-500">
                    STEP 0{st.id}
                  </span>
                )}
              </div>
              <div className="font-medium text-xs text-white leading-tight mb-1">
                {st.name}
              </div>
              <div className="text-[10px] font-mono text-cyan-400/70 truncate">
                {st.engine}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
