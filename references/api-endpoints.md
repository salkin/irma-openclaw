# IRMA API Endpoints Reference

Base URL: `https://irma.suunnistusliitto.fi`

## Public HTML Pages (no authentication required)

| URL | Description |
|---|---|
| `/public/competitioncalendar/list` | Competition calendar browser |
| `/public/competition/view/{dayId}` | Single competition day page |
| `/public/club/list` | Club directory |
| `/public/person/view/{personId}` | Athlete profile page |
| `/public/ranking/list` | Rankings browser |

### Competition calendar query parameters

```
/public/competitioncalendar/list?year=upcoming&tab=competition&area=all&competition=ALL
```

| Parameter | Values | Description |
|---|---|---|
| `year` | `upcoming`, `2024`, `2025`, `2026` | Year filter |
| `tab` | `competition`, `training` | Event type |
| `area` | `all`, or area ID (see below) | District filter |
| `competition` | `ALL`, `OPEN`, `CLOSED` | Registration status |
| `discipline` | `SUUNNISTUS`, `HIIHTOSUUNNISTUS`, `MTB` | Discipline filter |

## JSON API Endpoints (requires session + CSRF token)

These endpoints are Vaadin Flow backend endpoints and require:
1. A valid session cookie obtained from the main HTML page
2. The `X-CSRF-TOKEN` header set to the CSRF token value embedded in the page HTML

### Competition Calendar

**Endpoint:** `POST /connect/CompetitionCalendarEndpoint/view`

**Headers:**
```
Content-Type: application/json
X-CSRF-TOKEN: <csrf_token>
Origin: https://irma.suunnistusliitto.fi
```

**Request body:**
```json
{
  "year": null,
  "month": "1",
  "upcoming": "ONE_WEEK",
  "disciplines": [],
  "areaId": null,
  "calendarType": "all",
  "competitionOpen": "ALL"
}
```

**Field values:**

| Field | Values | Description |
|---|---|---|
| `year` | `null` or `"2026"` | Year; `null` uses `upcoming` |
| `month` | `"1"`–`"12"` | Month number |
| `upcoming` | `"ONE_WEEK"`, `"ONE_MONTH"`, `"THREE_MONTHS"` | Lookahead when `year` is null |
| `disciplines` | `[]`, `["SUUNNISTUS"]`, `["HIIHTOSUUNNISTUS"]`, `["MTB"]` | Discipline filter |
| `areaId` | `null` or district ID integer | Geographic area filter |
| `calendarType` | `"all"`, `"competition"`, `"training"` | Event type |
| `competitionOpen` | `"ALL"`, `"OPEN"`, `"CLOSED"` | Registration status |

**Response:** JSON array of competition day objects:
```json
[
  {
    "dayId": 1234567,
    "competitionDayName": "Kisa 2026",
    "competitionDate": "2026-05-15",
    "organisingClubs": [{"name": "IF Femman", "id": 100}],
    "disciplines": ["SUUNNISTUS"],
    "registrationAllowed": true
  }
]
```

### Competition Day Details

**Endpoint:** `POST /connect/CompetitionEndpoint/viewCompetitionDay`

**Request body:**
```json
{
  "id": 1234567,
  "discipline": "SUUNNISTUS"
}
```

**Response:** Competition day detail object including:
- `registrationPeriod.firstRegistrationPeriodClosingDate` — entry deadline
- `classes` — list of available competition classes (sarjat)
- `startTime` — competition start time

### Person / Athlete Search

**Endpoint:** `POST /connect/PersonEndpoint/search` *(inferred from Vaadin pattern)*

**Request body:**
```json
{
  "searchTerm": "Firstname Lastname",
  "discipline": "SUUNNISTUS"
}
```

### Rankings

**Endpoint:** `POST /connect/RankingEndpoint/view` *(inferred from Vaadin pattern)*

**Request body:**
```json
{
  "discipline": "SUUNNISTUS",
  "year": "2026",
  "seriesId": null,
  "areaId": null
}
```

## CSV / Legacy Endpoints (no authentication required)

These older endpoints return data in CSV format and can be fetched with a simple HTTP GET.

### Competition Entries (Registrations)

```
GET /irma/haku/ilmoittautumiset?kilpailu={competitionId}&sarja=&seura=&kayttaja=
```

| Parameter | Description |
|---|---|
| `kilpailu` | Competition ID (integer) |
| `sarja` | Series/class filter (empty = all) |
| `seura` | Club filter (empty = all) |
| `kayttaja` | Person filter (empty = all) |

**Example:**
```bash
curl "https://irma.suunnistusliitto.fi/irma/haku/ilmoittautumiset?kilpailu=1208011&sarja=&seura=&kayttaja="
```

### Competition Results

```
GET /irma/haku/tulokset?kilpailu={competitionId}&sarja=&seura=
```

| Parameter | Description |
|---|---|
| `kilpailu` | Competition ID (integer) |
| `sarja` | Series/class filter (empty = all) |
| `seura` | Club filter (empty = all) |

**Example:**
```bash
curl "https://irma.suunnistusliitto.fi/irma/haku/tulokset?kilpailu=1208011&sarja=&seura="
```

## Finnish Orienteering Districts (Piirit)

| ID | District (Finnish) | District (English) |
|---|---|---|
| 1 | Helsingin piiri | Helsinki District |
| 2 | Uudenmaan piiri | Uusimaa District |
| 3 | Varsinais-Suomen piiri | Southwest Finland District |
| 4 | Satakunnan piiri | Satakunta District |
| 5 | Hämeen piiri | Häme District |
| 6 | Kaakkois-Suomen piiri | Southeast Finland District |
| 7 | Etelä-Savon piiri | South Savo District |
| 8 | Pohjois-Savon piiri | North Savo District |
| 9 | Pohjois-Karjalan piiri | North Karelia District |
| 10 | Keski-Suomen piiri | Central Finland District |
| 11 | Etelä-Pohjanmaan piiri | South Ostrobothnia District |
| 12 | Pohjanmaan piiri | Ostrobothnia District |
| 13 | Keski-Pohjanmaan piiri | Central Ostrobothnia District |
| 14 | Pohjois-Pohjanmaan piiri | North Ostrobothnia District |
| 15 | Kainuun piiri | Kainuu District |
| 16 | Lapin piiri | Lapland District |

## Common Competition Classes (Sarjat)

### Foot / Ski orienteering

| Class | Description |
|---|---|
| H21 | Men's elite (21+) |
| D21 | Women's elite (21+) |
| H20 | Men U20 |
| D20 | Women U20 |
| H18 | Men U18 |
| D18 | Women U18 |
| H16 | Men U16 |
| D16 | Women U16 |
| H40 | Men 40+ |
| D40 | Women 40+ |
| H50 | Men 50+ |
| D50 | Women 50+ |
| H60 | Men 60+ |
| D60 | Women 60+ |
| H70 | Men 70+ |
| D70 | Women 70+ |

*Note: H = Herrat (Men), D = Damer (Women)*

## Notes on Endpoint Discovery

IRMA is built with [Vaadin Flow](https://vaadin.com/flow). Backend endpoints follow the Vaadin convention:

```
/connect/{ServiceName}/{methodName}
```

If an endpoint returns a 401 or empty response, the session has expired — re-fetch the main page to refresh the CSRF token and session cookie.

To discover available endpoints, inspect the network requests in a browser's developer tools while navigating the IRMA website.
