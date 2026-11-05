import React, { useState, useEffect, useRef } from 'react';
import { soundEffects } from './SoundEffects';
import { UZBEKISTAN_REGIONS, UZBEKISTAN_OUTER_BORDER } from './uzbekistanMapData';

export default function UzbekistanMap({ year = 2026, onSelectRegion, selectedRegion }) {
  const [is3D, setIs3D] = useState(true);
  const [isRotatingY, setIsRotatingY] = useState(true);
  const [rotY, setRotY] = useState(0); // Y-axis rotation in degrees (0 to 360°)
  const [tradeFlows, setTradeFlows] = useState([]);
  const [regionsData, setRegionsData] = useState({});
  const [hoveredRegion, setHoveredRegion] = useState(null);
  const [activeArc, setActiveArc] = useState(null);

  // Drag interaction state
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startRotY = useRef(0);
  const animFrameId = useRef(null);

  // Quick lookup dictionary for regions coordinates
  const coordsMap = useRef({});
  useEffect(() => {
    const map = {};
    UZBEKISTAN_REGIONS.forEach(r => {
      map[r.id] = { x: r.cx, y: r.cy };
    });
    coordsMap.current = map;
  }, []);

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

  // Smooth continuous 360-DEGREE rotation along the Y-AXIS
  useEffect(() => {
    const loop = () => {
      if (isRotatingY && !isDragging.current && is3D) {
        setRotY(prev => (prev + 0.35) % 360);
      }
      animFrameId.current = requestAnimationFrame(loop);
    };

    animFrameId.current = requestAnimationFrame(loop);
    return () => {
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [isRotatingY, is3D]);

  // Mouse / Touch Drag to Spin along Y-AXIS
  const handleMouseDown = (e) => {
    if (!is3D) return;
    isDragging.current = true;
    startX.current = e.clientX || (e.touches && e.touches[0].clientX) || 0;
    startRotY.current = rotY;
  };

  const handleMouseMove = (e) => {
    if (!isDragging.current || !is3D) return;
    const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
    const deltaX = (clientX - startX.current) * 0.5;
    setRotY((startRotY.current + deltaX + 3600) % 360);
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const toggleRotation = () => {
    soundEffects.playToggle();
    setIsRotatingY(!isRotatingY);
  };

  const togglePerspective = () => {
    soundEffects.playToggle();
    setIs3D(!is3D);
  };

  const resetRotation = () => {
    soundEffects.playClick();
    setRotY(0);
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
            360° ВРАЩЕНИЕ ПО ОСИ Y • 14 РЕГИОНОВ ({year})
          </span>
        </div>

        {/* View & Rotation Controls */}
        <div className="flex items-center gap-2">
          {/* 360° Rotation Toggle along Y Axis */}
          <button
            onClick={toggleRotation}
            className={`px-3 py-1 rounded text-xs font-mono transition-all flex items-center gap-1.5 ${
              isRotatingY
                ? 'bg-[#182a18] border border-[#C8EA4A]/50 text-[#C8EA4A]'
                : 'bg-[#121c12] border border-[#263a26] text-[#6e886b]'
            }`}
            title="Автоматическое 360-градусное вращение по оси Y"
          >
            <span className={isRotatingY ? 'animate-spin text-sm' : 'text-sm'}>🔄</span>
            <span>{isRotatingY ? 'ВРАЩЕНИЕ 360°: ВКЛ' : 'ПАУЗА'}</span>
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
              onClick={resetRotation}
              className="p-1 px-2.5 rounded text-[11px] font-mono bg-[#111c11] text-[#708c6d] hover:text-white border border-[#203220]"
              title="Сброс на 0°"
            >
              СБРОС 0°
            </button>
          )}
        </div>
      </div>

      {/* 3D Turntable Stage Container */}
      <div 
        className="relative w-full h-[380px] sm:h-[480px] flex items-center justify-center cursor-ew-resize overflow-hidden"
        style={{
          perspective: '1300px',
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleMouseDown}
      >
        {/* Holographic Island Stage - ROTATES 360° AROUND Y-AXIS */}
        <div 
          className="relative w-full h-full max-w-[960px] flex items-center justify-center origin-center"
          style={{
            transform: is3D 
              ? `rotateX(28deg) rotateY(${rotY}deg) scale(0.95)` 
              : 'rotateX(0deg) rotateY(0deg) scale(1)',
            transformStyle: 'preserve-3d',
            transition: isDragging.current ? 'none' : 'transform 0.08s linear',
          }}
        >
          {/* Ground Circular Radar Turntable Base */}
          {is3D && (
            <div 
              className="absolute inset-0 flex items-center justify-center pointer-events-none -z-20"
              style={{ transform: 'translateZ(-45px)' }}
            >
              <div className="w-[780px] h-[460px] rounded-full border border-[#C8EA4A]/10 animate-pulse" />
              <div className="absolute w-[620px] h-[360px] rounded-full border border-[#C8EA4A]/15" />
              <div className="absolute w-[440px] h-[250px] rounded-full border border-[#C8EA4A]/20" />
            </div>
          )}

          {/* SVG Map of Uzbekistan with 14 regions and 3D extrusion */}
          <svg
            viewBox="0 0 1000 550"
            className="w-full h-full overflow-visible"
            style={{ 
              filter: 'drop-shadow(0 25px 35px rgba(0,0,0,0.9))',
              transformStyle: 'preserve-3d',
            }}
          >
            <defs>
              <linearGradient id="regionFill" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#142414" stopOpacity="0.96" />
                <stop offset="100%" stopColor="#0B150B" stopOpacity="0.96" />
              </linearGradient>

              <filter id="uzGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* 3D Depth Extrusion Slabs (Layer 1, 2, 3) for thick volume while rotating */}
            {is3D && (
              <>
                <path
                  d={UZBEKISTAN_OUTER_BORDER}
                  fill="#050A05"
                  stroke="#122412"
                  strokeWidth="4"
                  transform="translate(0, 24)"
                  opacity="0.8"
                />
                <path
                  d={UZBEKISTAN_OUTER_BORDER}
                  fill="#091309"
                  stroke="#1B331B"
                  strokeWidth="3"
                  transform="translate(0, 16)"
                  opacity="0.85"
                />
                <path
                  d={UZBEKISTAN_OUTER_BORDER}
                  fill="#0D1A0D"
                  stroke="#264526"
                  strokeWidth="2"
                  transform="translate(0, 8)"
                  opacity="0.9"
                />
              </>
            )}

            {/* All 14 Administrative Regions (Official GADM vector polygons) */}
            <g className="transition-all duration-300">
              {UZBEKISTAN_REGIONS.map((reg) => {
                const isHovered = hoveredRegion === reg.id;
                const isSelected = selectedRegion === reg.id;

                return (
                  <path
                    key={reg.id}
                    d={reg.path}
                    fill={isHovered ? "#234023" : (isSelected ? "#1C331C" : "url(#regionFill)")}
                    stroke={isHovered ? "#C8EA4A" : "#2E4E2E"}
                    strokeWidth={isHovered ? "2.2" : "1.2"}
                    className="cursor-pointer transition-colors duration-200"
                    onMouseEnter={() => {
                      soundEffects.playClick();
                      setHoveredRegion(reg.id);
                    }}
                    onMouseLeave={() => setHoveredRegion(null)}
                    onClick={() => {
                      soundEffects.playClick();
                      if (onSelectRegion) onSelectRegion(reg.id);
                    }}
                  />
                );
              })}
            </g>

            {/* Country Outer Border Glow Line */}
            <path
              d={UZBEKISTAN_OUTER_BORDER}
              fill="none"
              stroke="#C8EA4A"
              strokeWidth="2.2"
              filter="url(#uzGlow)"
              className="pointer-events-none"
            />

            {/* Animated 3D Trade Arcs */}
            {tradeFlows.map((flow, index) => {
              const from = coordsMap.current[flow.from_region];
              const to = coordsMap.current[flow.to_region];
              if (!from || !to) return null;

              // Arc mid-point with high 3D curved elevation
              const midX = (from.x + to.x) / 2;
              const midY = (from.y + to.y) / 2 - Math.min(95, Math.hypot(to.x - from.x, to.y - from.y) * 0.38);

              const isHighlighted = activeArc === index || 
                (hoveredRegion && (hoveredRegion === flow.from_region || hoveredRegion === flow.to_region));

              return (
                <g key={`flow-${index}`} className="transition-all duration-300 pointer-events-none">
                  {/* Glowing Arc Path */}
                  <path
                    d={`M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`}
                    fill="none"
                    stroke={isHighlighted ? "#C8EA4A" : "rgba(200, 234, 74, 0.35)"}
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

            {/* Region Node Hubs with 3D Billboard Counter-Rotation */}
            {UZBEKISTAN_REGIONS.map((reg) => {
              const regData = regionsData[reg.id];
              const isHovered = hoveredRegion === reg.id;
              const isSelected = selectedRegion === reg.id;
              const dealsCount = regData?.deals_count || 0;

              return (
                <g
                  key={reg.id}
                  transform={`translate(${reg.cx}, ${reg.cy})`}
                  className="cursor-pointer group"
                  onMouseEnter={() => {
                    soundEffects.playClick();
                    setHoveredRegion(reg.id);
                  }}
                  onMouseLeave={() => setHoveredRegion(null)}
                  onClick={(e) => {
                    e.stopPropagation();
                    soundEffects.playClick();
                    if (onSelectRegion) onSelectRegion(reg.id);
                  }}
                >
                  {/* Pulsing Radar Ring on Capital and Major Hubs */}
                  {(reg.isCapital || dealsCount > 7000) && (
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
                    r={isHovered ? "14" : (reg.isCapital ? "10" : "7.5")}
                    fill={isHovered ? "rgba(200, 234, 74, 0.35)" : "rgba(25, 45, 25, 0.7)"}
                    stroke={isHovered || reg.isCapital ? "#C8EA4A" : "#3e633e"}
                    strokeWidth={reg.isCapital ? 2.5 : 1.2}
                    className="transition-all duration-200"
                  />

                  {/* Center Dot */}
                  <circle
                    r={reg.isCapital ? "4.5" : "3.2"}
                    fill={reg.isCapital ? "#FFFFFF" : (isHovered ? "#C8EA4A" : "#B2D858")}
                  />

                  {/* Region Code Tag with Counter-Rotation Billboarding so text is ALWAYS readable */}
                  <g 
                    style={{ 
                      transform: is3D ? `rotateY(${-rotY}deg)` : 'none', 
                      transformOrigin: '0px -12px',
                      transition: isDragging.current ? 'none' : 'transform 0.08s linear'
                    }}
                  >
                    <text
                      y="-12"
                      textAnchor="middle"
                      fill={isHovered || isSelected ? "#C8EA4A" : "#97B592"}
                      fontSize={reg.isCapital ? "11" : "10"}
                      fontFamily="monospace"
                      fontWeight={reg.isCapital || isHovered ? "bold" : "normal"}
                      className="pointer-events-none select-none drop-shadow-md"
                    >
                      {reg.short}
                    </text>
                  </g>
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
                {UZBEKISTAN_REGIONS.find(r => r.id === hoveredRegion)?.label || hoveredRegion}
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
          <span>360° ВРАЩЕНИЕ ПО ОСИ Y</span>
          <span className="text-[#556952] hidden md:inline">| Двигайте мышью влево/вправо для ручного вращения</span>
        </div>
        <div className="text-[10px] text-[#C8EA4A]">
          УГОЛ ВРАЩЕНИЯ Y: {Math.round(rotY)}°
        </div>
      </div>
    </div>
  );
}
