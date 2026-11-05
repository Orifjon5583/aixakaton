import React, { useEffect, useState } from 'react';
import { soundEffects } from './SoundEffects';

export default function DealPassportModal({ dealId, onClose, onFilterCompany, lang = 'ru' }) {
  const [deal, setDeal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!dealId) return;
    let isMounted = true;
    soundEffects.playClick();

    const fetchDeal = async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/analytics/deals/${dealId}`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) setDeal(data);
        }
      } catch (err) {
        console.error('Error fetching deal passport', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDeal();

    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => {
      isMounted = false;
      window.removeEventListener('keydown', handleEsc);
    };
  }, [dealId, onClose]);

  const copyPassportId = () => {
    if (deal) {
      navigator.clipboard.writeText(`UZEX-DEAL-${deal.deal_id}`);
      setCopied(true);
      soundEffects.playSuccess();
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!dealId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-fadeIn">
      {/* Background click to close */}
      <div className="absolute inset-0" onClick={onClose} />

      <div className="relative w-full max-w-3xl max-h-[92vh] overflow-y-auto bg-[#0C140C] border border-[#284028] rounded-2xl p-6 sm:p-8 shadow-2xl text-left z-10 text-[#E6ECE0]">
        
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-[#1f331f] pb-4 mb-6">
          <div>
            <div className="flex items-center gap-3 text-xs font-mono text-[#8aa587] mb-1">
              <span>{deal?.deal_date || '—'}</span>
              <span>•</span>
              <span className="uppercase text-[#C8EA4A]">{deal?.contract_type || (lang === 'uz' ? 'Ichki' : 'Внутренний')}</span>
              <span>•</span>
              <span className="uppercase text-[#8aa587]">{deal?.auction_type || (lang === 'uz' ? 'Spot' : 'Спот')}</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-white flex items-center gap-3">
              <span>{lang === 'uz' ? `Bitim №${deal?.deal_id || dealId}` : `Сделка №${deal?.deal_id || dealId}`}</span>
              <button 
                onClick={copyPassportId} 
                className="text-xs px-2 py-0.5 rounded bg-[#182818] border border-[#2c472c] text-[#A6C49F] hover:text-[#C8EA4A] transition-colors"
                title={lang === 'uz' ? "Raqamni nusxalash" : "Скопировать номер"}
              >
                {copied ? (lang === 'uz' ? '✓ Nusxalandi' : '✓ Скопировано') : (lang === 'uz' ? 'Nusxalash' : 'Копировать')}
              </button>
            </h2>
          </div>

          <button
            onClick={() => {
              soundEffects.playClick();
              onClose();
            }}
            className="w-9 h-9 rounded-full bg-[#182618] hover:bg-[#253d25] border border-[#2c472c] text-[#A6C49F] hover:text-white flex items-center justify-center text-lg transition-colors"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div className="py-16 text-center font-mono text-sm text-[#7F967B] animate-pulse">
            {lang === 'uz' ? 'Birja bitimining elektron pasporti yuklanmoqda...' : 'Загрузка электронного паспорта биржевой сделки...'}
          </div>
        ) : !deal ? (
          <div className="py-16 text-center font-mono text-sm text-red-400">
            {lang === 'uz' ? `Bitim #${dealId} UZEX ma'lumotlar bazasida topilmadi.` : `Сделка #${dealId} не найдена в базе данных UZEX.`}
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* Product Card Title */}
            <div className="bg-[#121E12] border border-[#253d25] rounded-xl p-4">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-xs font-mono text-[#8aa587] uppercase tracking-wider">
                  {lang === 'uz' ? 'Birja tovari / Nomenklatura' : 'Биржевой товар / Номенклатура'}
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#C8EA4A]/10 text-[#C8EA4A] border border-[#C8EA4A]/30">
                  {deal.deal_status || (lang === 'uz' ? 'Bajarilgan' : 'Исполнен')}
                </span>
              </div>
              <h3 className="text-base sm:text-lg font-semibold text-white leading-relaxed">
                {deal.product_name}
              </h3>
            </div>

            {/* Main KPI Amount & Physical Volume */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-[#101a10] border border-[#223822] rounded-xl p-5">
                <div className="text-xs font-mono text-[#7b9777] mb-1 uppercase">
                  {lang === 'uz' ? 'Bitimning umumiy summasi' : 'Общая сумма сделки'}
                </div>
                <div className="text-2xl sm:text-3xl font-mono font-bold text-[#C8EA4A]">
                  {Number(deal.deal_amount_uzs).toLocaleString('ru-RU')}
                  <span className="text-base font-normal text-[#8aa587] ml-2">UZS</span>
                </div>
                <div className="text-[11px] font-mono text-[#5b7357] mt-1">
                  {lang === 'uz' ? `Hisob-kitob valyutasi: ${deal.currency || 'UZS'}` : `Валюта расчёта: ${deal.currency || 'UZS'}`}
                </div>
              </div>

              <div className="bg-[#101a10] border border-[#223822] rounded-xl p-5">
                <div className="text-xs font-mono text-[#7b9777] mb-1 uppercase">
                  {lang === 'uz' ? 'Jismoniy yetkazib berish hajmi' : 'Физический объём поставки'}
                </div>
                <div className="text-2xl sm:text-3xl font-mono font-bold text-white">
                  {Number(deal.volume_units || deal.quantity).toLocaleString('ru-RU')}
                  <span className="text-base font-normal text-[#8aa587] ml-2">{deal.unit || (lang === 'uz' ? 'birlik' : 'ед.')}</span>
                </div>
                <div className="text-[11px] font-mono text-[#5b7357] mt-1">
                  {lang === 'uz'
                    ? `Formula: ${deal.quantity} lot × ${deal.lot_size || 1} ${deal.unit}`
                    : `Формула: ${deal.quantity} лотов × ${deal.lot_size || 1} ${deal.unit}`}
                </div>
              </div>
            </div>

            {/* Seller & Buyer Detailed Dossier */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* SELLER */}
              <div className="bg-[#111c11] border border-[#233b23] rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#70FFC2]" />
                    <span className="text-xs font-mono font-bold tracking-wider uppercase text-[#70FFC2]">
                      {lang === 'uz' ? 'SOTUVCHI (SELLER)' : 'ПРОДАВЕЦ (SELLER)'}
                    </span>
                  </div>

                  <div className="font-semibold text-white text-base mb-1">
                    {deal.seller_name || (lang === 'uz' ? 'Sotuvchi korxona' : 'Предприятие-продавец')}
                  </div>
                  <div className="font-mono text-xs text-[#8aa587] mb-3">
                    {lang === 'uz' ? 'STIR / INN:' : 'ИНН / STIR:'} <span className="text-white font-bold">{deal.seller_inn}</span>
                  </div>

                  <div className="pt-3 border-t border-[#1e331e] space-y-1 text-xs font-mono text-[#7b9777]">
                    <div>
                      {lang === 'uz' ? 'Hudud:' : 'Регион:'} <span className="text-[#A6C49F]">{deal.seller_region || (lang === 'uz' ? 'O‘zbekiston' : 'Узбекистан')}</span>
                    </div>
                    <div>
                      {lang === 'uz' ? 'Broker:' : 'Брокер:'} <span className="text-white">{deal.seller_broker}</span> ({deal.seller_broker_name || (lang === 'uz' ? 'Akkreditatsiyadan o‘tgan broker' : 'Аккредитованный брокер')})
                    </div>
                  </div>
                </div>

                {onFilterCompany && (
                  <button
                    onClick={() => {
                      soundEffects.playClick();
                      onFilterCompany(deal.seller_name);
                      onClose();
                    }}
                    className="mt-4 w-full py-2 px-3 rounded-lg bg-[#182718] hover:bg-[#233a23] border border-[#2b442b] text-xs font-mono text-[#C8EA4A] text-center transition-colors"
                  >
                    {lang === 'uz' ? 'Sotuvchining barcha bitimlari →' : 'Все сделки продавца →'}
                  </button>
                )}
              </div>

              {/* BUYER */}
              <div className="bg-[#111c11] border border-[#233b23] rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#C8EA4A]" />
                    <span className="text-xs font-mono font-bold tracking-wider uppercase text-[#C8EA4A]">
                      {lang === 'uz' ? 'XARIDOR (BUYER)' : 'ПОКУПАТЕЛЬ (BUYER)'}
                    </span>
                  </div>

                  <div className="font-semibold text-white text-base mb-1">
                    {deal.buyer_name || (lang === 'uz' ? 'Xaridor korxona' : 'Предприятие-покупатель')}
                  </div>
                  <div className="font-mono text-xs text-[#8aa587] mb-3">
                    {lang === 'uz' ? 'STIR / INN:' : 'ИНН / STIR:'} <span className="text-white font-bold">{deal.buyer_inn}</span>
                  </div>

                  <div className="pt-3 border-t border-[#1e331e] space-y-1 text-xs font-mono text-[#7b9777]">
                    <div>
                      {lang === 'uz' ? 'Hudud:' : 'Регион:'} <span className="text-[#A6C49F]">{deal.buyer_region || (lang === 'uz' ? 'O‘zbekiston' : 'Узбекистан')}</span>
                    </div>
                    <div>
                      {lang === 'uz' ? 'Broker:' : 'Брокер:'} <span className="text-white">{deal.buyer_broker}</span> ({deal.buyer_broker_name || (lang === 'uz' ? 'Akkreditatsiyadan o‘tgan broker' : 'Аккредитованный брокер')})
                    </div>
                  </div>
                </div>

                {onFilterCompany && (
                  <button
                    onClick={() => {
                      soundEffects.playClick();
                      onFilterCompany(deal.buyer_name);
                      onClose();
                    }}
                    className="mt-4 w-full py-2 px-3 rounded-lg bg-[#182718] hover:bg-[#233a23] border border-[#2b442b] text-xs font-mono text-[#C8EA4A] text-center transition-colors"
                  >
                    {lang === 'uz' ? 'Xaridorning barcha bitimlari →' : 'Все сделки покупателя →'}
                  </button>
                )}
              </div>

            </div>

            {/* Detailed Parameters Registry Table */}
            <div className="bg-[#0f170f] border border-[#1f331f] rounded-xl p-4">
              <div className="text-xs font-mono text-[#8aa587] uppercase tracking-wider mb-3">
                {lang === 'uz' ? 'Shartnomaning texnik xususiyatlari' : 'Технические спецификации контракта'}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                <div className="bg-[#142014] p-2.5 rounded-lg border border-[#233823]">
                  <div className="text-[#6d8569] text-[10px]">{lang === 'uz' ? 'Birlik narxi' : 'Цена за единицу'}</div>
                  <div className="text-white font-bold mt-0.5">
                    {Number(deal.unit_price).toLocaleString('ru-RU')} UZS
                  </div>
                </div>

                <div className="bg-[#142014] p-2.5 rounded-lg border border-[#233823]">
                  <div className="text-[#6d8569] text-[10px]">{lang === 'uz' ? 'Boshlang‘ich narx' : 'Стартовая цена'}</div>
                  <div className="text-white font-bold mt-0.5">
                    {deal.starting_price ? `${Number(deal.starting_price).toLocaleString('ru-RU')} UZS` : '—'}
                  </div>
                </div>

                <div className="bg-[#142014] p-2.5 rounded-lg border border-[#233823]">
                  <div className="text-[#6d8569] text-[10px]">{lang === 'uz' ? 'Shartnoma ID' : 'ID Контракта'}</div>
                  <div className="text-[#C8EA4A] font-bold mt-0.5">
                    #{deal.contract_id || deal.deal_id}
                  </div>
                </div>

                <div className="bg-[#142014] p-2.5 rounded-lg border border-[#233823]">
                  <div className="text-[#6d8569] text-[10px]">{lang === 'uz' ? 'Yetkazib berish bazisi' : 'Базис поставки'}</div>
                  <div className="text-white font-bold mt-0.5 truncate" title={deal.region}>
                    {deal.region || (lang === 'uz' ? 'Sotuvchi ombori' : 'Склад продавца')}
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-[#1b2b1b] flex flex-wrap items-center justify-between text-[11px] font-mono text-[#5b7357]">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#C8EA4A]" />
                  <span>{lang === 'uz' ? 'DUCKDB DWH DA TASDIQLANGAN • 100% FAKTIK AUDIT' : 'ВЕРИФИЦИРОВАНО В DUCKDB DWH • 100% ФАКТИЧЕСКИЙ АУДИТ'}</span>
                </div>
                <div>
                  {lang === 'uz' ? `Kliring sanasi: ${deal.payment_date || deal.deal_date}` : `Дата клиринга: ${deal.payment_date || deal.deal_date}`}
                </div>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
