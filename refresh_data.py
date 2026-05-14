#!/usr/bin/env python3
"""Refresh prayer_times.json + prayer_times.csv from towerhamletsmosques.co.uk.

Usage:
  refresh_data.py                # scrape the current calendar year
  refresh_data.py 2027           # scrape a specific year
  refresh_data.py --append 2027  # scrape and merge with existing data

After writing, sends SIGHUP to the running service so it picks up new times without restart.
Requires: requests, beautifulsoup4 (auto-installed via pip if missing).
"""
from __future__ import annotations

import argparse
import csv
import json
import signal
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_FILE = ROOT / "prayer_times.json"
CSV_FILE = ROOT / "prayer_times.csv"
PID_FILE = ROOT / "logs" / "adhan.pid"  # written by service via launchd

PRAYER_ORDER = ("Fajr", "Sunrise", "Zuhr", "Asr", "Maghrib", "Isha")


def ensure_deps() -> None:
    try:
        import requests  # noqa: F401
        import bs4  # noqa: F401
    except ImportError:
        print("Installing requests + beautifulsoup4 ...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests", "beautifulsoup4"])


def fetch_day(month_abbr: str, day: int) -> dict | None:
    import requests
    url = "https://www.towerhamletsmosques.co.uk/wp-content/themes/squared/masajid-files/request.php"
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.towerhamletsmosques.co.uk",
        "referer": "https://www.towerhamletsmosques.co.uk/salah-beginning-times/",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    try:
        r = requests.post(url, headers=headers, params={"showJumma": "false"},
                          data={"selectedMonth": month_abbr, "selectedDay": str(day)}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  fetch failed {month_abbr} {day}: {e}", file=sys.stderr)
        return None


def to_24h(time_str: str, prayer: str) -> str:
    if not time_str or ":" not in time_str:
        return time_str
    h, m = time_str.split(":", 1)
    h = int(h)
    if prayer in ("Fajr", "Sunrise"):
        if h == 12:
            h = 0
    else:
        if h < 12:
            h += 12
    return f"{h:02d}:{m}"


def parse_table(html: str) -> dict[str, str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, str] = {}
    for row in soup.find_all("tr", class_="active"):
        if "mithl" in row.get("class", []):
            continue
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        name_span = cells[0].find("span")
        name = (name_span.get_text(strip=True) if name_span else cells[0].get_text(strip=True))
        jamaah_span = cells[2].find("span")
        if not jamaah_span:
            continue
        out[name] = to_24h(jamaah_span.get_text(strip=True), name)
    return out


def scrape_date(month: int, day: int, year: int) -> dict | None:
    month_abbr = datetime(year, month, day).strftime("%b")
    data = fetch_day(month_abbr, day)
    if not data or "salah" not in data:
        return None
    times = parse_table(data["salah"])
    if not times:
        return None
    return {
        "date": f"{year}-{month:02d}-{day:02d}",
        "month": month_abbr,
        "day": day,
        "prayer_times": times,
    }


def scrape_year(year: int, workers: int = 10) -> list[dict]:
    dates: list[tuple[int, int]] = []
    d = datetime(year, 1, 1)
    end = datetime(year, 12, 31)
    while d <= end:
        dates.append((d.month, d.day))
        d += timedelta(days=1)

    print(f"Scraping {len(dates)} days for {year} ...", file=sys.stderr)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(scrape_date, m, day, year): (m, day) for m, day in dates}
        done = 0
        for fut in as_completed(futures):
            done += 1
            try:
                r = fut.result()
                if r:
                    results.append(r)
            except Exception as e:
                m, day = futures[fut]
                print(f"  error {m}/{day}: {e}", file=sys.stderr)
            if done % 30 == 0 or done == len(dates):
                print(f"  {done}/{len(dates)}", file=sys.stderr)

    results.sort(key=lambda x: x["date"])
    missing = len(dates) - len(results)
    if missing:
        print(f"WARN: {missing} day(s) missing", file=sys.stderr)
    return results


def write_csv(data: list[dict]) -> None:
    with CSV_FILE.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"])
        for d in data:
            p = d["prayer_times"]
            w.writerow([
                d["date"], p.get("Fajr", ""), p.get("Sunrise", ""), p.get("Zuhr", ""),
                p.get("Asr", ""), p.get("Maghrib", ""), p.get("Isha", ""),
            ])


def signal_running_service() -> None:
    """SIGHUP the daemon so it reloads the new data without a restart."""
    try:
        out = subprocess.check_output(
            ["launchctl", "list", "com.homeserver.adhan"], stderr=subprocess.DEVNULL, text=True
        )
        pid = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('"PID"'):
                pid = int(line.split("=")[1].rstrip(";").strip())
                break
        if pid:
            import os
            os.kill(pid, signal.SIGHUP)
            print(f"sent SIGHUP to running service (pid {pid})")
        else:
            print("service not running — new data will load on next start")
    except subprocess.CalledProcessError:
        print("service not loaded — new data will load on next start")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("year", nargs="?", type=int, default=datetime.now().year)
    ap.add_argument("--append", action="store_true",
                    help="merge new year into existing JSON instead of replacing")
    args = ap.parse_args()

    ensure_deps()

    new_data = scrape_year(args.year)
    if not new_data:
        print("no data scraped, aborting", file=sys.stderr)
        return 1

    if args.append and JSON_FILE.exists():
        with JSON_FILE.open() as f:
            existing = json.load(f)
        by_date = {d["date"]: d for d in existing}
        for d in new_data:
            by_date[d["date"]] = d
        merged = sorted(by_date.values(), key=lambda x: x["date"])
    else:
        merged = new_data

    with JSON_FILE.open("w") as f:
        json.dump(merged, f, indent=2)
    write_csv(merged)
    print(f"wrote {len(merged)} days to {JSON_FILE.name} and {CSV_FILE.name}")

    signal_running_service()
    return 0


if __name__ == "__main__":
    sys.exit(main())
