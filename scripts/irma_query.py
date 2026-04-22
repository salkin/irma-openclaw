#!/usr/bin/env python3
"""
IRMA Query Tool — Query Finnish Orienteering results, rankings, and competition calendar
from irma.suunnistusliitto.fi

Usage:
  python3 irma_query.py calendar [--discipline SUUNNISTUS|HIIHTOSUUNNISTUS|MTB]
                                  [--upcoming ONE_WEEK|ONE_MONTH|THREE_MONTHS]
                                  [--year YEAR] [--month MONTH] [--area-id ID]

  python3 irma_query.py person "Firstname Lastname" [--discipline SUUNNISTUS|...]

  python3 irma_query.py results --competition-id ID [--class SARJA] [--format csv|table]
  python3 irma_query.py results --day-id ID [--discipline SUUNNISTUS|...]

  python3 irma_query.py rankings [--discipline SUUNNISTUS|HIIHTOSUUNNISTUS|MTB]
                                  [--class H21|D21|...] [--year YEAR] [--top N]

Requirements:
  pip install requests
"""

import argparse
import csv
import io
import json
import re
import sys

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")

BASE_URL = "https://irma.suunnistusliitto.fi"
CALENDAR_PAGE = f"{BASE_URL}/public/competitioncalendar/list"
CALENDAR_API = f"{BASE_URL}/connect/CompetitionCalendarEndpoint/view"
COMPETITION_API = f"{BASE_URL}/connect/CompetitionEndpoint/viewCompetitionDay"
PERSON_SEARCH_API = f"{BASE_URL}/connect/PersonEndpoint/search"
RANKING_API = f"{BASE_URL}/connect/RankingEndpoint/view"
RESULTS_CSV_URL = f"{BASE_URL}/irma/haku/tulokset"
ENTRIES_CSV_URL = f"{BASE_URL}/irma/haku/ilmoittautumiset"

DISCIPLINE_LABELS = {
    "SUUNNISTUS": "Foot orienteering (Suunnistus)",
    "HIIHTOSUUNNISTUS": "Ski orienteering (Hiihtosuunnistus)",
    "MTB": "Mountain bike orienteering (MTB / Pyöräsuunnistus)",
}


