"""
Flask API for NYC Taxi Trip Dashboard
Provides REST endpoints for trip data, statistics, and visualizations
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import mysql.connector
from pathlib import Path
import sys
import json

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from database.db_connection import get_connection, close_connection

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Path to GeoJSON file
GEOJSON_PATH = project_root / "Data" / "raw" / "taxi_zones (1)" / "taxi_zones.geojson"


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_db():
    """Get database connection"""
    return get_connection()


def execute_query(query, params=None, fetchone=False):
    """Execute query and return results"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchone() if fetchone else cursor.fetchall()
        return result
    finally:
        cursor.close()
        close_connection(conn)


# ============================================
# CORE ENDPOINTS
# ============================================

@app.route('/')
def home():
    """API documentation"""
    return jsonify({
        "message": "NYC Taxi Trip API",
        "version": "1.0",
        "endpoints": {
            "trips": "/api/trips",
            "overview": "/api/stats/overview",
            "by_rate_code": "/api/stats/by-rate-code",
            "by_borough": "/api/stats/by-borough",
            "top_pickup": "/api/locations/top-pickup",
            "top_dropoff": "/api/locations/top-dropoff",
            "zones_geojson": "/api/zones/geojson"
        }
    })


# ============================================
# TRIP ENDPOINTS
# ============================================

@app.route('/api/trips', methods=['GET'])
def get_trips():
    """
    Get trips with optional filters
    Query params: limit, offset, start_date, end_date, borough, rate_code, min_fare, max_fare
    """
    # Get query parameters
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    borough = request.args.get('borough')
    rate_code = request.args.get('rate_code')
    min_fare = request.args.get('min_fare', type=float)
    max_fare = request.args.get('max_fare', type=float)
    sort_by = request.args.get('sort_by', 'tpep_pickup_datetime')
    sort_order = request.args.get('sort_order', 'DESC')
    
    # Build query
    query = "SELECT * FROM trip_details WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND tpep_pickup_datetime >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND tpep_pickup_datetime <= %s"
        params.append(end_date)
    
    if borough:
        query += " AND pickup_borough = %s"
        params.append(borough)
    
    if rate_code:
        query += " AND rate_code_name = %s"
        params.append(rate_code)
    
    if min_fare:
        query += " AND fare_amount >= %s"
        params.append(min_fare)
    
    if max_fare:
        query += " AND fare_amount <= %s"
        params.append(max_fare)
    
    # Add sorting
    allowed_sort_columns = ['tpep_pickup_datetime', 'fare_amount', 'trip_distance', 'trip_duration_minutes']
    if sort_by in allowed_sort_columns:
        sort_order_safe = 'DESC' if sort_order.upper() == 'DESC' else 'ASC'
        query += f" ORDER BY {sort_by} {sort_order_safe}"
    
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    trips = execute_query(query, params)
    
    return jsonify({
        "trips": trips,
        "count": len(trips),
        "limit": limit,
        "offset": offset
    })


# ============================================
# STATISTICS ENDPOINTS
# ============================================

@app.route('/api/stats/overview', methods=['GET'])
def get_overview():
    """Get overall statistics"""
    query = """
        SELECT 
            COUNT(*) as total_trips,
            ROUND(AVG(fare_amount), 2) as avg_fare,
            ROUND(AVG(trip_distance), 2) as avg_distance,
            ROUND(AVG(trip_duration_minutes), 2) as avg_duration,
            ROUND(SUM(total_amount), 2) as total_revenue,
            ROUND(AVG(tip_percentage), 2) as avg_tip_percentage
        FROM trips
    """
    stats = execute_query(query, fetchone=True)
    return jsonify(stats)


@app.route('/api/stats/by-rate-code', methods=['GET'])
def get_by_rate_code():
    """Get statistics grouped by rate code"""
    query = "SELECT * FROM rate_code_statistics"
    stats = execute_query(query)
    return jsonify(stats)


@app.route('/api/stats/by-borough', methods=['GET'])
def get_by_borough():
    """Get statistics grouped by borough"""
    query = "SELECT * FROM borough_statistics"
    stats = execute_query(query)
    return jsonify(stats)


@app.route('/api/stats/by-hour', methods=['GET'])
def get_by_hour():
    """Get trip patterns by hour of day"""
    query = """
        SELECT 
            HOUR(tpep_pickup_datetime) as hour,
            COUNT(*) as trip_count,
            ROUND(AVG(fare_amount), 2) as avg_fare,
            ROUND(AVG(average_speed_mph), 2) as avg_speed
        FROM trips
        GROUP BY HOUR(tpep_pickup_datetime)
        ORDER BY hour
    """
    stats = execute_query(query)
    return jsonify(stats)


@app.route('/api/stats/time-series', methods=['GET'])
def get_time_series():
    """Get daily trip trends"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = """
        SELECT 
            DATE(tpep_pickup_datetime) as date,
            COUNT(*) as trip_count,
            ROUND(SUM(total_amount), 2) as total_revenue,
            ROUND(AVG(fare_amount), 2) as avg_fare
        FROM trips
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND tpep_pickup_datetime >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND tpep_pickup_datetime <= %s"
        params.append(end_date)
    
    query += " GROUP BY DATE(tpep_pickup_datetime) ORDER BY date"
    
    stats = execute_query(query, params)
    return jsonify(stats)


