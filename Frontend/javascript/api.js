// app.js
import { fetchTrips, fetchOverview, fetchByBorough, fetchZonesGeoJSON } from "./api.js";
import { renderTripsTable, renderStats, renderBoroughChart, renderMap } from "./chart.js";

let mapInstance = null;   // Keep track of map instance
let boroughChartInstance = null; // Keep track of chart instance

// Get filter elements
const boroughFilter = document.getElementById("boroughFilter");
const hourFilter = document.getElementById("hourFilter");
const minFareInput = document.getElementById("minFare");
const maxFareInput = document.getElementById("maxFare");
const applyFiltersBtn = document.getElementById("applyFilters");

// Load dashboard data
async function loadDashboard(filters = {}) {
  try {
    // 1️⃣ Stats
    const overview = await fetchOverview();
    renderStats(overview);

    // 2️⃣ Trips table
    const tripsData = await fetchTrips({ limit: 20, ...filters });
    renderTripsTable(tripsData.trips);

    // 3️⃣ Borough chart
    const boroughData = await fetchByBorough();
    if (boroughChartInstance) boroughChartInstance.destroy(); // Destroy old chart
    boroughChartInstance = renderBoroughChart(boroughData);

    // 4️⃣ Map
    const geojson = await fetchZonesGeoJSON();
    if (!mapInstance) {
      mapInstance = renderMap(geojson);
    }
  } catch (error) {
    console.error("Error loading dashboard:", error);
  }
}

// Apply filters when button is clicked
applyFiltersBtn.addEventListener("click", () => {
  const filters = {};
  if (boroughFilter.value) filters.borough = boroughFilter.value;
  if (hourFilter.value) filters.hour = hourFilter.value;
  if (minFareInput.value) filters.min_fare = parseFloat(minFareInput.value);
  if (maxFareInput.value) filters.max_fare = parseFloat(maxFareInput.value);

  loadDashboard(filters);
});

// Initialize dashboard on page load
window.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});
