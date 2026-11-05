import React, { useState, useEffect, useRef } from 'react';
import { soundEffects } from './SoundEffects';

// Accurate geographic coordinates for the 14 administrative regions of Uzbekistan
// Scaled to a 1000x550 canvas coordinate space
const REGIONS_COORDINATES = {
  'Qoraqalpog‘iston Respublikasi': { x: 175, y: 175, label: 'Нукус / Қорақалпоғистон', short: 'ККР', depth: 15 },
  'Xorazm viloyati': { x: 285, y: 255, label: 'Урганч / Хоразм', short: 'ХОР', depth: 20 },
  'Navoiy viloyati': { x: 450, y: 220, label: 'Навоий вилояти', short: 'НАВ', depth: 25 },
  'Buxoro viloyati': { x: 410, y: 310, label: 'Бухоро вилояти', short: 'БУХ', depth: 22 },
  'Samarqand viloyati': { x: 540, y: 320, label: 'Самарқанд вилояти', short: 'САМ', depth: 30 },
  'Qashqadaryo viloyati': { x: 535, y: 405, label: 'Қарши / Қашқадарё', short: 'ҚАШ', depth: 26 },
  'Surxondaryo viloyati': { x: 625, y: 465, label: 'Термиз / Сурхондарё', short: 'СУР', depth: 28 },
  'Jizzax viloyati': { x: 615, y: 275, label: 'Жиззах виloyati', short: 'ЖИЗ', depth: 32 },
  'Sirdaryo viloyati': { x: 675, y: 250, label: 'Гулистон / Сирдарё', short: 'СИР', depth: 35 },
  'Toshkent viloyati': { x: 735, y: 200, label: 'Тошкент вилояти', short: 'ТАШ.В', depth: 40 },
  'Toshkent shahri': { x: 750, y: 170, label: 'Тошкент шаҳри (Пойтахт)', short: 'ТОШКЕНТ', isCapital: true, depth: 45 },
  'Namangan viloyati': { x: 825, y: 185, label: 'Наманган вилояти', short: 'НАМ', depth: 42 },
  'Farg‘ona viloyati': { x: 835, y: 255, label: 'Фарғона вилояти', short: 'ФАР', depth: 38 },
  'Andijon viloyati': { x: 895, y: 215, label: 'Андижон вилояти', short: 'АНД', depth: 40 },
};

// Accurate geographic contour of the Republic of Uzbekistan
const UZBEKISTAN_CONTOUR_PATH = `
  M 75 140
  C 110 95, 200 85, 270 95
  C 320 102, 360 120, 395 140
  C 435 125, 490 145, 530 170
  C 570 195, 620 205, 660 185
  C 700 165, 735 140, 770 150
  C 805 160, 850 165, 880 180
  C 920 200, 955 220, 940 250
  C 925 280, 875 295, 835 285
  C 800 275, 780 250, 755 245
  C 730 240, 710 260, 690 270
  C 670 280, 650 320, 650 360
  C 650 400, 655 450, 640 495
  C 625 540, 590 520, 570 475
  C 555 440, 520 430, 480 395
  C 440 360, 390 350, 350 330
  C 310 310, 275 320, 250 305
  C 225 290, 180 280, 140 260
  C 100 240, 65 210, 60 175
  Z
`;

