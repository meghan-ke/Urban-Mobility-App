// api.js
const BASE_URL = "http://localhost:5000";

export async function fetchOverview() {
  const res = await fetch(`${BASE_URL}/api/stats/overview`);
  return res.json();
}

export async function fetchTrips(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE_URL}/api/trips?${query}`);
  return res.json();
}

export async function fetchByBorough() {
  const res = await fetch(`${BASE_URL}/api/stats/by-borough`);
  return res.json();
}

export async function fetchZonesGeoJSON() {
  const res = await fetch(`${BASE_URL}/api/zones/geojson`);
  return res.json();
}

export async function fetchTopPickups(limit = 10) {
  const res = await fetch(`${BASE_URL}/api/locations/top-pickup?limit=${limit}`);
  return res.json();

}
export async function fetchBoroughs() {
     const res = await fetch(`${BASE_URL}/api/locations/zones`);
      const data = await res.json();
       return [...new Set(data.map(z => z.Borough))].filter(Boolean).sort(); 
    }
