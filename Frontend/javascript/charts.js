// charts.js
let map = null;         // Map instance
let boroughChart = null; // Chart.js instance
let hourlyChart = null;
let fareChart = null;

// Render trips in table with better performance (limited rows)
export function renderTripsTable(trips) {
  const tableBody = document.querySelector("#tripsTable tbody");
  if (!tableBody) return;
  
  tableBody.innerHTML = ""; // Clear previous rows

  if (!trips || trips.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px; opacity: 0.6;">No trips found</td></tr>';
    return;
  }

  // Limit rendering to first 10 rows for performance
  const maxRows = 10;
  const tripsToRender = trips.slice(0, maxRows);
  
  // Use DocumentFragment to batch DOM updates
  const fragment = document.createDocumentFragment();
  
  tripsToRender.forEach(trip => {
    const row = document.createElement("tr");
    
    // Safely get values with fallbacks and convert to numbers
    const pickupDate = trip.tpep_pickup_datetime 
      ? new Date(trip.tpep_pickup_datetime).toLocaleString() 
      : "N/A";
    const pickupZone = trip.pickup_borough || trip.PULocationID || "Unknown";
    const dropoffZone = trip.dropoff_borough || trip.DOLocationID || "Unknown";
    const distance = parseFloat(trip.trip_distance) ? parseFloat(trip.trip_distance).toFixed(2) : "0";
    const fare = parseFloat(trip.fare_amount) ? parseFloat(trip.fare_amount).toFixed(2) : "0";
    
    row.innerHTML = `
      <td>${pickupDate}</td>
      <td>${pickupZone}</td>
      <td>${dropoffZone}</td>
      <td>${distance} mi</td>
      <td>$${fare}</td>
    `;
    fragment.appendChild(row);
  });
  
  tableBody.appendChild(fragment);
  
  // Show count info if truncated
  if (trips.length > maxRows) {
    const countRow = document.createElement("tr");
    countRow.innerHTML = `<td colspan="5" style="text-align:center; padding: 10px; opacity: 0.6; font-size: 12px;">Showing ${maxRows} of ${trips.length} trips</td>`;
    tableBody.appendChild(countRow);
  }
}

// Render overall stats with better formatting
export function renderStats(stats) {
  const totalTripsEl = document.getElementById("totalTrips");
  const avgFareEl = document.getElementById("avgFare");
  const totalRevenueEl = document.getElementById("totalRevenue");

  if (totalTripsEl) {
    totalTripsEl.textContent = stats.total_trips ? stats.total_trips.toLocaleString() : "0";
  }
  if (avgFareEl) {
    avgFareEl.textContent = stats.avg_fare ? `$${parseFloat(stats.avg_fare).toFixed(2)}` : "$0.00";
  }
  if (totalRevenueEl) {
    totalRevenueEl.textContent = stats.total_revenue ? `$${parseFloat(stats.total_revenue).toFixed(2)}` : "$0.00";
  }
}

