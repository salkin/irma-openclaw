# IRMA Session Setup

IRMA uses Vaadin Flow, which requires a browser-like session for its JSON API endpoints. This guide explains how to set up and maintain a valid session.

## How it works

1. The IRMA web application embeds a CSRF token in the HTML of the main page.
2. JSON API endpoints require this token in the `X-CSRF-TOKEN` header.
3. A session cookie (typically `JSESSIONID`) must be sent with each request.
4. Both the token and cookie are obtained by loading any public IRMA page.

## Step-by-step

### 1. Fetch a page and extract the CSRF token

```bash
COOKIES_FILE="/tmp/irma_cookies.txt"
INITIAL_URL="https://irma.suunnistusliitto.fi/public/competitioncalendar/list?year=upcoming&tab=competition&area=all&competition=ALL"

# Fetch page, save cookies, extract CSRF token
CSRF_TOKEN=$(curl -s -L \
  -c "$COOKIES_FILE" \
  -A "Mozilla/5.0" \
  "$INITIAL_URL" \
  | grep -oP 'name="_csrf" content="\K[^"]+')

echo "CSRF token: $CSRF_TOKEN"
```

### 2. Verify the session works

```bash
TEST_RESPONSE=$(curl -s -X POST \
  "https://irma.suunnistusliitto.fi/connect/CompetitionCalendarEndpoint/view" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-TOKEN: $CSRF_TOKEN" \
  -H "Origin: https://irma.suunnistusliitto.fi" \
  -H "Referer: $INITIAL_URL" \
  -b "$COOKIES_FILE" \
  -d '{"year":null,"month":"1","upcoming":"ONE_WEEK","disciplines":[],"areaId":null,"calendarType":"all","competitionOpen":"ALL"}')

# Should return a JSON array; if empty or error, refresh session
echo "$TEST_RESPONSE" | python3 -m json.tool | head -20
```

### 3. Refresh session when needed

Sessions expire after inactivity. Signs of an expired session:
- Empty JSON array `[]` returned from calendar endpoint
- HTTP 401 or 403 response
- Response contains HTML login page instead of JSON

To refresh, simply repeat step 1.

## Python session management

The `scripts/irma_query.py` script handles session management automatically:

```python
import requests
import re

class IRMASession:
    BASE_URL = "https://irma.suunnistusliitto.fi"
    INITIAL_URL = f"{BASE_URL}/public/competitioncalendar/list"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": self.BASE_URL,
        })
        self.csrf_token = None
        self._refresh_session()

    def _refresh_session(self):
        resp = self.session.get(self.INITIAL_URL)
        match = re.search(r'name="_csrf"\s+content="([^"]+)"', resp.text)
        if match:
            self.csrf_token = match.group(1)
            self.session.headers["X-CSRF-TOKEN"] = self.csrf_token

    def post(self, path, payload):
        url = f"{self.BASE_URL}{path}"
        resp = self.session.post(url, json=payload)
        if resp.status_code in (401, 403) or not resp.text.startswith("["):
            self._refresh_session()
            resp = self.session.post(url, json=payload)
        return resp.json()
```

## Notes

- The CSRF token is embedded as `<meta name="_csrf" content="...">` in the page HTML.
- Session cookies are handled automatically by the `requests.Session` object.
- The Vaadin Flow framework may also use `X-CSRF-TOKEN` values embedded in JavaScript bundles; the meta tag approach is more reliable.
- Do not make excessive requests — cache results where possible to avoid overloading the IRMA server.