export default function UzbekistanMap({ year = 2026, onSelectRegion, selectedRegion }) {
  const [is3D, setIs3D] = useState(true);
  const [isRotating, setIsRotating] = useState(true);
  const [rotAngle, setRotAngle] = useState(0);
  const [tradeFlows, setTradeFlows] = useState([]);
  const [regionsData, setRegionsData] = useState({});
  const [hoveredRegion, setHoveredRegion] = useState(null);
  const [activeArc, setActiveArc] = useState(null);

  // Drag interaction state
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startRot = useRef(0);
  const animFrameId = useRef(null);

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

  // Continuous smooth 3D rotation loop
  useEffect(() => {
    const rotate = () => {
      if (isRotating && !isDragging.current && is3D) {
        setRotAngle(prev => (prev + 0.35) % 360);
      }
      animFrameId.current = requestAnimationFrame(rotate);
    };

    animFrameId.current = requestAnimationFrame(rotate);
    return () => {
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [isRotating, is3D]);

  // Mouse / Touch drag to spin
  const handleMouseDown = (e) => {
    if (!is3D) return;
    isDragging.current = true;
    startX.current = e.clientX || (e.touches && e.touches[0].clientX) || 0;
    startRot.current = rotAngle;
  };

  const handleMouseMove = (e) => {
    if (!isDragging.current || !is3D) return;
    const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
    const delta = (clientX - startX.current) * 0.6;
    setRotAngle((startRot.current + delta) % 360);
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const toggleRotation = () => {
    soundEffects.playToggle();
    setIsRotating(!isRotating);
  };

  const togglePerspective = () => {
    soundEffects.playToggle();
    setIs3D(!is3D);
  };

  const resetRotation = () => {
    soundEffects.playClick();
    setRotAngle(0);
  };

  return (
    <div 
      className="relative w-full rounded-2xl bg-[#080D08] border border-[#203220] overflow-hidden select-none p-4 shadow-2xl"
      onMouseMove={handleMouseMove}
      onTouchMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onTouchEnd={handleMouseUp}
    >
      {/* Background Matrix Grid Pattern */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-25"
        style={{
          backgroundImage: `
            radial-gradient(#C8EA4A 1.2px, transparent 1.2px),
            linear-gradient(to right, rgba(200, 234, 74, 0.06) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(200, 234, 74, 0.06) 1px, transparent 1px)
          `,
          backgroundSize: '28px 28px',
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

        {/* View & Rotation Controls */}
        <div className="flex items-center gap-2">
          {/* Rotation Toggle Button */}
          <button
            onClick={toggleRotation}
            className={`px-3 py-1 rounded text-xs font-mono transition-all flex items-center gap-1.5 ${
              isRotating
                ? 'bg-[#182a18] border border-[#C8EA4A]/50 text-[#C8EA4A]'
                : 'bg-[#121c12] border border-[#263a26] text-[#6e886b]'
            }`}
            title="Авто-вращение платформы"
          >
            <span className={isRotating ? 'animate-spin text-sm' : 'text-sm'}>🔄</span>
            <span>{isRotating ? 'ВРАЩЕНИЕ: ВКЛ' : 'ПАУЗА'}</span>
          </button>

          {/* 3D / 2D Perspective Toggle */}
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
              onClick={resetRotation}
              className="p-1 px-2 rounded text-[11px] font-mono bg-[#111c11] text-[#708c6d] hover:text-white border border-[#203220]"
              title="Сброс ракурса"
            >
              СБРОС
            </button>
          )}
        </div>
      </div>

      {/* Interactive 3D Turntable Stage Container */}
      <div 
        className="relative w-full h-[380px] sm:h-[480px] flex items-center justify-center cursor-grab active:cursor-grabbing overflow-hidden"
        style={{
          perspective: '1300px',
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleMouseDown}
      >
        {/* Holographic 3D Turntable Island */}
        <div 
          className="relative w-full h-full max-w-[960px] flex items-center justify-center origin-center"
          style={{
            transform: is3D 
              ? `rotateX(42deg) rotateZ(-6deg) rotateY(${rotAngle}deg) scale(0.95)` 
              : 'rotateX(0deg) rotateZ(0deg) rotateY(0deg) scale(1)',
            transformStyle: 'preserve-3d',
            transition: isDragging.current ? 'none' : 'transform 0.1s linear',
          }}
        >
          {/* Ground Reflection Radar Rings */}
          {is3D && (
            <div 
              className="absolute inset-0 flex items-center justify-center pointer-events-none -z-20"
              style={{ transform: 'translateZ(-50px)' }}
            >
              <div className="w-[780px] h-[480px] rounded-full border border-[#C8EA4A]/10 animate-pulse" />
              <div className="absolute w-[620px] h-[360px] rounded-full border border-[#C8EA4A]/15" />
              <div className="absolute w-[440px] h-[240px] rounded-full border border-[#C8EA4A]/20" />
            </div>
          )}

          {/* SVG Map Container */}
          <svg
            viewBox="0 0 1000 550"
            className="w-full h-full overflow-visible"
            style={{ 
              filter: 'drop-shadow(0 25px 35px rgba(0,0,0,0.9))',
              transformStyle: 'preserve-3d',
            }}
          >
            <defs>
              {/* Gradients */}
              <linearGradient id="territoryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#122012" stopOpacity="0.95" />
                <stop offset="50%" stopColor="#0F1B0F" stopOpacity="0.95" />
                <stop offset="100%" stopColor="#0B140B" stopOpacity="0.95" />
              </linearGradient>

              <linearGradient id="baseExtrusion" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#C8EA4A" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#050805" stopOpacity="0.9" />
              </linearGradient>

              <filter id="mapGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Layer 1: 3D Deep Base Shadow (gives thick island volume) */}
            {is3D && (
              <path
                d={UZBEKISTAN_CONTOUR_PATH}
                fill="#050905"
                stroke="#162616"
                strokeWidth="4"
                transform="translate(0, 22)"
                opacity="0.8"
              />
            )}

            {/* Layer 2: Middle Extrusion Shelf */}
            {is3D && (
              <path
                d={UZBEKISTAN_CONTOUR_PATH}
                fill="#0C170C"
                stroke="#2a452a"
                strokeWidth="2"
                transform="translate(0, 10)"
                opacity="0.9"
              />
            )}

            {/* Layer 3: Realistic Geographic Uzbekistan Territory Surface */}
            <path
              d={UZBEKISTAN_CONTOUR_PATH}
              fill="url(#territoryGrad)"
              stroke="#C8EA4A"
              strokeWidth="2"
              strokeDasharray={is3D ? "none" : "none"}
              filter="url(#mapGlow)"
              className="transition-all duration-300"
            />

            {/* Interior Regional Topography Arcs (Topographical relief lines) */}
            <g opacity="0.18" stroke="#C8EA4A" strokeWidth="1" fill="none">
              <path d="M 120 180 Q 220 140 330 200 Q 420 250 510 220" />
              <path d="M 280 270 Q 380 320 480 270 Q 580 310 680 240" />
              <path d="M 440 330 Q 530 400 620 440" />
              <path d="M 640 280 Q 730 220 840 220 Q 890 240 920 230" />
            </g>

            {/* Dynamic Animated Trade Arcs between Regions */}
            {tradeFlows.map((flow, index) => {
              const from = REGIONS_COORDINATES[flow.from_region];
              const to = REGIONS_COORDINATES[flow.to_region];
              if (!from || !to) return null;

              // Arc mid-point with high elevation curve
              const midX = (from.x + to.x) / 2;
              const midY = (from.y + to.y) / 2 - Math.min(100, Math.hypot(to.x - from.x, to.y - from.y) * 0.4);

              const isHighlighted = activeArc === index || 
                (hoveredRegion && (hoveredRegion === flow.from_region || hoveredRegion === flow.to_region));

              return (
                <g key={`flow-${index}`} className="transition-all duration-300">
                  {/* Arc Curve */}
                  <path
                    d={`M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`}
                    fill="none"
                    stroke={isHighlighted ? "#C8EA4A" : "rgba(200, 234, 74, 0.28)"}
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

            {/* Region Node Hubs (Cities / Regional Capitals) */}
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
                  {/* Capital / Major Hub Radiant Radar Pulsing Waves */}
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

                  {/* Center Node Core */}
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
          <span>3D ГЕОМЕТРИЯ: РЕСПУБЛИКА УЗБЕКИСТАН</span>
          <span className="text-[#556952] hidden md:inline">| Вращайте мышью или пальцем</span>
        </div>
        <div className="text-[10px] text-[#C8EA4A]">
          УГОЛ ОБЗОРА: {Math.round(rotAngle)}°
        </div>
      </div>
    </div>
  );
}
