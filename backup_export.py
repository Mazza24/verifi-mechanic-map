#!/usr/bin/env python3
"""Export the Supabase mechanics + change_log tables to CSV for nightly backup.

Reads SB_URL and SB_KEY from the environment. The nightly run also serves as
the free-tier keep-alive ping.
"""
import csv, json, os, urllib.request

SB_URL = os.environ['SB_URL'].rstrip('/')
SB_KEY = os.environ['SB_KEY']


def fetch_all(table, order):
    rows, start = [], 0
    while True:
        req = urllib.request.Request(
            f'{SB_URL}/rest/v1/{table}?select=*&order={order}',
            headers={'apikey': SB_KEY, 'Authorization': f'Bearer {SB_KEY}',
                     'Range': f'{start}-{start + 999}'})
        with urllib.request.urlopen(req, timeout=30) as r:
            page = json.load(r)
        rows.extend(page)
        if len(page) < 1000:
            return rows
        start += 1000


def write_csv(path, rows):
    if not rows:
        return
    cols = sorted(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([json.dumps(r[c], ensure_ascii=False) if isinstance(r[c], (dict, list)) else r[c] for c in cols])


os.makedirs('backup', exist_ok=True)
mechanics = fetch_all('mechanics', 'id')
write_csv('backup/mechanics.csv', mechanics)
log = fetch_all('change_log', 'id')
write_csv('backup/change_log.csv', log)
print(f'backed up {len(mechanics)} mechanics, {len(log)} change_log rows')
