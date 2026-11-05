import React, { useState, useEffect, useRef } from 'react';
import { soundEffects } from './SoundEffects';

// Normalized 2D coordinates for the 14 administrative regions of Uzbekistan
const REGIONS_COORDINATES = {
  'Qoraqalpog‘iston Respublikasi': { x: 190, y: 170, label: 'Нукус / Каракалпакстан', short: 'ККР' },
  'Xorazm viloyati': { x: 310, y: 220, label: 'Ургенч / Хорезм', short: 'ХОР' },
  'Buxoro viloyati': { x: 420, y: 280, label: 'Бухара', short: 'БУХ' },
  'Navoiy viloyati': { x: 450, y: 190, label: 'Навои', short: 'НАВ' },
  'Samarqand viloyati': { x: 540, y: 295, label: 'Самарканд', short: 'САМ' },
  'Qashqadaryo viloyati': { x: 540, y: 375, label: 'Карши / Кашкадарья', short: 'КАШ' },
  'Surxondaryo viloyati': { x: 620, y: 410, label: 'Термез / Сурхандарья', short: 'СУР' },
  'Jizzax viloyati': { x: 615, y: 255, label: 'Джизак', short: 'ДЖИ' },
  'Sirdaryo viloyati': { x: 685, y: 235, label: 'Гулистан / Сырдарья', short: 'СЫР' },
  'Toshkent viloyati': { x: 745, y: 185, label: 'Ташкентская обл.', short: 'ТАШ.ОБЛ' },
  'Toshkent shahri': { x: 760, y: 160, label: 'г. Ташкент (Столица)', short: 'ТАШКЕНТ', isCapital: true },
  'Namangan viloyati': { x: 835, y: 175, label: 'Наманган', short: 'НАМ' },
  'Farg‘ona viloyati': { x: 830, y: 245, label: 'Фергана', short: 'ФЕР' },
  'Andijon viloyati': { x: 890, y: 205, label: 'Андижан', short: 'АНД' },
};

