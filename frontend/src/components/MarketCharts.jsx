import React, { useState, useEffect } from 'react';
import { soundEffects } from './SoundEffects';

export default function MarketCharts({ year = 2026 }) {
  const [metricType, setMetricType] = useState('amount'); // 'amount' or 'deals'
  const [monthlyData, setMonthlyData] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [hoveredMonth, setHoveredMonth] = useState(null);
  const [hoveredSlice, setHoveredSlice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchChartData = async () => {
      try {
        setLoading(true);
        const [monthlyRes, productsRes] = await Promise.all([
          fetch(`/api/analytics/monthly?year=${year}`),
          fetch(`/api/analytics/top-products?limit=5`)
        ]);

        if (monthlyRes.ok && productsRes.ok) {
          const mData = await monthlyRes.json();
          const pData = await productsRes.json();
          if (isMounted) {
            setMonthlyData(mData);
            setTopProducts(pData);
          }
        }
      } catch (err) {
        console.error('Error fetching market chart data', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchChartData();
    return () => { isMounted = false; };
  }, [year]);

  // Compute SVG Points for Monthly Chart
  const svgWidth = 600;
  const svgHeight = 220;
  const paddingX = 40;
  const paddingY = 30;

  const getPoints = () => {
    if (!monthlyData.length) return { linePath: '', areaPath: '', points: [] };

    const values = monthlyData.map(d => metricType === 'amount' ? d.amount_trln : d.deals_count);
    const maxVal = Math.max(...values, 1) * 1.15;
    const stepX = (svgWidth - paddingX * 2) / Math.max(1, monthlyData.length - 1);

    const points = monthlyData.map((d, i) => {
      const val = metricType === 'amount' ? d.amount_trln : d.deals_count;
      const x = paddingX + i * stepX;
      const y = svgHeight - paddingY - (val / maxVal) * (svgHeight - paddingY * 2);
      return { x, y, data: d, val };
    });

    const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
    const areaPath = `${linePath} L ${points[points.length - 1].x.toFixed(1)} ${svgHeight - paddingY} L ${points[0].x.toFixed(1)} ${svgHeight - paddingY} Z`;

    return { linePath, areaPath, points };
  };

  const { linePath, areaPath, points } = getPoints();

  // Donut chart calculations
  const totalTopProductsSum = topProducts.reduce((acc, p) => acc + (p.total_amount_uzs || 0), 0) || 1;
  const donutColors = ['#C8EA4A', '#70FFC2', '#4AA8EA', '#F5A623', '#A84AEA'];

  let cumulativeAngle = 0;
  const donutSlices = topProducts.map((p, idx) => {
    const fraction = (p.total_amount_uzs || 0) / totalTopProductsSum;
    const angle = fraction * 360;
    const startAngle = cumulativeAngle;
    const endAngle = cumulativeAngle + angle;
    cumulativeAngle = endAngle;

    // SVG arc coordinates
    const r = 80;
    const cx = 110;
    const cy = 110;

    const startRad = (startAngle - 90) * (Math.PI / 180);
    const endRad = (endAngle - 90) * (Math.PI / 180);

    const x1 = cx + r * Math.cos(startRad);
    const y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad);
    const y2 = cy + r * Math.sin(endRad);

    const largeArcFlag = angle > 180 ? 1 : 0;
    const pathData = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;

    return {
      product: p,
      pathData,
      color: donutColors[idx % donutColors.length],
      percentage: (fraction * 100).toFixed(1),
      amount_mlrd: Math.round((p.total_amount_uzs || 0) / 1e9)
    };
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      {/* 1. Monthly Dynamics Card (2 Columns wide) */}
      <div className="lg:col-span-2 bg-[#090E09] border border-[#203220] rounded-2xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between">
        
        {/* Header with Switcher */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#1b2b1b]">
          <div>
            <div className="text-xs font-mono text-[#8aa587] uppercase tracking-wider">
              Динамика торгов ({year})
            </div>
            <h3 className="text-lg font-bold font-mono text-white">
              Ежемесячная активность биржи
            </h3>
          </div>

          <div className="flex items-center gap-1 bg-[#121c12] p-1 rounded-lg border border-[#233823]">
            <button
              onClick={() => {
                soundEffects.playClick();
                setMetricType('amount');
              }}
              className={`px-2.5 py-1 text-xs font-mono rounded transition-all ${
                metricType === 'amount'
                  ? 'bg-[#C8EA4A] text-[#090E09] font-bold shadow-md'
                  : 'text-[#8aa587] hover:text-white'
              }`}
            >
              Сумма (трлн UZS)
            </button>
            <button
              onClick={() => {
                soundEffects.playClick();
                setMetricType('deals');
              }}
              className={`px-2.5 py-1 text-xs font-mono rounded transition-all ${
                metricType === 'deals'
                  ? 'bg-[#C8EA4A] text-[#090E09] font-bold shadow-md'
                  : 'text-[#8aa587] hover:text-white'
              }`}
            >
              Сделки (шт)
            </button>
          </div>
        </div>

        {/* SVG Dynamics Graph */}
        <div className="relative w-full h-[240px] my-2 select-none">
          <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#C8EA4A" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#C8EA4A" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Horizontal Grid lines */}
            {[0.25, 0.5, 0.75, 1.0].map((frac, idx) => {
              const y = svgHeight - paddingY - frac * (svgHeight - paddingY * 2);
              return (
                <line
                  key={idx}
                  x1={paddingX}
                  y1={y}
                  x2={svgWidth - paddingX}
                  y2={y}
                  stroke="#1c2b1c"
                  strokeDasharray="3 3"
                />
              );
            })}

            {/* Filled Area */}
            {areaPath && (
              <path d={areaPath} fill="url(#chartGradient)" />
            )}

            {/* Line Path */}
            {linePath && (
              <path
                d={linePath}
                fill="none"
                stroke="#C8EA4A"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Data Points */}
            {points.map((p, idx) => {
              const isHovered = hoveredMonth === p.data.month;
              return (
                <g key={idx} className="cursor-pointer" onMouseEnter={() => setHoveredMonth(p.data.month)} onMouseLeave={() => setHoveredMonth(null)}>
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={isHovered ? 6 : 4}
                    fill={isHovered ? '#FFFFFF' : '#C8EA4A'}
                    stroke="#090E09"
                    strokeWidth="2"
                    className="transition-all duration-150"
                  />
                  {/* Month Label on X axis */}
                  <text
                    x={p.x}
                    y={svgHeight - 10}
                    textAnchor="middle"
                    fill={isHovered ? '#C8EA4A' : '#6f886c'}
                    fontSize="10"
                    fontFamily="monospace"
                  >
                    {p.data.name_ru || p.data.month}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Floating Hover Readout Tooltip */}
          {hoveredMonth && (
            <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-[#101b10]/95 border border-[#C8EA4A]/50 rounded-lg px-3 py-1.5 shadow-xl font-mono text-xs flex items-center gap-3">
              <span className="text-[#C8EA4A] font-bold">
                {monthlyData.find(d => d.month === hoveredMonth)?.name_ru}:
              </span>
              <span className="text-white">
                {monthlyData.find(d => d.month === hoveredMonth)?.deals_count?.toLocaleString()} сделок
              </span>
              <span className="text-[#A6C49F]">
                ({monthlyData.find(d => d.month === hoveredMonth)?.amount_trln} трлн UZS)
              </span>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between text-[11px] font-mono text-[#5b7357] pt-2 border-t border-[#1b2b1b]">
          <span>Источник: Spot DWH UZEX</span>
          <span>Сезонный пик: Сентябрь — Октябрь</span>
        </div>
      </div>

      {/* 2. Commodity Market Structure Donut Card (1 Column wide) */}
      <div className="bg-[#090E09] border border-[#203220] rounded-2xl p-5 shadow-2xl flex flex-col justify-between">
        
        <div className="pb-3 border-b border-[#1b2b1b]">
          <div className="text-xs font-mono text-[#8aa587] uppercase tracking-wider">
            Структура рынка ({year})
          </div>
          <h3 className="text-lg font-bold font-mono text-white">
            Ключевые товарные группы
          </h3>
        </div>

        {/* Donut SVG Visual */}
        <div className="relative flex items-center justify-center my-3">
          <svg width="220" height="220" viewBox="0 0 220 220" className="overflow-visible">
            {donutSlices.map((slice, idx) => (
              <path
                key={idx}
                d={slice.pathData}
                fill={slice.color}
                opacity={hoveredSlice === null || hoveredSlice === idx ? 0.9 : 0.35}
                stroke="#090E09"
                strokeWidth="2.5"
                className="cursor-pointer transition-all duration-200 hover:opacity-100"
                onMouseEnter={() => setHoveredSlice(idx)}
                onMouseLeave={() => setHoveredSlice(null)}
              />
            ))}

            {/* Inner Hollow Center for Donut */}
            <circle cx="110" cy="110" r="50" fill="#090E09" stroke="#1f331f" strokeWidth="1" />
            
            <text x="110" y="105" textAnchor="middle" fill="#8aa587" fontSize="10" fontFamily="monospace">
              ТОП-5
            </text>
            <text x="110" y="125" textAnchor="middle" fill="#C8EA4A" fontSize="13" fontWeight="bold" fontFamily="monospace">
              {hoveredSlice !== null ? `${donutSlices[hoveredSlice]?.percentage}%` : 'UZEX SPOT'}
            </text>
          </svg>
        </div>

        {/* Legend List */}
        <div className="space-y-1.5 font-mono text-xs pt-2 border-t border-[#1b2b1b]">
          {donutSlices.map((slice, idx) => (
            <div
              key={idx}
              className={`flex items-center justify-between p-1 rounded transition-colors ${
                hoveredSlice === idx ? 'bg-[#142214]' : ''
              }`}
              onMouseEnter={() => setHoveredSlice(idx)}
              onMouseLeave={() => setHoveredSlice(null)}
            >
              <div className="flex items-center gap-2 truncate max-w-[170px]">
                <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: slice.color }} />
                <span className="text-white truncate" title={slice.product.product_name}>
                  {slice.product.product_name}
                </span>
              </div>
              <div className="flex items-center gap-2 text-right">
                <span className="text-[#C8EA4A] font-bold">{slice.percentage}%</span>
                <span className="text-[#647c61] text-[10px]">({slice.amount_mlrd} млрд)</span>
              </div>
            </div>
          ))}
        </div>

      </div>

    </div>
  );
}
