// app.js
import { 
  fetchTrips, fetchOverview, fetchByBorough, fetchZonesGeoJSON, 
  fetchTopPickups, fetchZones 
} from "./api.js";
import { 
  renderTripsTable, renderStats, renderBoroughChart, renderMap
} from "./charts.js";
const loadedTabs = new Set();
// Global state
let currentFilters = {
  borough: "",
  hour: "",
  minFare: "",
  maxFare: "",
  limit: 20,
  offset: 0
};

let filterTimeout;
let isLoading = false;
let hasActiveFilters = false; // Track if filters are currently applied

async function initDashboard() {
  try {
    // Load critical data first
    await Promise.all([
      loadOverview(),
      populateFilters()
    ]);
    
    // Then load overview tab content
    await loadOverviewTab();
  } catch (error) {
    console.error("Error initializing dashboard:", error);
  }
}

async function loadOverview() {
  try {
    const overview = await fetchOverview();
    renderStats(overview);
  } catch (error) {
    console.error("Error loading overview stats:", error);
  }
}

async function populateFilters() {
  try {
    // Populate borough filter
    const zones = await fetchZones();
    const boroughs = [...new Set(zones.map(z => z.pickup_Borough || z.Borough || z.borough))].filter(Boolean).sort();
    const boroughSelect = document.getElementById("boroughFilter");
    
    // Clear existing options except the first one
    while (boroughSelect.options.length > 1) {
      boroughSelect.remove(1);
    }
    
    boroughs.forEach(borough => {
      const option = document.createElement("option");
      option.value = borough;
      option.textContent = borough;
      boroughSelect.appendChild(option);
    });

    // Populate hour filter
    const hourSelect = document.getElementById("hourFilter");
    for (let i = 0; i < 24; i++) {
      const option = document.createElement("option");
      option.value = i;
      option.textContent = `${i.toString().padStart(2, '0')}:00`;
      hourSelect.appendChild(option);
    }
  } catch (error) {
    console.error("Error populating filters:", error);
  }
}

async function loadOverviewTab() {
  try {
    showLoadingState(true);
    
    // Load borough chart and map in parallel
    const [boroughStats, geojson] = await Promise.all([
      fetchByBorough(),
      fetchZonesGeoJSON()
    ]);

    renderBoroughChart(boroughStats);
    renderMap(geojson);
    
    // Only load unfiltered trips if no filters are active
    if (!hasActiveFilters) {
      const tripsData = await fetchTrips({ limit: 10, sort_by: "fare_amount" });
      const trips = Array.isArray(tripsData) ? tripsData : tripsData.trips || [];
      renderTripsTable(trips);
    }
    
    showLoadingState(false);
  } catch (error) {
    console.error("Error loading overview tab:", error);
    showLoadingState(false);
  }
}

// Debounced filter application
async function applyFilters() {
  console.log("Apply filters clicked!");
  
  // Clear previous timeout
  if (filterTimeout) {
    clearTimeout(filterTimeout);
  }

  // Set new timeout to debounce rapid filter changes
  filterTimeout = setTimeout(async () => {
    try {
      console.log("Filter timeout executing...");
      showLoadingState(true);
      
      // Get filter values
      const borough = document.getElementById("boroughFilter").value;
      const hour = document.getElementById("hourFilter").value;
      const minFare = document.getElementById("minFare").value;
      const maxFare = document.getElementById("maxFare").value;

      console.log("Filter values:", { borough, hour, minFare, maxFare });

      // Build query params - limit to 20 rows
      const params = { limit: 20 };
      if (borough) params.borough = borough;
      if (hour) params.hour = hour;
      if (minFare) params.min_fare = parseFloat(minFare);
      if (maxFare) params.max_fare = parseFloat(maxFare);

      console.log("Fetching trips with params:", params);

      // Fetch filtered data
      const tripsData = await fetchTrips(params);
      console.log("Trips data received:", tripsData);
      
      const trips = Array.isArray(tripsData) ? tripsData : tripsData.trips || [];
      console.log("Trips array:", trips);
      
      // Mark that filters are active
      hasActiveFilters = true;
      
      renderTripsTable(trips);

      // Update stats if available
      if (trips.length > 0) {
        const stats = {
          total_trips: tripsData.count || trips.length,
          avg_fare: (trips.reduce((sum, t) => sum + (parseFloat(t.fare_amount) || 0), 0) / trips.length).toFixed(2),
          total_revenue: trips.reduce((sum, t) => sum + (parseFloat(t.total_amount) || 0), 0).toFixed(2)
        };
        console.log("Stats calculated:", stats);
        renderStats(stats);
      } else {
        console.log("No trips found for these filters");
        alert("No trips found matching these filters");
      }
      
      // Scroll to show results
      const tripsTable = document.querySelector(".table-card");
      if (tripsTable) {
        setTimeout(() => {
          tripsTable.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);
      }
      
      showLoadingState(false);
    } catch (error) {
      console.error("Error applying filters:", error);
      showLoadingState(false);
    }
  }, 500); // 500ms debounce delay
}

async function loadGeographicTab() {
  if (loadedTabs.has("geographic")) return;
  try {
    showLoadingState(true);
    
    // Check if mapHeatmap element exists
    const mapContainer = document.getElementById("mapHeatmap");
    if (!mapContainer) {
      console.warn("mapHeatmap container not found");
      loadedTabs.add("geographic");
      showLoadingState(false);
      return;
    }
    
    const geojson = await fetchZonesGeoJSON();
    
    // Create new map instance for geographic tab
    let geoMap = L.map("mapHeatmap").setView([40.7128, -74.0060], 11);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors"
    }).addTo(geoMap);
    
    L.geoJSON(geojson, {
      style: feature => ({
        fillColor: "#ef4444",
        weight: 1,
        opacity: 1,
        color: "white",
        fillOpacity: 0.6
      }),
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        layer.bindPopup(`<strong>${props.zone || props.Zone}</strong><br>${props.borough || props.Borough}`);
      }
    }).addTo(geoMap);
    
    showLoadingState(false);
  } catch (error) {
    console.error("Error loading geographic tab:", error);
    showLoadingState(false);
  }
}

