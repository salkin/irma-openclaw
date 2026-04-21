---
name: irma
description: "Query the Finnish Orienteering Federation's IRMA system at irma.suunnistusliitto.fi. Look up orienteering competition results, search athlete/person results, get ranking statistics, and browse the competition calendar. Supports all orienteering disciplines: foot orienteering (suunnistus), ski orienteering (hiihtosuunnistus), and mountain bike orienteering (MTB). Triggers: irma, orienteering results, suunnistus tulokset, ski orienteering results, MTB orienteering results, Finnish orienteering, person results orienteering, orienteering rankings, athlete results Finland, competition calendar Finland, suunnistusliitto, Orienteering Finland results"
allowed-tools: Bash(python3 *), Bash(curl *)
---

# IRMA — Finnish Orienteering Results & Rankings

Query competition results, athlete statistics, and rankings from the Finnish Orienteering Federation's IRMA system at [irma.suunnistusliitto.fi](https://irma.suunnistusliitto.fi).

## Overview

IRMA (Information and Result Management for Athletics) is the official system used by Orienteering Finland (Suomen Suunnistusliitto). It covers:

| Discipline | Finnish name | Code |
|---|---|---|
| Foot orienteering | Suunnistus | `SUUNNISTUS` |
| Ski orienteering | Hiihtosuunnistus | `HIIHTOSUUNNISTUS` |
| Mountain bike orienteering | Pyöräsuunnistus | `MTB` |

## Quick Start

The IRMA web application is Vaadin-based and requires a browser session with CSRF token for its JSON endpoints. The helper script at `scripts/irma_query.py` handles this automatically.

### Installation

```bash
pip install requests beautifulsoup4
```

## Usage

### 1. List upcoming competitions (all disciplines)

```bash
python3 scripts/irma_query.py calendar
```

### 2. List competitions by discipline

```bash
# Foot orienteering
python3 scripts/irma_query.py calendar --discipline SUUNNISTUS

# Ski orienteering
python3 scripts/irma_query.py calendar --discipline HIIHTOSUUNNISTUS

# Mountain bike orienteering
python3 scripts/irma_query.py calendar --discipline MTB
```

### 3. Filter by time range

```bash
# Upcoming (next 7 days)
python3 scripts/irma_query.py calendar --upcoming ONE_WEEK

# Next month
python3 scripts/irma_query.py calendar --upcoming ONE_MONTH

# Specific year and month (e.g. June 2026)
python3 scripts/irma_query.py calendar --year 2026 --month 6
```

### 4. Search person / athlete results

```bash
# Search by athlete name (partial match supported)
python3 scripts/irma_query.py person "Firstname Lastname"

# Search by athlete name within a specific discipline
python3 scripts/irma_query.py person "Firstname Lastname" --discipline SUUNNISTUS
```

### 5. Get results for a specific competition

```bash
# First find the competition day ID from the calendar, then:
python3 scripts/irma_query.py results --day-id 1234567

# Download results as CSV
python3 scripts/irma_query.py results --competition-id 1208011 --format csv
```

### 6. Get rankings

```bash
# General rankings (current year)
python3 scripts/irma_query.py rankings

# Rankings by discipline
python3 scripts/irma_query.py rankings --discipline SUUNNISTUS

# Rankings filtered by class/series (sarja)
python3 scripts/irma_query.py rankings --discipline SUUNNISTUS --class H21

# Ski orienteering rankings
python3 scripts/irma_query.py rankings --discipline HIIHTOSUUNNISTUS
```

### 7. Browse competition calendar via public URL

Open the calendar directly:

```bash
# All competitions
curl -s "https://irma.suunnistusliitto.fi/public/competitioncalendar/list?year=upcoming&tab=competition&area=all&competition=ALL"
```

## API Endpoints Reference

See [references/api-endpoints.md](references/api-endpoints.md) for full API documentation.

### Core endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/connect/CompetitionCalendarEndpoint/view` | POST JSON | Competition calendar (requires session) |
| `/connect/CompetitionEndpoint/viewCompetitionDay` | POST JSON | Single competition day details |
| `/irma/haku/ilmoittautumiset` | GET CSV | Entries/registrations for a competition |
| `/irma/haku/tulokset` | GET CSV | Results for a competition |
| `/public/competitioncalendar/list` | GET HTML | Calendar browser UI |
| `/public/competition/view/{id}` | GET HTML | Single competition page |
| `/public/club/list` | GET HTML | Club directory |

### Session setup (for JSON endpoints)

The JSON endpoints require a browser-like session with a CSRF token:

```bash
# Step 1: Fetch the main page and capture CSRF token + cookies
curl -s -c /tmp/irma_cookies.txt \
  "https://irma.suunnistusliitto.fi/public/competitioncalendar/list?year=upcoming&tab=competition&area=all&competition=ALL" \
  | grep -oP 'name="_csrf" content="\K[^"]+'
```

See [references/session-setup.md](references/session-setup.md) for full session management details.

### Calendar API payload

```bash
# POST to competition calendar endpoint
curl -s -X POST \
  "https://irma.suunnistusliitto.fi/connect/CompetitionCalendarEndpoint/view" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-TOKEN: $CSRF_TOKEN" \
  -H "Origin: https://irma.suunnistusliitto.fi" \
  -b /tmp/irma_cookies.txt \
  -d '{
    "year": null,
    "month": "1",
    "upcoming": "ONE_WEEK",
    "disciplines": ["SUUNNISTUS"],
    "areaId": null,
    "calendarType": "all",
    "competitionOpen": "ALL"
  }' | python3 -m json.tool
```

## Output Interpretation

### Competition calendar fields

| Field | Description |
|---|---|
| `competitionDayName` | Name of the competition day |
| `competitionDate` | Date (ISO format) |
| `dayId` | ID used for detail queries |
| `organisingClubs` | List of organising clubs |
| `disciplines` | Orienteering discipline(s) |
| `registrationAllowed` | Whether entries are still open |

### Results CSV columns

The CSV from `/irma/haku/tulokset` contains:
- Competitor number, name, club, series/class, result time, position, points

### Rankings fields

| Field | Description |
|---|---|
| `rank` | Overall ranking position |
| `name` | Athlete full name |
| `club` | Club name |
| `points` | Ranking points (pisteet) |
| `series` | Age/gender class (sarja) |

## Examples

### Find all ski orienteering competitions in 2026

```bash
python3 scripts/irma_query.py calendar --discipline HIIHTOSUUNNISTUS --year 2026
```

### Find results for a specific athlete across all competitions

```bash
python3 scripts/irma_query.py person "Matti Meikäläinen"
```

### Get top 10 rankings for men's elite (H21) foot orienteering

```bash
python3 scripts/irma_query.py rankings --discipline SUUNNISTUS --class H21 --top 10
```

## Notes

- IRMA uses Vaadin Flow, so JSON endpoints require a valid session with CSRF token; the helper script manages this automatically.
- Results CSVs are available without authentication.
- The `disciplines` filter accepts a list; pass `[]` for all disciplines.
- Area IDs correspond to Finnish orienteering districts (piirit); see [references/api-endpoints.md](references/api-endpoints.md) for the list.
- Competition day IDs (`dayId`) are used in detail queries; competition IDs (`kilpailu`) are used in CSV result downloads.

## Related Links

- [IRMA competition calendar](https://irma.suunnistusliitto.fi/public/competitioncalendar/list)
- [Orienteering Finland (Suomen Suunnistusliitto)](https://www.suunnistusliitto.fi)
- [API endpoints reference](references/api-endpoints.md)
- [Session setup guide](references/session-setup.md)