# ============================================
# LOCATION ENDPOINTS
# ============================================

@app.route('/api/locations/zones', methods=['GET'])
def get_zones():
    """Get all taxi zones"""
    borough = request.args.get('borough')
    
    query = "SELECT * FROM taxi_zones"
    params = []
    
    if borough:
        query += " WHERE Borough = %s"
        params.append(borough)
    
    query += " ORDER BY Zone"
    
    zones = execute_query(query, params)
    return jsonify(zones)


@app.route('/api/locations/top-pickup', methods=['GET'])
def get_top_pickup():
    """Get top pickup locations"""
    limit = request.args.get('limit', 10, type=int)
    
    query = """
        SELECT 
            tz.Zone,
            tz.Borough,
            COUNT(*) as trip_count,
            ROUND(AVG(t.fare_amount), 2) as avg_fare
        FROM trips t
        JOIN taxi_zones tz ON t.PULocationID = tz.LocationID
        GROUP BY tz.Zone, tz.Borough
        ORDER BY trip_count DESC
        LIMIT %s
    """
    locations = execute_query(query, [limit])
    return jsonify(locations)


@app.route('/api/locations/top-dropoff', methods=['GET'])
def get_top_dropoff():
    """Get top dropoff locations"""
    limit = request.args.get('limit', 10, type=int)
    
    query = """
        SELECT 
            tz.Zone,
            tz.Borough,
            COUNT(*) as trip_count,
            ROUND(AVG(t.fare_amount), 2) as avg_fare
        FROM trips t
        JOIN taxi_zones tz ON t.DOLocationID = tz.LocationID
        GROUP BY tz.Zone, tz.Borough
        ORDER BY trip_count DESC
        LIMIT %s
    """
    locations = execute_query(query, [limit])
    return jsonify(locations)


@app.route('/api/locations/top-routes', methods=['GET'])
def get_top_routes():
    """Get most common pickup-dropoff pairs"""
    limit = request.args.get('limit', 10, type=int)
    
    query = """
        SELECT 
            pu_zone.Zone as pickup_zone,
            pu_zone.Borough as pickup_borough,
            do_zone.Zone as dropoff_zone,
            do_zone.Borough as dropoff_borough,
            COUNT(*) as trip_count,
            ROUND(AVG(t.fare_amount), 2) as avg_fare,
            ROUND(AVG(t.trip_duration_minutes), 2) as avg_duration
        FROM trips t
        JOIN taxi_zones pu_zone ON t.PULocationID = pu_zone.LocationID
        JOIN taxi_zones do_zone ON t.DOLocationID = do_zone.LocationID
        GROUP BY pu_zone.Zone, pu_zone.Borough, do_zone.Zone, do_zone.Borough
        ORDER BY trip_count DESC
        LIMIT %s
    """
    routes = execute_query(query, [limit])
    return jsonify(routes)


# ============================================
# MAP / GEOJSON ENDPOINT
# ============================================

@app.route('/api/zones/geojson', methods=['GET'])
def get_zones_geojson():
    """Serve taxi zones GeoJSON for map visualization"""
    try:
        if not GEOJSON_PATH.exists():
            return jsonify({"error": "GeoJSON file not found"}), 404
        
        with open(GEOJSON_PATH, 'r') as f:
            geojson_data = json.load(f)
        
        return jsonify(geojson_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/zones/heatmap', methods=['GET'])
def get_zone_heatmap():
    """Get trip counts per zone for heatmap visualization"""
    query = """
        SELECT 
            tz.LocationID,
            tz.Zone,
            tz.Borough,
            COUNT(*) as trip_count
        FROM trips t
        JOIN taxi_zones tz ON t.PULocationID = tz.LocationID
        GROUP BY tz.LocationID, tz.Zone, tz.Borough
        ORDER BY trip_count DESC
    """
    heatmap_data = execute_query(query)
    return jsonify(heatmap_data)


# ============================================
# FARE & TIP ENDPOINTS
# ============================================

@app.route('/api/tips/distribution', methods=['GET'])
def get_tip_distribution():
    """Get tip percentage distribution"""
    query = """
        SELECT 
            CASE 
                WHEN tip_percentage = 0 THEN '0% (No Tip)'
                WHEN tip_percentage > 0 AND tip_percentage <= 10 THEN '1-10%'
                WHEN tip_percentage > 10 AND tip_percentage <= 15 THEN '11-15%'
                WHEN tip_percentage > 15 AND tip_percentage <= 20 THEN '16-20%'
                WHEN tip_percentage > 20 AND tip_percentage <= 25 THEN '21-25%'
                WHEN tip_percentage > 25 THEN '25%+'
            END as tip_bracket,
            COUNT(*) as trip_count,
            ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM trips)), 2) as percentage
        FROM trips
        GROUP BY tip_bracket
        ORDER BY 
            CASE tip_bracket
                WHEN '0% (No Tip)' THEN 1
                WHEN '1-10%' THEN 2
                WHEN '11-15%' THEN 3
                WHEN '16-20%' THEN 4
                WHEN '21-25%' THEN 5
                WHEN '25%+' THEN 6
            END
    """
    distribution = execute_query(query)
    return jsonify(distribution)


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ============================================
# RUN APP
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("NYC Taxi Trip API Server")
    print("=" * 60)
    print("API Documentation: http://localhost:5000/")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)