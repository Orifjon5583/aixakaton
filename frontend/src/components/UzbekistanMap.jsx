import React, { useState, useEffect, useRef } from 'react';
import { soundEffects } from './SoundEffects';

// Mathematically calibrated GPS coordinates for Uzbekistan's 14 regions
// Screen coordinate space: 1000 x 540 (Horizontal East-West layout)
const REGIONS_COORDINATES = {
  'Qoraqalpog‘iston Respublikasi': { x: 230, y: 175, label: 'Нукус / Қорақалпоғистон', short: 'ККР' },
  'Xorazm viloyati': { x: 300, y: 245, label: 'Урганч / Хоразм', short: 'ХОР' },
  'Buxoro viloyati': { x: 480, y: 330, label: 'Бухоро вилояти', short: 'БУХ' },
  'Navoiy viloyati': { x: 530, y: 270, label: 'Навоий вилояти', short: 'НАВ' },
  'Samarqand viloyati': { x: 615, y: 335, label: 'Самарқанд вилояти', short: 'САМ' },
  'Qashqadaryo viloyati': { x: 565, y: 385, label: 'Қарши / Қашқадарё', short: 'ҚАШ' },
  'Surxondaryo viloyati': { x: 645, y: 465, label: 'Термиз / Сурхондарё', short: 'СУР' },
  'Jizzax viloyati': { x: 665, y: 310, label: 'Жиззах вилояти', short: 'ЖИЗ' },
  'Sirdaryo viloyati': { x: 710, y: 290, label: 'Гулистон / Сирдарё', short: 'СИР' },
  'Toshkent viloyati': { x: 745, y: 245, label: 'Тошкент вилояти', short: 'ТАШ.В' },
  'Toshkent shahri': { x: 755, y: 225, label: 'Тошкент шаҳри (Пойтахт)', short: 'ТОШКЕНТ', isCapital: true },
  'Namangan viloyati': { x: 845, y: 245, label: 'Наманган вилояти', short: 'НАМ' },
  'Farg‘ona viloyati': { x: 855, y: 295, label: 'Фарғона вилояти', short: 'ФАР' },
  'Andijon viloyati': { x: 895, y: 270, label: 'Андижон вилояти', short: 'АНД' },
};

// Geographically accurate boundary polygon of Uzbekistan (Horizontal 1000x540)
const UZBEKISTAN_BORDER_PATH = `
  M 75 80
  C 120 75, 200 65, 270 70
  C 320 75, 360 90, 420 120
  C 480 150, 540 180, 600 200
  C 640 210, 680 180, 715 150
  C 740 130, 765 140, 785 160
  C 810 185, 835 220, 860 210
  C 890 200, 920 230, 935 265
  C 945 290, 930 310, 905 320
  C 870 335, 840 330, 810 310
  C 785 295, 765 285, 740 280
  C 715 280, 690 310, 675 330
  C 660 350, 660 390, 665 435
  C 670 470, 650 500, 630 495
  C 605 485, 590 445, 570 415
  C 550 395, 510 380, 465 375
  C 420 370, 375 350, 335 325
  C 295 305, 265 300, 240 285
  C 200 260, 160 245, 120 230
  C 85 215, 70 170, 68 125
  Z
`;

