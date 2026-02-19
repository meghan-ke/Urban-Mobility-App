// api.js
const BASE_URL = "http://localhost:5000";

// Simple cache to avoid repeated API calls
const cache = {
  overview: null,
  zones: null,
  boroughs: null,
  overviewTime: 0,
  zonesTime: 0
};

const CACHE_DURATION = 60000; // 60 seconds

export async function fetchOverview() {
  const now = Date.now();
  if (cache.overview && (now - cache.overviewTime) < CACHE_DURATION) {
    return cache.overview;
  }
  
  const res = await fetch(`${BASE_URL}/api/stats/overview`);
  const data = await res.json();
  cache.overview = data;
  cache.overviewTime = now;
  return data;
}

export async function fetchTrips(params = {}) {
  // Default limit to 20 to reduce load
  if (!params.limit) params.limit = 20;
  
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE_URL}/api/trips?${query}`);
  return res.json();
}

export async function fetchByBorough() {
  const res = await fetch(`${BASE_URL}/api/stats/by-borough`);
  return res.json();
}

export async function fetchZonesGeoJSON() {
  const now = Date.now();
  if (cache.zones && (now - cache.zonesTime) < CACHE_DURATION) {
    return cache.zones;
  }
  
  const res = await fetch(`${BASE_URL}/api/zones/geojson`);
  const data = await res.json();
  cache.zones = data;
  cache.zonesTime = now;
  return data;
}

export async function fetchTopPickups(limit = 10) {
  const res = await fetch(`${BASE_URL}/api/locations/top-pickup?limit=${limit}`);
  return res.json();
}

export async function fetchZones() {
  const now = Date.now();
  if (cache.boroughs && (now - cache.zonesTime) < CACHE_DURATION) {
    return cache.boroughs;
  }
  
  const res = await fetch(`${BASE_URL}/api/locations/zones`);
  const data = await res.json();
  cache.boroughs = Array.isArray(data) ? data : [];
  cache.zonesTime = now;
  return cache.boroughs;
}

export async function fetchZoneHeatmap() {
  const res = await fetch(`${BASE_URL}/api/zones/heatmap`);
  return res.json();
}

export async function fetchTipDistribution() {
  const res = await fetch(`${BASE_URL}/api/tips/distribution`);
  return res.json();
}
