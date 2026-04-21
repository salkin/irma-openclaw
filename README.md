# irma-openclaw

An [OpenClaw](https://github.com/openakita/openakita) skill for querying [IRMA](https://irma.suunnistusliitto.fi/) — the Finnish Orienteering Federation's competition management and results system.

## What it does

- **Competition calendar** — list upcoming orienteering events, filterable by discipline and area
- **Person / athlete search** — find results for a specific athlete
- **Results** — fetch race results for a specific competition (CSV and table formats)
- **Rankings** — view orienteering ranking tables

Supports all three orienteering disciplines:
- 🏃 Foot orienteering (Suunnistus)
- ⛷️ Ski orienteering (Hiihtosuunnistus)
- 🚵 Mountain bike orienteering (MTB / Pyöräsuunnistus)

## Installation

```bash
# Install the skill
npx skills add salkin/irma-openclaw

# Install Python dependency for the query script
pip install requests beautifulsoup4
```

## Quick start

```bash
# Upcoming competitions (all disciplines)
python3 scripts/irma_query.py calendar

# Foot orienteering competitions next month
python3 scripts/irma_query.py calendar --discipline SUUNNISTUS --upcoming ONE_MONTH

# Ski orienteering competitions in 2026
python3 scripts/irma_query.py calendar --discipline HIIHTOSUUNNISTUS --year 2026

# Search athlete results
python3 scripts/irma_query.py person "Matti Meikäläinen"

# Results for a specific competition (CSV ID)
python3 scripts/irma_query.py results --competition-id 1208011

# Top 10 men's elite rankings (foot orienteering)
python3 scripts/irma_query.py rankings --discipline SUUNNISTUS --class H21 --top 10

# Mountain bike orienteering rankings
python3 scripts/irma_query.py rankings --discipline MTB
```

## Files

| File | Description |
|---|---|
| `SKILL.md` | OpenClaw skill definition (agent instructions) |
| `scripts/irma_query.py` | Python CLI for querying the IRMA API |
| `references/api-endpoints.md` | Full IRMA API endpoint reference |
| `references/session-setup.md` | Guide to IRMA session and CSRF handling |

## Data source

All data is sourced from [irma.suunnistusliitto.fi](https://irma.suunnistusliitto.fi), operated by [Suomen Suunnistusliitto (Orienteering Finland)](https://www.suunnistusliitto.fi).
