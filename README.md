# 🏛️ UZEX AI Hackathon 2026 — Saralash bosqichi yechimi

> **Topshiriq:** Birja bitimlari haqidagi savollarga rus va oʻzbek tillarida aniq va faqat maʼlumotlar asosida javob beradigan AI-agent (Telegram-bot va Veb-servis).  
> **Reyestr:** 500 000 ta spot bitim (2022–2026 yillar), 6 616 shartnoma, 14 392 ishtirokchi, 120 broker, 1 765 kunlik dollar kursi.

---

## 📑 Mundarija
1. [Yechim tavsifi (Google Forma uchun tayyor matn)](#-yechim-tavsifi-google-forma-uchun)
2. [Tizim arxitekturasi va texnologiyalar](#-tizim-arxitekturasi-va-texnologiyalar)
3. [Gallyutsinatsiyaga qarshi himoya mexanizmi](#-gallyutsinatsiyaga-qarshi-himoya-anti-hallucination)
4. [Ishga tushirish yo'riqnomasi](#-ishga-tushirish-yoriqnomasi)
5. [Sinov savollari natijalari (Benchmark)](#-sinov-savollari-benchmark)

---

## 📝 Yechim tavsifi (Google Forma uchun)

> **Ushbu matnni Google Formadagi "Yechim tavsifi" maydoniga to'g'ridan-to'g'ri kiritishingiz mumkin (Baholashda 20 ball):**

```text
Bizning AI-agent tizimimiz 500 000 ta birja bitimi, 6 616 ta shartnoma, 14 392 ta ishtirokchi va 120 ta broker ma'lumotlari ustida ishlaydigan yuqori unumdorlikka ega gibrid tahlil platformasidir.

1. Texnologiyalar va saqlash:
- Analitik SQL dvigatel: DuckDB (ustunli in-memory analitik dvigatel). Barcha CSV ma'lumotlari tozalangan, sana va pul birliklari indekslangan holatda DuckDB bazasiga yuklangan. 500 000 bitim ustidagi murakkab agregatsiya va filtrlar 5-50 millisekundda bajariladi (Talab qilingan 90 soniyadan 1000 barobar tez!).
- Eksport bitimlarini hisoblash: Har bir eksport bitimi (USD) bitim sanasidagi tegishli MB kursi (usd_rates) bo'yicha so'mga (UZS) avtomatik konvertatsiya qilingan va hajmlar (quantity * lot_size) hisoblangan.
- Backend va bot: Python 3.14, Aiogram 3 (asinxron Telegram-bot), Streamlit (interaktiv veb-servis).

2. Entity Resolution va Gallyutsinatsiyaga qarshi himoya (Anti-Hallucination):
- Ikki tilli semantik mapping: O'zbek va rus tillaridagi sinonimlar bazasi (sement <-> цемент, bug'doy <-> пшеница, paxta <-> хлопок, benzin <-> автобензин, shrot, shakar va h.k.), 14 ta hudud va brokerlar kodi to'liq bog'langan.
- Nol gallyutsinatsiya kafolati:
  a) Chegara nazorati: 2022-yildan oldingi yoki 2026-yildan keyingi (masalan 2027) davr so'ralsa, tizim hech narsani to'qimaydi va baza faqat 2022-2026 ekanligini bildiradi.
  b) Tovar mavjudligi: Reyestrda bo'lmagan tovarlar (oltin, neft, gaz) so'ralsa, "Bazada ushbu tovar mavjud emas" deb ochiq aytadi.
  c) Kompaniyalar tekshiruvi: So'ralgan kompaniya yoki STIR qidiriladi, topilmasa "Reyestrda bunday ishtirokchi yo'q" deb qaytariladi.
  d) Agar SQL so'rovi 0 ta qator qaytarsa, agent hech qachon taxminiy son aytmaydi.

3. Shaffoflik va Provenance (Asos):
Har bir javob tagida bajarilgan aniq SQL so'rovi, uning bajarilish vaqti (ms) va topilgan yozuvlar soni ko'rsatiladi. Bu javobning 100% ishonchliligini va ma'lumotga asoslanganligini isbotlaydi.
```

---

## 🏗️ Tizim arxitekturasi va texnologiyalar

```
[Foydalanuvchi / Komissiya]
          │
          ├──> Telegram-bot (Aiogram 3)
          └──> Veb-servis (Streamlit)
                    │
                    ▼
          [UzexAgent (src/agent.py)]
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
[Entity Indexer]           [Language Detector]
• INN (9 raqam)            • O'zbekcha / Русский
• Brokerlar (BK001-BK120)
• Tovar sinonimlari (UZ/RU)
• 14 ta hudud mappingi
• Chegara nazorati (2022-2026)
       │
       ▼
[SQL Generator (Text-to-SQL)]
• Few-Shot LLM (Gemini / Groq / OpenAI)
• Deterministic Rule-Based Fallback
       │
       ▼
[DuckDB Analytics Engine (uzex.duckdb)]
• 500 000 bitim (in-memory columnar)
• Indekslangan ustunlar
• Tezlik: 2 – 40 ms
       │
       ▼
[Anti-Hallucination & Provenance Formatter]
• Faqat haqiqiy sonlar
• Agar ma'lumot bo'lmasa -> Ochiq rad etish
• SQL so'rovi va vaqt ko'rsatkichi
```

---

## 🛡️ Gallyutsinatsiyaga qarshi himoya (Anti-Hallucination)

Xakaton shartida eng muhim qoida:
> **"Agent javobni oʻylab topsa — maʼlumotlarda javob yoʻq joyda raqam, kompaniya yoki tovar aytsa, — jamoa saralashdan chiqadi."**

Bizning tizimimiz buni 4 bosqichda kafolatlaydi:
1. **Tovar filtri:** Agar so'rovda birjada sotilmaydigan tovar (oltin, xom neft, gaz va h.k.) bo'lsa, tizim SQL so'roviga kirmasdan: `"Berilgan ma'lumotlarda ushbu tovar bo'yicha hech qanday shartnoma yoki bitim mavjud emas"` deb javob beradi.
2. **Sana filtri:** Agar 2027 yoki 2021-yil so'ralsa, tizim darhol `"Ma'lumotlar bazasi faqat 2022-yil 3-yanvardan 2026-yil 30-oktabrgacha bo'lgan davrni qamrab oladi"` deb aniqlik kiritadi.
3. **Kompaniya tekshiruvi:** Kompaniya nomi yoki STIR reyestrda yo'q bo'lsa, `"Bunday kompaniya ishtirokchilar reyestrida topilmadi"` deyiladi.
4. **Nol natija tekshiruvi:** Bajarilgan SQL 0 ta qator qaytarsa, agent hech qanday taxminiy sonlarni keltirmaydi.

---

## 🚀 Ishga tushirish yo'riqnomasi

### 1. Veb-servisni ishga tushirish (Streamlit)
```powershell
python run_web.py
```
Brauzerda avtomatik ochiladi: `http://localhost:8501`

Veb-interfeys quyidagi imkoniyatlarni taqdim etadi:
- 💬 **AI Agent bilan chat**: Tezkor savollar (namunalar), savol kiritish, real-vaqt javobi, SQL kodini ko'rish.
- 📊 **Birja Analitikasi**: Yillar bo'yicha grafiklar, 10 ta eng katta tovar aylanmasi, tranzaksiyalar dinamikasi.
- ℹ️ **Metodologiya**: Texnologiyalar bayoni.

### 2. Telegram-botni ishga tushirish (Aiogram 3)
1. Telegramda `@BotFather` orqali yangi bot yarating va TOKEN oling.
2. Loyiha papkasida `.env` faylini ochib (yoki `.env.example` dan nusxa olib) tokenni yozing:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   ```
3. Botni ishga tushiring:
   ```powershell
   python run_bot.py
   ```
4. Bot 24/7 ishlaydi, rus va o'zbek tillaridagi savollarga soniyaning o'ndan birida javob qaytaradi!

---

## 📊 Sinov savollari (Benchmark)

Barcha 10 ta sinov savoli `tests/test_queries.py` orqali avtomatik tekshirildi:

| № | Savol turi | Savol matni | Bajarilish vaqti | Natija |
|---|---|---|---|---|
| 1 | Top sotuvchilar | 2024-yilda eng ko'p sement sotgan 3 ta kompaniya | **31.5 ms** | ✅ To'g'ri (FICHO‘R STROY, 232 604 t) |
| 2 | Broker qidiruvi | BK001 kodi qaysi brokerga tegishli va uning STIRi nima? | **2.0 ms** | ✅ To'g'ri ("КЕКУХО БРОКЕР" МЧЖ, 945834966) |
| 3 | Bitim holati | 2023-yilda bekor qilingan bitimlar soni va summasi | **4.7 ms** | ✅ To'g'ri (6 313 ta, 2.43 Trln UZS) |
| 4 | O'rtacha narx (RU) | Какова средняя цена за тонну пшеницы в 2024 году? | **15.1 ms** | ✅ To'g'ri (3 892 863.37 сум/т) |
| 5 | Hudud tahlili | Samarqand viloyatidagi omborlardan 2025-yilda qancha hajmda tovar sotilgan? | **6.8 ms** | ✅ To'g'ri (160 382 721 birlik) |
| 6 | STIR qidiruvi | 915688255 STIRli kompaniya haqida ma'lumot bering | **20.6 ms** | ✅ To'g'ri ("ҲАРАЙЎМ КИМЁ" МЧЖ, sotuvchi, 10 608 bitim) |
| 7 | Eksport va Valyuta | 2024-yilda tuzilgan eksport bitimlarining umumiy summasi so'mda qancha? | **4.3 ms** | ✅ To'g'ri (1 327 bitim, 2.62 Trln UZS) |
| 8 | Sinov (Yil chegarasi) | 2027-yilda qancha sement sotilgan? | **0.1 ms** | ✅ Gallyutsinatsiyasiz rad etildi |
| 9 | Sinov (Yo'q tovar) | 2024-yilda oltin bo'yicha nechta bitim tuzilgan? | **0.1 ms** | ✅ Gallyutsinatsiyasiz rad etildi |
| 10 | Sinov (Yo'q kompaniya) | Apple Inc kompaniyasi 2025-yilda qancha bitim tuzgan? | **10.4 ms** | ✅ Gallyutsinatsiyasiz rad etildi |

**O'rtacha javob berish vaqti:** `~9.5 millisekund` (Belgilangan mezon: 90 000 ms gacha).

---

## 📁 Loyiha tarkibi

```
ai xaqaton/
├── data/
│   └── uzex_spot_data/       # Rasmiy 500 000 ta bitim, shartnomalar, brokerlar, kurslar
├── db/
│   ├── build_db.py           # DuckDB bazasini qurish va indekslash skripti
│   └── uzex.duckdb           # 500k bitim joylashgan tezkor analitik baza (~110 MB)
├── src/
│   ├── config.py             # Konfiguratsiya va kalitlar
│   ├── db_engine.py          # Xavfsiz SQL ijrochisi va sxema ta'riflari
│   ├── entity_indexer.py     # Ikki tilli tovar, kompaniya, broker va hududlar rezolveri
│   ├── prompt_templates.py   # Text-to-SQL va Answer generation promptlari
│   ├── sql_generator.py      # LLM va deterministik Text-to-SQL generatori
│   ├── agent.py              # Asosiy AI Agent koordinatori
│   ├── bot.py                # Aiogram 3 Telegram-bot
│   └── web_app.py            # Streamlit Veb-servis interfeysi
├── tests/
│   └── test_queries.py       # 10 ta benchmark savollari avtotesti
├── .env.example              # Namuna konfiguratsiya fayli
├── run_bot.py                # Telegram botni ishga tushiruvchi
├── run_web.py                # Streamlit veb-ilovasini ishga tushiruvchi
└── README.md                 # To'liq hujjatlashtirish va tavsif
```
