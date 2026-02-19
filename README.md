# Urban-Mobility-App
# NYC Taxi Analytics Dashboard

A web-based dashboard for exploring and visualizing NYC Yellow Taxi trip data.

---

## Project Structure

```
project/
├── index.html              # Main HTML file — layout, tabs, containers
├── css/
│   └── style.css           # Dashboard styling
├── javascript/
│   ├── app.js              # Main logic — tab switching, data fetching, filters
│   ├── charts.js           # All rendering — charts, tables, map
│   └── api.js              # API calls and client-side caching
└── README.md
```

---

## How It Works

### `api.js`
Handles all communication with the Flask backend at `http://localhost:5000`. Includes a simple cache to avoid repeated API calls within 60 seconds.

| Function | Endpoint | Purpose |
|---|---|---|
| `fetchOverview()` | `/api/stats/overview` | Top-level stats (trips, fare, revenue) |
| `fetchByBorough()` | `/api/stats/by-borough` | Trip counts and averages per borough |
| `fetchTrips()` | `/api/trips` | Individual trip records with filters |
| `fetchZones()` | `/api/locations/zones` | Zone list for borough filter dropdown |
| `fetchZonesGeoJSON()` | `/api/zones/geojson` | GeoJSON for the map |
| `fetchZoneHeatmap()` | `/api/zones/heatmap` | Trip counts per zone for color-coding |

### `app.js`
Controls the dashboard lifecycle and tab behaviour.
- On load: fetches overview stats and populates filter dropdowns in parallel
- Tab switching: each tab loads its data only once (using a `Set` to track loaded tabs) — switching back does not re-fetch
- Filters: debounced 500ms so rapid changes don't spam the API
- Overview tab is excluded from the Set so it re-renders correctly when filters are applied

### `charts.js`
All rendering lives here. Each function is independent and can be called separately.
- `renderStats()` — updates the 3 stat cards at the top
- `renderBoroughChart()` — horizontal bar chart sorted by trip count
- `renderBoroughSummaryTable()` — table showing trips, avg fare, avg distance, avg duration per borough. Reuses the same data as the chart — no extra API call
- `renderTripsTable()` — recent trips table, capped at 10 rows for performance
- `renderGeoMap()` — Leaflet map color-coded by trip volume with a legend. Uses a HashMap (`tripsByZone`) for O(1) zone lookups

---

## Tabs

| Tab | What it shows |
|---|---|
| Overview | Borough bar chart, borough summary table, recent trips |
| Geographic Analysis | Interactive zone heatmap (color = trip volume) |
| Trip Explorer | Full filterable trips table |

---

## Running the App

### 1. Start the backend
```bash
python app.py
# or
flask run --port=5000
```

### 2. Open the frontend
Open `index.html` in your browser directly, or serve it with:
```bash
python -m http.server 8000
```
Then visit `http://localhost:8000`

---

## Data
Powered by NYC TLC Yellow Taxi Trip Records. The backend exposes pre-processed data via a REST API built with Flask.

Here is the Link to our team task sheet for colaboration on this summative project 
https://docs.google.com/spreadsheets/d/1GhrOVPYVF76xLCBHelFu07ePUgK41lswFS55tYiSPmo/edit?usp=sharing

