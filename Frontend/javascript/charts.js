// charts.js
let map = null;         // Map instance
let boroughChart = null; // Chart.js instance

// Render trips in table
export function renderTripsTable(trips) {
  const tableBody = document.querySelector("#tripsTable tbody");
  tableBody.innerHTML = ""; // Clear previous rows

  trips.forEach(trip => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${new Date(trip.tpep_pickup_datetime).toLocaleString()}</td>
      <td>${trip.pickup_borough || trip.PULocationID}</td>
      <td>${trip.dropoff_borough || trip.DOLocationID}</td>
      <td>${trip.trip_distance} mi</td>
      <td>$${trip.fare_amount}</td>
    `;
    tableBody.appendChild(row);
  });
}

// Render overall stats
export function renderStats(stats) {
  document.getElementById("totalTrips").textContent = stats.total_trips.toLocaleString();
  document.getElementById("avgFare").textContent = `$${stats.avg_fare}`;
  document.getElementById("totalRevenue").textContent = `$${stats.total_revenue}`;
}

// Render borough chart
export function renderBoroughChart(data) {
  const ctx = document.getElementById("boroughChart").getContext("2d");

  // Destroy previous chart if exists
  if (boroughChart) {
    boroughChart.destroy();
  }

  boroughChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map(d => d.Borough),
      datasets: [{
        label: "Trip Count",
        data: data.map(d => d.trip_count),
        backgroundColor: "rgba(54, 162, 235, 0.6)"
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  return boroughChart;
}

// Render Leaflet map with GeoJSON
export function renderMap(geojson) {
  if (!map) {
    map = L.map("map").setView([40.7128, -74.0060], 11); // NYC center

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors"
    }).addTo(map);
  }

  // Clear existing GeoJSON layers
  map.eachLayer(layer => {
    if (layer.feature) map.removeLayer(layer);
  });

  // Add GeoJSON with color based on feature properties (optional example)
  L.geoJSON(geojson, {
    style: feature => ({
      fillColor: "#3498db",
      weight: 1,
      opacity: 1,
      color: "white",
      fillOpacity: 0.5
    }),
    onEachFeature: (feature, layer) => {
      layer.bindPopup(`<strong>${feature.properties.zone}</strong><br>${feature.properties.borough}`);
    }
  }).addTo(map);

  return map;
}
