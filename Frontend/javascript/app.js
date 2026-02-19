// app.js
import { fetchTrips, fetchOverview, fetchByBorough, fetchZonesGeoJSON, fetchTopPickups } from "./api.js";
import { renderTripsTable, renderStats, renderBoroughChart, renderMap } from "./chart.js";

async function initDashboard() {
  try {
    // 1. Show overall statistics
    const overview = await fetchOverview();
    renderStats(overview);

    // 2. Show top trips
    const tripsData = await fetchTrips({ limit: 20, sort_by: "fare_amount" });
    renderTripsTable(tripsData.trips);

    // 3. Show borough chart
    const boroughStats = await fetchByBorough();
    renderBoroughChart(boroughStats);

    // 4. Show NYC taxi zones map
    const geojson = await fetchZonesGeoJSON();
    renderMap(geojson);

    // 5. Show top pickup locations
    const topPickups = await fetchTopPickups(10);
    console.log("Top Pickup Locations:", topPickups);
  } catch (error) {
    console.error("Error initializing dashboard:", error);
  }
}

// Initialize dashboard when page loads
window.addEventListener("DOMContentLoaded", initDashboard);