// Render borough chart with better data handling
export function renderBoroughChart(data) {
  const ctx = document.getElementById("boroughChart");
  if (!ctx) return;

  // Destroy previous chart if exists
  if (boroughChart) {
    boroughChart.destroy();
  }

  // Ensure data is an array
  const chartData = Array.isArray(data) ? data : (data.data || []);
  
  if (chartData.length === 0) {
    console.warn("No borough data available");
    return;
  }

  const canvasCtx = ctx.getContext("2d");
  
  // Sort by trip count and take top 10
  const topBoroughs = chartData
    .sort((a, b) => (parseInt(b.trip_count) || 0) - (parseInt(a.trip_count) || 0))
    .slice(0, 10);
  
  boroughChart = new Chart(canvasCtx, {
    type: "bar",
    data: {
      labels: topBoroughs.map(d => d.pickup_borough || d.Borough || d.borough || "Unknown"),
      datasets: [{
        label: "Trip Count",
        data: topBoroughs.map(d => parseInt(d.trip_count) || 0),
        backgroundColor: "rgba(54, 162, 235, 0.6)",
        borderColor: "rgba(54, 162, 235, 1)",
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      indexAxis: 'y',
      plugins: {
        legend: { display: true }
      },
      scales: {
        x: { beginAtZero: true }
      }
    }
  });

  return boroughChart;
}

// Render hourly distribution chart
export function renderHourlyChart(data) {
  const ctx = document.getElementById("hourlyChart");
  if (!ctx) return;

  if (hourlyChart) {
    hourlyChart.destroy();
  }

  const chartData = Array.isArray(data) ? data : (data.data || []);
  
  if (chartData.length === 0) return;

  const canvasCtx = ctx.getContext("2d");
  
  hourlyChart = new Chart(canvasCtx, {
    type: "line",
    data: {
      labels: chartData.map(d => `${d.hour}:00`),
      datasets: [{
        label: "Trips by Hour",
        data: chartData.map(d => d.trip_count || 0),
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.1)",
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  return hourlyChart;
}

// Render fare distribution chart
export function renderFareChart(data) {
  const ctx = document.getElementById("fareChart");
  if (!ctx) return;

  if (fareChart) {
    fareChart.destroy();
  }

  const chartData = Array.isArray(data) ? data : (data.data || []);
  
  if (chartData.length === 0) return;

  const canvasCtx = ctx.getContext("2d");
  
  fareChart = new Chart(canvasCtx, {
    type: "pie",
    data: {
      labels: chartData.map(d => d.fare_bracket || "Unknown"),
      datasets: [{
        data: chartData.map(d => d.trip_count || 0),
        backgroundColor: [
          "rgba(255, 99, 132, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 206, 86, 0.6)",
          "rgba(75, 192, 192, 0.6)",
          "rgba(153, 102, 255, 0.6)",
          "rgba(255, 159, 64, 0.6)"
        ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true }
      }
    }
  });

  return fareChart;
}

// Render Leaflet map with GeoJSON OR display as a zones table with legend
export function renderMap(geojson) {
  const mapContainer = document.getElementById("map");
  if (!mapContainer) return;

  // Check if we should render as table instead (better for zones display)
  if (geojson && geojson.features) {
    // Extract zones from GeoJSON
    const zones = geojson.features.map(f => f.properties);
    
    // Group by borough
    const byBorough = {};
    zones.forEach(zone => {
      const borough = zone.borough || "Unknown";
      if (!byBorough[borough]) byBorough[borough] = [];
      byBorough[borough].push(zone);
    });

    // Color scheme for boroughs
    const boroughColors = {
      "Manhattan": "#FF6B6B",
      "Queens": "#4ECDC4",
      "Brooklyn": "#45B7D1",
      "Bronx": "#FFA07A",
      "Staten Island": "#98D8C8",
      "EWR": "#F7DC6F"
    };

    // Create legend
    let html = '<div style="margin-bottom: 20px;">';
    html += '<h4 style="margin: 0 0 10px 0; font-weight: 600;">Borough Legend</h4>';
    html += '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px;">';
    
    Object.keys(boroughColors).sort().forEach(borough => {
      const color = boroughColors[borough];
      html += `
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 20px; height: 20px; background-color: ${color}; border-radius: 3px; border: 1px solid #333;"></div>
          <span style="font-size: 12px;">${borough}</span>
        </div>
      `;
    });
    
    html += '</div></div>';

    // Add zones list with color-coded headers
    html += '<div style="max-height: 400px; overflow-y: auto; font-size: 12px;">';
    Object.keys(byBorough).sort().forEach(borough => {
      const color = boroughColors[borough] || "#CCCCCC";
      html += `<h4 style="margin: 10px 0 5px 0; font-weight: 600; padding: 5px; background-color: ${color}; color: white; border-radius: 3px;">${borough} (${byBorough[borough].length} zones)</h4>`;
      html += '<ul style="margin: 0; padding-left: 20px; list-style: none;">';
      byBorough[borough].forEach(zone => {
        html += `<li style="padding: 3px 0;">• ${zone.zone || 'Unknown'}</li>`;
      });
      html += '</ul>';
    });
    html += '</div>';

    // Replace map container with zones table
    mapContainer.innerHTML = html;
  }

  return null;
}

// Render zone heatmap
export function renderZoneHeatmap(data) {
  const mapContainer = document.getElementById("map");
  if (!mapContainer || !map) return;

  // Clear existing layers
  map.eachLayer(layer => {
    if (layer.feature) map.removeLayer(layer);
  });

  const zoneData = Array.isArray(data) ? data : (data.data || []);
  
  if (zoneData.length === 0) return;

  const maxTrips = Math.max(...zoneData.map(z => z.trip_count || 0));
  console.log("Heatmap data loaded:", zoneData.length, "zones");
}
