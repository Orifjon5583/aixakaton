import React, { useState, useEffect } from 'react';
import { soundEffects } from './SoundEffects';

export default function DealRegistryTable({ year = 2026, onSelectDeal, initialFilter = '', lang = 'ru' }) {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState(initialFilter);
  const [page, setPage] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    setSearchTerm(initialFilter);
  }, [initialFilter]);

  useEffect(() => {
    let isMounted = true;
    const fetchDeals = async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/analytics/deals?year=${year}&limit=100&offset=0`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) setDeals(data);
        }
      } catch (err) {
        console.error('Error fetching deals registry', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDeals();
    return () => { isMounted = false; };
  }, [year]);

  // Client-side filtering by search term (company, product, contract)
  const filteredDeals = deals.filter(d => {
    if (!searchTerm) return true;
    const s = searchTerm.toLowerCase();
    return (
      d.product_name?.toLowerCase().includes(s) ||
      d.seller_name?.toLowerCase().includes(s) ||
      d.buyer_name?.toLowerCase().includes(s) ||
      d.region?.toLowerCase().includes(s) ||
      String(d.deal_id).includes(s) ||
      String(d.contract_id).includes(s)
    );
  });

  const pagedDeals = filteredDeals.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(filteredDeals.length / pageSize) || 1;

  // CSV Export for Deal Registry
  const exportRegistryCSV = () => {
    soundEffects.playSuccess();
    const headers = ['Deal ID', 'Date', 'Product', 'Amount UZS', 'Quantity', 'Unit', 'Unit Price', 'Seller', 'Buyer', 'Region', 'Status'];
    const rows = filteredDeals.map(d => [
      d.deal_id,
      d.deal_date,
      `"${(d.product_name || '').replace(/"/g, '""')}"`,
      d.deal_amount_uzs,
      d.quantity,
      d.unit || '',
      d.unit_price,
      `"${(d.seller_name || '').replace(/"/g, '""')}"`,
      `"${(d.buyer_name || '').replace(/"/g, '""')}"`,
      `"${(d.region || '').replace(/"/g, '""')}"`,
      d.deal_status || ''
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `uzex_deals_registry_${year}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-[#090E09] border border-[#203220] rounded-2xl p-5 shadow-2xl text-left select-none">
      
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#1b2b1b]">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-[#8aa587] uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-[#C8EA4A]" />
            <span>{lang === 'uz' ? `Rasmiy birja reyestri (${year})` : `Официальный биржевой реестр (${year})`}</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold font-mono text-white mt-1">
            {lang === 'uz' ? 'UZEX tezkor spot-bitimlari' : 'Оперативные спот-сделки UZEX'}
          </h3>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto">
          {/* Search Box */}
          <div className="relative flex-1 sm:w-72">
            <input
              type="text"
              placeholder={lang === 'uz' ? "Tovar, kompaniya, ID bo‘yicha qidiruv..." : "Поиск по товару, компании, ID..."}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0);
              }}
              className="w-full px-3 py-1.5 rounded-lg bg-[#111c11] border border-[#284028] text-xs font-mono text-white placeholder-[#5a7357] focus:outline-none focus:border-[#C8EA4A] transition-colors"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-[#708c6d] hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          {/* CSV Export Button */}
          <button
            onClick={exportRegistryCSV}
            className="px-3 py-1.5 rounded-lg bg-[#162416] hover:bg-[#223622] border border-[#2c472c] text-xs font-mono text-[#C8EA4A] flex items-center justify-center gap-1.5 transition-colors"
          >
            <span>{lang === 'uz' ? '📥 CSV eksport' : '📥 Экспорт CSV'}</span>
          </button>
        </div>
      </div>

      <div className="text-[10px] text-[#556952] font-mono sm:hidden flex items-center justify-between mt-2">
        <span>{lang === 'uz' ? '↔️ Jadvalni gorizontal suring' : '↔️ Прокручивайте таблицу'}</span>
        <span>{lang === 'uz' ? `Jami: ${filteredDeals.length} ta` : `Всего: ${filteredDeals.length} сделок`}</span>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto mt-4">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-[#1b2b1b] text-[#6d8869] text-[11px] uppercase">
              <th className="py-2.5 px-3">{lang === 'uz' ? '№ Bitim / Sana' : '№ Сделки / Дата'}</th>
              <th className="py-2.5 px-3">{lang === 'uz' ? 'Tovar / Nomenklatura' : 'Товар / Номенклатура'}</th>
              <th className="py-2.5 px-3 text-right">{lang === 'uz' ? 'Bitim summasi' : 'Сумма сделки'}</th>
              <th className="py-2.5 px-3">{lang === 'uz' ? 'Sotuvchi' : 'Продавец'}</th>
              <th className="py-2.5 px-3">{lang === 'uz' ? 'Xaridor' : 'Покупатель'}</th>
              <th className="py-2.5 px-3">{lang === 'uz' ? 'Hudud' : 'Регион'}</th>
              <th className="py-2.5 px-3 text-center">{lang === 'uz' ? 'Pasport' : 'Паспорт'}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#152215]">
            {loading ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-[#708c6d] animate-pulse">
                  {lang === 'uz' ? 'Birja reyestri yuklanmoqda...' : 'Загрузка биржевого реестра...'}
                </td>
              </tr>
            ) : pagedDeals.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-[#708c6d]">
                  {lang === 'uz' ? `«${searchTerm}» bo‘yicha bitimlar topilmadi.` : `По запросу «${searchTerm}» сделок не найдено.`}
                </td>
              </tr>
            ) : (
              pagedDeals.map((deal) => (
                <tr
                  key={deal.deal_id}
                  onClick={() => {
                    soundEffects.playClick();
                    onSelectDeal(deal.deal_id);
                  }}
                  className="hover:bg-[#121c12] cursor-pointer transition-colors group"
                >
                  <td className="py-3 px-3">
                    <div className="font-bold text-white group-hover:text-[#C8EA4A] transition-colors">
                      #{deal.deal_id}
                    </div>
                    <div className="text-[10px] text-[#5e785b]">{deal.deal_date}</div>
                  </td>

                  <td className="py-3 px-3 max-w-[220px]">
                    <div className="text-white truncate font-sans text-xs font-medium" title={deal.product_name}>
                      {deal.product_name}
                    </div>
                    <div className="text-[10px] text-[#708c6d]">
                      {Number(deal.quantity).toLocaleString()} {deal.unit} • {Number(deal.unit_price).toLocaleString()} UZS/{lang === 'uz' ? 'birlik' : 'ед'}
                    </div>
                  </td>

                  <td className="py-3 px-3 text-right">
                    <div className="font-bold text-[#C8EA4A]">
                      {Number(deal.deal_amount_uzs).toLocaleString('ru-RU')}
                    </div>
                    <div className="text-[10px] text-[#5e785b]">UZS</div>
                  </td>

                  <td className="py-3 px-3 max-w-[150px]">
                    <div className="text-[#A6C49F] truncate font-medium" title={deal.seller_name}>
                      {deal.seller_name}
                    </div>
                  </td>

                  <td className="py-3 px-3 max-w-[150px]">
                    <div className="text-[#A6C49F] truncate font-medium" title={deal.buyer_name}>
                      {deal.buyer_name}
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-[#132013] border border-[#233823] text-[10px] text-[#8aa587]">
                      {deal.region?.replace(' viloyati', '').replace(' shahri', '') || '—'}
                    </span>
                  </td>

                  <td className="py-3 px-3 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        soundEffects.playClick();
                        onSelectDeal(deal.deal_id);
                      }}
                      className="px-2.5 py-1 rounded bg-[#182818] group-hover:bg-[#C8EA4A] group-hover:text-[#090E09] border border-[#2b442b] text-[11px] font-mono text-[#C8EA4A] transition-all"
                    >
                      {lang === 'uz' ? 'Pasport ↗' : 'Паспорт ↗'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between pt-4 mt-2 border-t border-[#1b2b1b] text-xs font-mono text-[#6d8869]">
        <div>
          {lang === 'uz'
            ? `Ko‘rsatildi: ${pagedDeals.length} ta (${filteredDeals.length} tadan)`
            : `Показано: ${pagedDeals.length} из ${filteredDeals.length} сделок`}
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled={page === 0}
            onClick={() => {
              soundEffects.playClick();
              setPage(p => Math.max(0, p - 1));
            }}
            className="px-2.5 py-1 rounded bg-[#132013] disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#1e301e] text-[#A6C49F] transition-colors"
          >
            {lang === 'uz' ? '← Oldingi' : '← Назад'}
          </button>
          <span>
            {page + 1} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages - 1}
            onClick={() => {
              soundEffects.playClick();
              setPage(p => p + 1);
            }}
            className="px-2.5 py-1 rounded bg-[#132013] disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#1e301e] text-[#A6C49F] transition-colors"
          >
            {lang === 'uz' ? 'Keyingi →' : 'Вперёд →'}
          </button>
        </div>
      </div>

    </div>
  );
}