export default function UzbekistanMap({ year = 2026, onSelectRegion, selectedRegion }) {
  const [is3D, setIs3D] = useState(true);
  const [isAutoTilting, setIsAutoTilting] = useState(true);
  const [tiltX, setTiltX] = useState(45); // X-axis tilt (pitch) in degrees
  const [tradeFlows, setTradeFlows] = useState([]);
  const [regionsData, setRegionsData] = useState({});
  const [hoveredRegion, setHoveredRegion] = useState(null);
  const [activeArc, setActiveArc] = useState(null);

  // Drag interaction state
  const isDragging = useRef(false);
  const startY = useRef(0);
  const startTilt = useRef(45);
  const animFrameId = useRef(null);
  const tiltTimer = useRef(0);

  // Fetch trade flows and regional stats
  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        const [flowsRes, regionsRes] = await Promise.all([
          fetch(`/api/analytics/trade-flows?year=${year}&limit=25`),
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
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, [year]);

  // Smooth continuous rotation/tilting along the X-AXIS (Pitch oscillation)
  useEffect(() => {
    const loop = () => {
      if (isAutoTilting && !isDragging.current && is3D) {
        tiltTimer.current += 0.025;
        // Smooth sine wave between 28° and 56° along the X-AXIS
        const newTilt = 42 + 14 * Math.sin(tiltTimer.current);
        setTiltX(newTilt);
      }
      animFrameId.current = requestAnimationFrame(loop);
    };

    animFrameId.current = requestAnimationFrame(loop);
    return () => {
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [isAutoTilting, is3D]);

  // Mouse / Touch Drag to Tilt along X-AXIS
  const handleMouseDown = (e) => {
    if (!is3D) return;
    isDragging.current = true;
    startY.current = e.clientY || (e.touches && e.touches[0].clientY) || 0;
    startTilt.current = tiltX;
  };

  const handleMouseMove = (e) => {
    if (!isDragging.current || !is3D) return;
    const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
    const deltaY = (startY.current - clientY) * 0.4;
    // Clamp tilt between 15° and 65°
    const clamped = Math.max(15, Math.min(65, startTilt.current + deltaY));
    setTiltX(clamped);
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const toggleAutoTilt = () => {
    soundEffects.playToggle();
    setIsAutoTilting(!isAutoTilting);
  };

  const togglePerspective = () => {
    soundEffects.playToggle();
    setIs3D(!is3D);
  };

  const resetTilt = (val = 45) => {
    soundEffects.playClick();
    setTiltX(val);
  };

  return (
    <div 
      className="relative w-full rounded-2xl bg-[#080D08] border border-[#203220] overflow-hidden select-none p-4 shadow-2xl"
      onMouseMove={handleMouseMove}
      onTouchMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onTouchEnd={handleMouseUp}
    >
      {/* Background Matrix Grid */}
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
            3D ОБСЕРВАТОРИЯ СПОТ-СДЕЛОК ({year})
          </span>
        </div>

        {/* View & Tilt Controls */}
        <div className="flex items-center gap-2">
          {/* Auto-Tilt along X Axis */}
          <button
            onClick={toggleAutoTilt}
            className={`px-3 py-1 rounded text-xs font-mono transition-all flex items-center gap-1.5 ${
              isAutoTilting
                ? 'bg-[#182a18] border border-[#C8EA4A]/50 text-[#C8EA4A]'
                : 'bg-[#121c12] border border-[#263a26] text-[#6e886b]'
            }`}
            title="Автоматическое 3D-колебание по оси X"
          >
            <span>{isAutoTilting ? '🔄 НАКЛОН X: ВКЛ' : 'НАКЛОН X: ПАУЗА'}</span>
          </button>

          {/* Perspective Switcher */}
          <button
            onClick={togglePerspective}
            className={`px-3 py-1 rounded text-xs font-mono transition-all flex items-center gap-1.5 ${
              is3D 
                ? 'bg-[#C8EA4A] text-[#090E09] font-bold shadow-lg shadow-[#C8EA4A]/20' 
                : 'bg-[#152215] text-[#A6C49F] hover:bg-[#1f321f]'
            }`}
          >
            <span>{is3D ? '3D РАКУРС' : '2D СХЕМА'}</span>
          </button>

          {is3D && (
            <button
              onClick={() => resetTilt(45)}
              className="p-1 px-2.5 rounded text-[11px] font-mono bg-[#111c11] text-[#708c6d] hover:text-white border border-[#203220]"
              title="Сброс на 45°"
            >
              45°
            </button>
          )}
        </div>
      </div>

      {/* 3D Isometric View Stage */}
      <div 
        className="relative w-full h-[380px] sm:h-[460px] flex items-center justify-center cursor-ns-resize overflow-hidden"
        style={{
          perspective: '1100px',
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleMouseDown}
      >
        {/* Holographic Island Container - ROTATES ONLY ALONG X-AXIS (No side flipping!) */}
        <div 
          className="relative w-full h-full max-w-[960px] flex items-center justify-center origin-center"
          style={{
            transform: is3D 
              ? `rotateX(${tiltX}deg) translateY(${tiltX * 0.4}px) scale(0.96)` 
              : 'rotateX(0deg) translateY(0) scale(1)',
            transformStyle: 'preserve-3d',
            transition: isDragging.current ? 'none' : 'transform 0.15s ease-out',
          }}
        >
          {/* Subtle Base Shadow Layer for 3D Volume */}
          {is3D && (
            <div 
              className="absolute inset-0 bg-[#040804]/90 rounded-3xl blur-2xl -z-20"
              style={{ transform: 'translateZ(-40px) translateY(35px)' }}
            />
          )}

          {/* SVG Map of Uzbekistan */}
          <svg
            viewBox="0 0 1000 540"
            className="w-full h-full overflow-visible"
            style={{ 
              filter: 'drop-shadow(0 20px 30px rgba(0,0,0,0.85))',
              transformStyle: 'preserve-3d',
            }}
          >
            <defs>
              <linearGradient id="uzTerritoryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#132213" stopOpacity="0.95" />
                <stop offset="60%" stopColor="#0E1A0E" stopOpacity="0.95" />
                <stop offset="100%" stopColor="#081008" stopOpacity="0.95" />
              </linearGradient>

              <filter id="uzGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="3.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* 3D Extrusion Layer (Thick base edge) */}
            {is3D && (
              <path
                d={UZBEKISTAN_BORDER_PATH}
                fill="#070D07"
                stroke="#1B2F1B"
                strokeWidth="3"
                transform="translate(0, 14)"
                opacity="0.85"
              />
            )}

            {/* Main Accurate Geographic Contour */}
            <path
              d={UZBEKISTAN_BORDER_PATH}
              fill="url(#uzTerritoryGrad)"
              stroke="#C8EA4A"
              strokeWidth="2.2"
              filter="url(#uzGlow)"
              className="transition-all duration-300"
            />

            {/* Regional Topography Guides (subtle relief curves) */}
            <g opacity="0.2" stroke="#C8EA4A" strokeWidth="1" fill="none">
              <path d="M 120 180 Q 230 150 340 210 Q 450 260 550 230" />
              <path d="M 310 270 Q 420 330 520 280 Q 620 320 720 250" />
              <path d="M 490 340 Q 570 410 650 450" />
              <path d="M 660 290 Q 750 240 850 240 Q 900 260 925 250" />
            </g>

            {/* Animated Trade Arcs between Regions */}
            {tradeFlows.map((flow, index) => {
              const from = REGIONS_COORDINATES[flow.from_region];
              const to = REGIONS_COORDINATES[flow.to_region];
              if (!from || !to) return null;

              // Arc mid-point with high 3D curved elevation
              const midX = (from.x + to.x) / 2;
              const midY = (from.y + to.y) / 2 - Math.min(95, Math.hypot(to.x - from.x, to.y - from.y) * 0.38);

              const isHighlighted = activeArc === index || 
                (hoveredRegion && (hoveredRegion === flow.from_region || hoveredRegion === flow.to_region));

              return (
                <g key={`flow-${index}`} className="transition-all duration-300">
                  {/* Glowing Arc Curve */}
                  <path
                    d={`M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`}
                    fill="none"
                    stroke={isHighlighted ? "#C8EA4A" : "rgba(200, 234, 74, 0.3)"}
                    strokeWidth={isHighlighted ? 2.8 : 1.4}
                    strokeLinecap="round"
                  />

                  {/* Flow Particle */}
                  <circle r={isHighlighted ? "4" : "2.2"} fill="#C8EA4A">
                    <animateMotion
                      path={`M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`}
                      dur={`${2.0 + (index % 5) * 0.5}s`}
                      repeatCount="indefinite"
                    />
                  </circle>
                </g>
              );
            })}

            {/* Region Node Hubs */}
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
                  onMouseEnter={() => {
                    soundEffects.playClick();
                    setHoveredRegion(regName);
                  }}
                  onMouseLeave={() => setHoveredRegion(null)}
                  onClick={(e) => {
                    e.stopPropagation();
                    soundEffects.playClick();
                    if (onSelectRegion) onSelectRegion(regName);
                  }}
                >
                  {/* Pulsing Radar Ring on Capital and Major Hubs */}
                  {(coords.isCapital || dealsCount > 7000) && (
                    <circle
                      r="18"
                      fill="none"
                      stroke="#C8EA4A"
                      strokeWidth="1.2"
                      opacity="0.3"
                      className="animate-ping"
                    />
                  )}

                  {/* Outer Orbit Halo */}
                  <circle
                    r={isHovered ? "15" : (coords.isCapital ? "11" : "8")}
                    fill={isHovered ? "rgba(200, 234, 74, 0.35)" : "rgba(25, 45, 25, 0.7)"}
                    stroke={isHovered || coords.isCapital ? "#C8EA4A" : "#3e633e"}
                    strokeWidth={coords.isCapital ? 2.5 : 1.2}
                    className="transition-all duration-200"
                  />

                  {/* Center Dot */}
                  <circle
                    r={coords.isCapital ? "5" : "3.5"}
                    fill={coords.isCapital ? "#FFFFFF" : (isHovered ? "#C8EA4A" : "#B2D858")}
                  />

                  {/* Region Code Tag */}
                  <text
                    y="-13"
                    textAnchor="middle"
                    fill={isHovered || isSelected ? "#C8EA4A" : "#8AA885"}
                    fontSize={coords.isCapital ? "11" : "10"}
                    fontFamily="monospace"
                    fontWeight={coords.isCapital || isHovered ? "bold" : "normal"}
                    className="pointer-events-none select-none drop-shadow-md"
                  >
                    {coords.short}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Dynamic Telemetry Tooltip when Hovering a Region */}
        {hoveredRegion && (
          <div className="absolute top-4 right-4 z-30 w-72 bg-[#0C140C]/95 backdrop-blur-md border border-[#C8EA4A]/50 rounded-xl p-3.5 shadow-2xl text-left pointer-events-none animate-fadeIn">
            <div className="flex items-center justify-between border-b border-[#243824] pb-2 mb-2">
              <span className="text-[11px] font-mono text-[#C8EA4A] tracking-wider uppercase font-bold">
                {REGIONS_COORDINATES[hoveredRegion]?.label || hoveredRegion}
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#182718] text-[#8ea88a]">
                {year}
              </span>
            </div>

            <div className="space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-[#8ea88a]">
                <span>Сделок:</span>
                <span className="text-white font-bold">
                  {regionsData[hoveredRegion]?.deals_count?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex justify-between text-[#8ea88a]">
                <span>Оборот:</span>
                <span className="text-[#C8EA4A] font-bold">
                  {regionsData[hoveredRegion]?.amount_mlrd ? `${regionsData[hoveredRegion]?.amount_mlrd.toLocaleString()} млрд` : '—'}
                </span>
              </div>
              <div className="flex justify-between text-[#8ea88a] pt-1 border-t border-[#1a2b1a]">
                <span>Топ-товар:</span>
                <span className="text-white truncate max-w-[140px]" title={regionsData[hoveredRegion]?.top_commodity}>
                  {regionsData[hoveredRegion]?.top_commodity || '—'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Telemetry Status Bar */}
      <div className="relative z-20 mt-2 pt-2 border-t border-[#1b2b1b] flex flex-wrap items-center justify-between text-[11px] font-mono text-[#7b9777]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#C8EA4A]" />
          <span>3D ПЕРСПЕКТИВА: ОСЬ X</span>
          <span className="text-[#556952] hidden md:inline">| Двигайте мышью вверх/вниз для наклона</span>
        </div>
        <div className="text-[10px] text-[#C8EA4A]">
          НАКЛОН ПО ОСИ X: {Math.round(tiltX)}°
        </div>
      </div>
    </div>
  );
}
