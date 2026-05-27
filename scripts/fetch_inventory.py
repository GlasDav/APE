#!/usr/bin/env python3
import csv
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

TARGET_URL = "https://easyauto123.com.au/buy/used-cars?page=1&limit=20"
CDX_URL = "https://web.archive.org/cdx/search/cdx"
CSV_PATH = Path("data/inventory.csv")
JSON_PATH = Path("data/inventory.json")

PATTERNS = [
    re.compile(r"(\d{1,6})\s+used\s+cars\s+for\s+sale", re.IGNORECASE),
    re.compile(r"content=\"(\d{1,6})\s+used\s+cars\s+for\s+sale\"", re.IGNORECASE),
]


def fetch_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_inventory(html: str):
    for pattern in PATTERNS:
        m = pattern.search(html)
        if m:
            return int(m.group(1))
    return None


def load_existing():
    rows = {}
    if CSV_PATH.exists():
        with CSV_PATH.open() as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows[r["date"]] = {
                    "date": r["date"],
                    "inventory": int(r["inventory"]),
                    "source": r.get("source", "unknown"),
                    "snapshot": r.get("snapshot", "")
                }
    return rows


def get_wayback_snapshots():
    params = {
        "url": TARGET_URL,
        "output": "json",
        "fl": "timestamp,original,statuscode,mimetype",
        "filter": ["statuscode:200", "mimetype:text/html"],
        "collapse": "timestamp:8",  # one snapshot/day
        "from": "20200101",
    }
    query = urllib.parse.urlencode(params, doseq=True)
    payload = fetch_text(f"{CDX_URL}?{query}")
    data = json.loads(payload)
    return data[1:] if len(data) > 1 else []


def scrape_historical(existing):
    added = 0
    for ts, _orig, _status, _mime in get_wayback_snapshots():
        day = dt.datetime.strptime(ts[:8], "%Y%m%d").date().isoformat()
        if day in existing:
            continue
        archive_url = f"https://web.archive.org/web/{ts}/{TARGET_URL}"
        try:
            html = fetch_text(archive_url, timeout=20)
            inv = parse_inventory(html)
            if inv is None:
                continue
            existing[day] = {
                "date": day,
                "inventory": inv,
                "source": "wayback",
                "snapshot": ts,
            }
            added += 1
        except Exception:
            continue
    return added


def scrape_live(existing):
    today = dt.date.today().isoformat()
    html = fetch_text(TARGET_URL)
    inv = parse_inventory(html)
    if inv is None:
        raise RuntimeError("Could not parse live inventory count")
    existing[today] = {
        "date": today,
        "inventory": inv,
        "source": "live",
        "snapshot": "",
    }


def save(existing):
    rows = sorted(existing.values(), key=lambda x: x["date"])
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "inventory", "source", "snapshot"])
        writer.writeheader()
        writer.writerows(rows)

    with JSON_PATH.open("w") as f:
        json.dump(rows, f, indent=2)


if __name__ == "__main__":
    existing = load_existing()
    added = scrape_historical(existing)
    scrape_live(existing)
    save(existing)
    print(f"Saved {len(existing)} rows ({added} historical rows added this run).")