async function loadTripExplorerTab() {
  try {
    showLoadingState(true);
    
    const tripsData = await fetchTrips({ limit: 20 });
    const trips = Array.isArray(tripsData) ? tripsData : tripsData.trips || [];
    
    // Render to the full trips table
    const tableBody = document.querySelector("#tripsTableFull tbody");
    if (tableBody) {
      tableBody.innerHTML = "";
      if (trips.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">No trips found</td></tr>';
      } else {
        trips.forEach(trip => {
          const row = document.createElement("tr");
          const pickupDate = trip.tpep_pickup_datetime ? new Date(trip.tpep_pickup_datetime).toLocaleString() : "N/A";
          const pickupZone = trip.pickup_borough || trip.PULocationID || "Unknown";
          const dropoffZone = trip.dropoff_borough || trip.DOLocationID || "Unknown";
          const distance = parseFloat(trip.trip_distance) ? parseFloat(trip.trip_distance).toFixed(2) : "0";
          const fare = parseFloat(trip.fare_amount) ? parseFloat(trip.fare_amount).toFixed(2) : "0";
          const duration = parseFloat(trip.trip_duration_minutes) ? parseFloat(trip.trip_duration_minutes).toFixed(0) : "0";
          
          row.innerHTML = `
            <td>${pickupDate}</td>
            <td>${pickupZone}</td>
            <td>${dropoffZone}</td>
            <td>${distance} mi</td>
            <td>$${fare}</td>
            <td>${duration} min</td>
          `;
          tableBody.appendChild(row);
        });
      }
    }
    
    showLoadingState(false);
  } catch (error) {
    console.error("Error loading trip explorer tab:", error);
    showLoadingState(false);
  }
}

function showLoadingState(loading) {
  isLoading = loading;
  const tables = document.querySelectorAll("table tbody");
  tables.forEach(table => {
    if (loading && table.children.length === 0) {
      table.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px; opacity: 0.6;">Loading...</td></tr>';
    }
  });
}

// Tab switching functionality
function setupTabSwitching() {
  const tabButtons = document.querySelectorAll(".tabs button");
  console.log(`Found ${tabButtons.length} tab buttons`);
  
  const tabs = [
    { id: "overviewTab", element: document.getElementById("overviewTab"), handler: loadOverviewTab },
    { id: "geographicTab", element: document.getElementById("geographicTab"), handler: loadGeographicTab },
    { id: "tripExplorerTab", element: document.getElementById("tripExplorerTab"), handler: loadTripExplorerTab }
  ];

  console.log("Tab elements found:", tabs.map((t, i) => ({ index: i, id: t.id, found: !!t.element })));

  tabButtons.forEach((button, index) => {
    console.log(`Attaching click listener to button ${index}: ${button.textContent}`);
    
    button.addEventListener("click", async (e) => {
      e.preventDefault();
      console.log(`Tab ${index} clicked: ${button.textContent}`);
      
      // Remove active class from all buttons
      tabButtons.forEach(b => b.classList.remove("active"));
      // Add active to clicked button
      button.classList.add("active");
      
      // Hide all tabs
      tabs.forEach(tab => {
        if (tab.element) {
          tab.element.style.display = "none";
          console.log(`Hiding tab: ${tab.id}`);
        }
      });
      
      // Show selected tab
      if (tabs[index] && tabs[index].element) {
        tabs[index].element.style.display = "block";
        console.log(`Showing tab: ${tabs[index].id}`);
        
        // Load content for this tab
        try {
          console.log(`Loading content for tab: ${tabs[index].id}`);
          await tabs[index].handler();
        } catch (error) {
          console.error(`Error loading tab ${index}:`, error);
        }
      } else {
        console.warn(`Tab ${index} element not found`);
      }
    });
  });
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  console.log("Dashboard initializing...");
  
  initDashboard();
  setupTabSwitching();
  
  // Apply filters button with debouncing
  const applyBtn = document.getElementById("applyFilters");
  if (applyBtn) {
    applyBtn.addEventListener("click", applyFilters);
    console.log("Filters button listener attached");
  }
  
  // Also debounce on input change
  const filterInputs = document.querySelectorAll("#boroughFilter, #hourFilter, #minFare, #maxFare");
  filterInputs.forEach(input => {
    input.addEventListener("change", applyFilters);
  });
  
  console.log("Dashboard initialized successfully");
});
