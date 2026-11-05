#!/usr/bin/env python3
"""
UZEX AI Analyst - Server Question Audit Viewer
Foydalanuvchilar va hakamlar bergan savollarni serverda real vaqtda ko'rish skripti.

Ishlatish:
  python3 view_queries.py           (Oxirgi 15 ta savolni ko'rish)
  python3 view_queries.py -n 50     (Oxirgi 50 ta savolni ko'rish)
  python3 view_queries.py --watch   (Jonli efir: yangi savol tushishi bilan ekranga chiqarish)
"""

import sys
import time
import sqlite3
import argparse
from pathlib import Path

# Windows va Linux terminallarida Unicode/Emoji xatolik bermasligi uchun
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

DB_PATH = Path(__file__).resolve().parent / "db" / "history.db"

def print_row(row):
    qid, created_at, q, lang, ans, sql, latency, status, rows = row
    status_icon = "🟢" if status == "success" else ("🔴" if status == "error" else "🟡")
    
    print("=" * 80)
    print(f"{status_icon} ID: #{qid} | ⏰ Vaqt: {created_at} UTC | Til: {lang} | Status: {status} | Latency: {latency:.1f}ms")
    print(f"❓ SAVOL: {q}")
    if ans:
        # 160 ta belgidan oshsa qisqartirish yoki to'liq ko'rsatish
        short_ans = ans.strip().replace("\n", " ")
        if len(short_ans) > 220:
            short_ans = short_ans[:220] + "..."
        print(f"💡 JAVOB: {short_ans}")
    if sql:
        print(f"⚡ SQL:   {sql}")

def show_recent(limit=15):
    if not DB_PATH.exists():
        print(f"Baza topilmadi: {DB_PATH}")
        return

    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""
        SELECT id, created_at, question, detected_lang, answer, 
               executed_sql, execution_time_ms, status, row_count
        FROM query_history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    con.close()

    if not rows:
        print("Hozircha hech qanday savol berilmagan.")
        return

    print(f"\n📋 OXIRGI {len(rows)} TA BERILGAN SAVOL:\n")
    for row in reversed(rows):
        print_row(row)
    print("=" * 80 + "\n")

def watch_live():
    if not DB_PATH.exists():
        print(f"Baza topilmadi: {DB_PATH}. Savol berilishini kutilmoqda...")

    print("\n🔴 JONLI KUZATUV REJIMI (LIVE STREAM) YOQILDI")
    print("Foydalanuvchi yoki hakam saytda savol yozishi bilan bu yerda chiqadi.")
    print("To'xtatish uchun: Ctrl + C bosing.\n")

    last_seen_id = 0
    if DB_PATH.exists():
        con = sqlite3.connect(DB_PATH)
        max_id = con.execute("SELECT max(id) FROM query_history").fetchone()[0]
        con.close()
        last_seen_id = max_id or 0

    while True:
        try:
            if DB_PATH.exists():
                con = sqlite3.connect(DB_PATH)
                rows = con.execute("""
                    SELECT id, created_at, question, detected_lang, answer, 
                           executed_sql, execution_time_ms, status, row_count
                    FROM query_history
                    WHERE id > ?
                    ORDER BY id ASC
                """, (last_seen_id,)).fetchall()
                con.close()

                for row in rows:
                    print_row(row)
                    last_seen_id = row[0]
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nKuzatuv to'xtatildi.")
            break
        except Exception as e:
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="UZEX Savollar Auditini ko'rish")
    parser.add_argument("-n", "--limit", type=int, default=15, help="Nechta oxirgi savolni ko'rish (default: 15)")
    parser.add_argument("-w", "--watch", action="store_true", help="Jonli rejimda real vaqtda kuzatish")
    args = parser.parse_args()

    if args.watch:
        watch_live()
    else:
        show_recent(args.limit)

if __name__ == "__main__":
    main()