class IRMASession:
    """Manages a browser-like session with CSRF token for IRMA JSON endpoints."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; irma-openclaw-skill/1.0)",
            "Accept": "application/json, text/html",
            "Origin": BASE_URL,
            "Referer": CALENDAR_PAGE,
        })
        self.csrf_token = None
        self._refresh_session()

    def _refresh_session(self):
        try:
            resp = self.session.get(CALENDAR_PAGE, timeout=15)
            resp.raise_for_status()
            match = re.search(r'name="_csrf"\s+content="([^"]+)"', resp.text)
            if match:
                self.csrf_token = match.group(1)
                self.session.headers["X-CSRF-TOKEN"] = self.csrf_token
            else:
                # Vaadin may also embed token in a different meta format
                match = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', resp.text)
                if match:
                    self.csrf_token = match.group(1)
                    self.session.headers["X-CSRF-TOKEN"] = self.csrf_token
        except requests.RequestException as e:
            sys.exit(f"Failed to connect to IRMA: {e}")

    def post_json(self, url, payload):
        try:
            resp = self.session.post(
                url, json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20,
            )
            if resp.status_code in (401, 403):
                self._refresh_session()
                resp = self.session.post(
                    url, json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20,
                )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            sys.exit(f"API request failed: {e}")
        except json.JSONDecodeError:
            sys.exit(f"Unexpected non-JSON response from {url}")

    def get_csv(self, url, params):
        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            sys.exit(f"CSV request failed: {e}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_calendar(args, irma):
    """Fetch and display competition calendar."""
    disciplines = [args.discipline] if args.discipline else []
    year = str(args.year) if args.year else None
    month = str(args.month) if args.month else None
    upcoming = args.upcoming if not year else None

    payload = {
        "year": year,
        "month": month or "1",
        "upcoming": upcoming,
        "disciplines": disciplines,
        "areaId": args.area_id,
        "calendarType": "all",
        "competitionOpen": "ALL",
    }

    print(f"Fetching competition calendar from IRMA...", file=sys.stderr)
    events = irma.post_json(CALENDAR_API, payload)

    if not events:
        print("No competitions found for the given filters.")
        return

    disc_label = DISCIPLINE_LABELS.get(args.discipline, "All disciplines") if args.discipline else "All disciplines"
    print(f"\n{'='*60}")
    print(f"IRMA Competition Calendar — {disc_label}")
    print(f"{'='*60}\n")

    for evt in events:
        day_id = evt.get("dayId", "?")
        name = evt.get("competitionDayName", "Unknown")
        date = evt.get("competitionDate", "?")
        clubs = ", ".join(c.get("name", "") for c in evt.get("organisingClubs", []))
        discs = ", ".join(evt.get("disciplines", []))
        reg_open = "Open" if evt.get("registrationAllowed") else "Closed"

        print(f"  {date}  {name}")
        print(f"    Organiser: {clubs}")
        print(f"    Discipline: {discs}  |  Registration: {reg_open}")
        print(f"    URL: {BASE_URL}/public/competition/view/{day_id}")
        print()

    print(f"Total: {len(events)} competition day(s)")


def cmd_person(args, irma):
    """Search for an athlete and display their results."""
    name = args.name
    discipline = args.discipline or ""

    print(f"Searching IRMA for athlete: '{name}'...", file=sys.stderr)

    payload = {
        "searchTerm": name,
        "discipline": discipline,
    }

    try:
        results = irma.post_json(PERSON_SEARCH_API, payload)
    except SystemExit:
        # Endpoint may not be available; fall back to public page guidance
        print(f"\nPerson search endpoint not directly accessible.")
        print(f"Browse athlete profiles at:")
        print(f"  {BASE_URL}/public/person/list")
        print(f"\nOr search the competition entries for '{name}':")
        print(f"  {BASE_URL}/irma/haku/ilmoittautumiset?kilpailu=&sarja=&seura=&kayttaja={name.replace(' ', '+')}")
        return

    if not results:
        print(f"No athletes found matching '{name}'.")
        return

    print(f"\n{'='*60}")
    print(f"Athletes matching '{name}'")
    print(f"{'='*60}\n")

    for person in results:
        person_id = person.get("id", "?")
        full_name = person.get("name", "Unknown")
        club = person.get("club", {}).get("name", "?")
        print(f"  {full_name}  ({club})")
        print(f"    Profile: {BASE_URL}/public/person/view/{person_id}")
        print()


def cmd_results(args, irma):
    """Fetch and display results for a specific competition."""
    if args.day_id:
        # Fetch day details via JSON API
        print(f"Fetching competition day {args.day_id}...", file=sys.stderr)
        payload = {
            "id": args.day_id,
            "discipline": args.discipline or "SUUNNISTUS",
        }
        detail = irma.post_json(COMPETITION_API, payload)

        print(f"\n{'='*60}")
        print(f"Competition Day Details (ID: {args.day_id})")
        print(f"{'='*60}\n")
        print(json.dumps(detail, indent=2, ensure_ascii=False))
        return

    if args.competition_id:
        comp_id = args.competition_id
        params = {
            "kilpailu": comp_id,
            "sarja": args.cls or "",
            "seura": "",
        }

        print(f"Fetching results for competition {comp_id}...", file=sys.stderr)
        csv_data = irma.get_csv(RESULTS_CSV_URL, params)

        if args.format == "csv":
            print(csv_data)
            return

        # Parse and display as table
        reader = csv.DictReader(io.StringIO(csv_data), delimiter=";")
        rows = list(reader)

        if not rows:
            print(f"No results found for competition {comp_id}.")
            return

        print(f"\n{'='*60}")
        print(f"Results — Competition {comp_id}")
        if args.cls:
            print(f"Class: {args.cls}")
        print(f"{'='*60}\n")

        headers = reader.fieldnames or []
        col_widths = {h: max(len(h), max((len(str(r.get(h, ""))) for r in rows), default=0)) for h in headers}
        header_line = "  ".join(h.ljust(col_widths[h]) for h in headers)
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            print("  ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers))

        print(f"\nTotal: {len(rows)} result(s)")
        return

    print("Error: provide --day-id or --competition-id", file=sys.stderr)
    sys.exit(1)


def cmd_rankings(args, irma):
    """Fetch and display orienteering rankings."""
    discipline = args.discipline or "SUUNNISTUS"
    year = str(args.year) if args.year else None

    print(f"Fetching {DISCIPLINE_LABELS.get(discipline, discipline)} rankings...", file=sys.stderr)

    payload = {
        "discipline": discipline,
        "year": year,
        "seriesId": None,
        "areaId": None,
    }
    if args.cls:
        payload["seriesName"] = args.cls

    try:
        rankings = irma.post_json(RANKING_API, payload)
    except SystemExit:
        print(f"\nRanking endpoint not directly accessible via this tool.")
        print(f"Browse rankings at:")
        print(f"  {BASE_URL}/public/ranking/list")
        return

    if not rankings:
        print("No ranking data returned.")
        return

    top_n = args.top or 20

    print(f"\n{'='*60}")
    print(f"Rankings — {DISCIPLINE_LABELS.get(discipline, discipline)}")
    if args.cls:
        print(f"Class: {args.cls}")
    print(f"{'='*60}\n")
    print(f"  {'#':<5}{'Name':<30}{'Club':<25}{'Points'}")
    print(f"  {'-'*5}{'-'*30}{'-'*25}{'-'*10}")

    for i, entry in enumerate(rankings[:top_n], 1):
        rank = entry.get("rank", i)
        name = entry.get("name", "Unknown")
        club = entry.get("club", {}).get("name", "?") if isinstance(entry.get("club"), dict) else entry.get("club", "?")
        points = entry.get("points", "?")
        print(f"  {str(rank):<5}{name:<30}{club:<25}{points}")

    print(f"\nShowing top {min(top_n, len(rankings))} of {len(rankings)} ranked athlete(s)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Query IRMA — Finnish Orienteering results system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # calendar
    cal = sub.add_parser("calendar", help="Browse competition calendar")
    cal.add_argument("--discipline", choices=["SUUNNISTUS", "HIIHTOSUUNNISTUS", "MTB"],
                     help="Filter by discipline")
    cal.add_argument("--upcoming", default="ONE_MONTH",
                     choices=["ONE_WEEK", "ONE_MONTH", "THREE_MONTHS"],
                     help="Lookahead window (used when --year is not set)")
    cal.add_argument("--year", type=int, help="Year (e.g. 2026)")
    cal.add_argument("--month", type=int, help="Month number 1–12")
    cal.add_argument("--area-id", type=int, dest="area_id",
                     help="Finnish orienteering district ID (1–16)")

    # person
    per = sub.add_parser("person", help="Search athlete results")
    per.add_argument("name", help="Athlete name (partial match)")
    per.add_argument("--discipline", choices=["SUUNNISTUS", "HIIHTOSUUNNISTUS", "MTB"],
                     help="Filter by discipline")

    # results
    res = sub.add_parser("results", help="Fetch competition results")
    res.add_argument("--day-id", type=int, dest="day_id",
                     help="Competition day ID (from calendar)")
    res.add_argument("--competition-id", type=int, dest="competition_id",
                     help="Competition ID for CSV results download")
    res.add_argument("--discipline", choices=["SUUNNISTUS", "HIIHTOSUUNNISTUS", "MTB"],
                     default="SUUNNISTUS", help="Discipline (for day-id queries)")
    res.add_argument("--class", dest="cls", help="Class/series filter (e.g. H21, D21)")
    res.add_argument("--format", choices=["table", "csv"], default="table",
                     help="Output format for CSV downloads")

    # rankings
    rnk = sub.add_parser("rankings", help="View orienteering rankings")
    rnk.add_argument("--discipline", choices=["SUUNNISTUS", "HIIHTOSUUNNISTUS", "MTB"],
                     help="Discipline (default: SUUNNISTUS)")
    rnk.add_argument("--class", dest="cls", help="Class/series filter (e.g. H21, D21)")
    rnk.add_argument("--year", type=int, help="Year (default: current)")
    rnk.add_argument("--top", type=int, default=20, help="Number of top entries to show")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    irma = IRMASession()

    if args.command == "calendar":
        cmd_calendar(args, irma)
    elif args.command == "person":
        cmd_person(args, irma)
    elif args.command == "results":
        cmd_results(args, irma)
    elif args.command == "rankings":
        cmd_rankings(args, irma)


if __name__ == "__main__":
    main()