export default function UzbekistanMap({ year = 2026, onSelectRegion, selectedRegion }) {
  const [is3D, setIs3D] = useState(true);
  const [tradeFlows, setTradeFlows] = useState([]);
  const [regionsData, setRegionsData] = useState({});
  const [hoveredRegion, setHoveredRegion] = useState(null);
  const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 });
  const [activeArc, setActiveArc] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch trade flows and regional stats
  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const [flowsRes, regionsRes] = await Promise.all([
          fetch(`/api/analytics/trade-flows?year=${year}&limit=20`),
          fetch(`/api/analytics/regions?year=${year}`)
        ]);

        if (flowsRes.ok && regionsRes.ok) {
          const flows = await flowsRes.json();
          const regions = await regionsRes.json();
          if (isMounted) {
            setTradeFlows(flows);
            const map = {};
            regions.forEach(r => {
              map[r.region] = r;
            });
            setRegionsData(map);
          }
        }
      } catch (err) {
        console.error('Failed to fetch map data', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, [year]);

  const togglePerspective = () => {
    soundEffects.playToggle();
    setIs3D(!is3D);
  };

  return (
    <div className="relative w-full rounded-2xl bg-[#090E09] border border-[#203220] overflow-hidden select-none p-4 shadow-2xl">
      {/* Background Matrix Grid Pattern */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: `
            radial-gradient(#C8EA4A 1px, transparent 1px),
            linear-gradient(to right, rgba(200, 234, 74, 0.05) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(200, 234, 74, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px',
        }}
      />

      {/* Top HUD Control Bar */}
      <div className="relative z-20 flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#1b2b1b]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#121c12] border border-[#283f28] text-xs font-mono text-[#C8EA4A]">
            <span className="w-2 h-2 rounded-full bg-[#C8EA4A] animate-ping" />
            <span>UZ / 41°18' N 69°14' E</span>
          </div>
          <span className="text-xs font-mono text-[#7e997a] tracking-wider uppercase hidden sm:inline">
            14 РЕГИОНОВ • ПОТОКИ СПОТ-СДЕЛОК ({year})
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={togglePerspective}
            className={`px-3 py-1 rounded text-xs font-mono transition-all flex items-center gap-1.5 ${
              is3D 
                ? 'bg-[#C8EA4A] text-[#090E09] font-bold shadow-lg shadow-[#C8EA4A]/20' 
                : 'bg-[#152215] text-[#A6C49F] hover:bg-[#1f321f]'
            }`}
          >
            <span>{is3D ? '3D РАКУРС' : '2D СХЕМА'}</span>
            <span className="text-[10px] opacity-75">{is3D ? 'ISOMETRIC' : 'FLAT'}</span>
          </button>
        </div>
      </div>

      {/* Interactive Map Canvas Container */}
      <div 
        className="relative w-full h-[380px] sm:h-[460px] flex items-center justify-center transition-all duration-700 ease-out"
        style={{
          perspective: '1200px',
        }}
      >
        <div 
          className="relative w-full h-full max-w-[960px] transition-transform duration-700 ease-out origin-center"
          style={{
            transform: is3D 
              ? 'rotateX(36deg) rotateZ(-4deg) translateY(20px) scale(0.92)' 
              : 'rotateX(0deg) rotateZ(0deg) translateY(0) scale(1)',
            transformStyle: 'preserve-3d',
          }}
        >
          {/* Subtle Isometric Base Shadow for 3D depth */}
          {is3D && (
            <div 
              className="absolute inset-0 bg-[#050805]/80 rounded-3xl blur-2xl -z-10"
              style={{ transform: 'translateZ(-40px) translateY(30px)' }}
            />
          )}

          <svg
            viewBox="0 0 980 500"
            className="w-full h-full overflow-visible"
            style={{ filter: 'drop-shadow(0 20px 30px rgba(0,0,0,0.8))' }}
          >
            <defs>
              {/* Gradients */}
              <linearGradient id="arcGlow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#C8EA4A" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#70FFC2" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#C8EA4A" stopOpacity="0.4" />
              </linearGradient>

              <filter id="glowEffect" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Stylized Uzbekistan Territory Outline Boundary */}
            <path
              d="M 120 180 Q 200 120 300 150 Q 380 140 450 160 Q 560 140 680 180 Q 750 140 820 150 Q 920 170 930 220 Q 920 280 840 270 Q 760 260 720 280 Q 660 360 630 430 Q 580 430 520 360 Q 460 350 400 300 Q 330 270 280 270 Q 180 260 140 220 Z"
              fill="#0E170E"
              stroke="#213821"
              strokeWidth="1.5"
              strokeDasharray="4 4"
              opacity="0.6"
            />

            {/* Animated Trade Arcs */}
            {tradeFlows.map((flow, index) => {
              const from = REGIONS_COORDINATES[flow.from_region];
              const to = REGIONS_COORDINATES[flow.to_region];
              if (!from || !to) return null;

              // Arc mid-point with upward curve for 3D elevation
              const midX = (from.x + to.x) / 2;
              const midY = (from.y + to.y) / 2 - Math.min(80, Math.hypot(to.x - from.x, to.y - from.y) * 0.35);

              const isHighlighted = activeArc === index || 
                (hoveredRegion && (hoveredRegion === flow.from_region || hoveredRegion === flow.to_region));

              return (
                <g key={`flow-${index}`} className="transition-all duration-300">
                  {/* Glowing Arc Path */}
                  <path
                    d={`M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`}
                    fill="none"
                    stroke={isHighlighted ? "#C8EA4A" : "rgba(200, 234, 74, 0.22)"}
                    strokeWidth={isHighlighted ? 2.5 : 1.2}
                    filter={isHighlighted ? "url(#glowEffect)" : undefined}
                    className="transition-all duration-200"
                  />

                  {/* Flow Particle */}
                  <circle r={isHighlighted ? "3.5" : "2"} fill="#C8EA4A">
                    <animateMotion
                      path={`M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`}
                      dur={`${2.2 + (index % 4) * 0.7}s`}
                      repeatCount="indefinite"
                    />
                  </circle>
                </g>
              );
            })}

            {/* Region Node Dots & Pulse Rings */}
            {Object.entries(REGIONS_COORDINATES).map(([regName, coords]) => {
              const regData = regionsData[regName];
              const isHovered = hoveredRegion === regName;
              const isSelected = selectedRegion === regName;
              const dealsCount = regData?.deals_count || 0;

              return (
                <g
                  key={regName}
                  transform={`translate(${coords.x}, ${coords.y})`}
                  className="cursor-pointer group"
                  onMouseEnter={(e) => {
                    soundEffects.playClick();
                    setHoveredRegion(regName);
                  }}
                  onMouseLeave={() => setHoveredRegion(null)}
                  onClick={() => {
                    soundEffects.playClick();
                    if (onSelectRegion) onSelectRegion(regName);
                  }}
                >
                  {/* Concentric Pulse Ring for Capital / Major Hubs */}
                  {(coords.isCapital || dealsCount > 7000) && (
                    <circle
                      r="16"
                      fill="none"
                      stroke="#C8EA4A"
                      strokeWidth="1"
                      opacity="0.3"
                      className="animate-ping"
                    />
                  )}

                  {/* Outer aura on hover */}
                  <circle
                    r={isHovered ? "14" : "9"}
                    fill={isHovered ? "rgba(200, 234, 74, 0.25)" : "rgba(35, 55, 35, 0.6)"}
                    stroke={isHovered ? "#C8EA4A" : "#3e5c3e"}
                    strokeWidth={coords.isCapital ? 2 : 1}
                    className="transition-all duration-200"
                  />

                  {/* Center Core Dot */}
                  <circle
                    r={coords.isCapital ? "4.5" : "3.5"}
                    fill={coords.isCapital ? "#FFFFFF" : (isHovered ? "#C8EA4A" : "#A7CA60")}
                    filter="url(#glowEffect)"
                  />

                  {/* Region Code Tag */}
                  <text
                    y="-12"
                    textAnchor="middle"
                    fill={isHovered || isSelected ? "#C8EA4A" : "#7F967B"}
                    fontSize="10"
                    fontFamily="monospace"
                    fontWeight={coords.isCapital || isHovered ? "bold" : "normal"}
                    className="pointer-events-none select-none"
                  >
                    {coords.short}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Dynamic Holographic Region Tooltip */}
        {hoveredRegion && (
          <div className="absolute top-4 right-4 z-30 w-72 bg-[#0F170F]/95 backdrop-blur-md border border-[#C8EA4A]/40 rounded-xl p-3.5 shadow-2xl text-left pointer-events-none animate-fadeIn">
            <div className="flex items-center justify-between border-b border-[#243824] pb-2 mb-2">
              <span className="text-[11px] font-mono text-[#C8EA4A] tracking-wider uppercase font-bold">
                {REGIONS_COORDINATES[hoveredRegion]?.label || hoveredRegion}
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1c2c1c] text-[#8ea88a]">
                {year}
              </span>
            </div>

            <div className="space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-[#8ea88a]">
                <span>Сделок зарегистрировано:</span>
                <span className="text-white font-bold">
                  {regionsData[hoveredRegion]?.deals_count?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex justify-between text-[#8ea88a]">
                <span>Оборот региона:</span>
                <span className="text-[#C8EA4A] font-bold">
                  {regionsData[hoveredRegion]?.amount_mlrd ? `${regionsData[hoveredRegion]?.amount_mlrd.toLocaleString()} млрд` : '—'}
                </span>
              </div>
              <div className="flex justify-between text-[#8ea88a] pt-1 border-t border-[#1a2b1a]">
                <span>Ведущий товар:</span>
                <span className="text-white truncate max-w-[140px]" title={regionsData[hoveredRegion]?.top_commodity}>
                  {regionsData[hoveredRegion]?.top_commodity || '—'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Live Trade Routes Ticker */}
      <div className="relative z-20 mt-2 pt-2 border-t border-[#1b2b1b] flex flex-wrap items-center justify-between text-[11px] font-mono text-[#7b9777]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#C8EA4A]" />
          <span>ТОП МЕЖРЕГИОНАЛЬНЫЙ МАРШРУТ:</span>
          {tradeFlows[0] && (
            <span className="text-[#C8EA4A]">
              {tradeFlows[0].from_region} → {tradeFlows[0].to_region} ({tradeFlows[0].deals_count.toLocaleString()} сделок, {tradeFlows[0].amount_mlrd} млрд)
            </span>
          )}
        </div>
        <div className="text-[10px] text-[#556952]">
          Нажмите на узел для фильтрации данных
        </div>
      </div>
    </div>
  );
}
