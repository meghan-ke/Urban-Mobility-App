CREATE DATABASE IF NOT EXISTS urban_mobility;
USE urban_mobility;


-- Drop views first (they depend on tables)
DROP VIEW IF EXISTS trip_details;
DROP VIEW IF EXISTS rate_code_statistics;
DROP VIEW IF EXISTS borough_statistics;


-- Drop tables if they exist (for clean recreation)
DROP TABLE IF EXISTS trips ;
DROP TABLE IF EXISTS rate_codes ;
DROP TABLE IF EXISTS taxi_zones ;


-- DIMENSION TABLE: rate_codes


CREATE TABLE rate_codes (
    RatecodeID INTEGER PRIMARY KEY,
    rate_code_name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL
);

-- DIMENSION TABLE: taxi_zones


CREATE TABLE taxi_zones (
    LocationID INTEGER PRIMARY KEY,
    Borough VARCHAR(50),
    Zone VARCHAR(100) NOT NULL,
    service_zone VARCHAR(50)
    
);

-- Indexes for efficient location lookups
CREATE INDEX idx_taxi_zones_borough ON taxi_zones(Borough);
CREATE INDEX idx_taxi_zones_service_zone ON taxi_zones(service_zone);

-- FACT TABLE: trips

CREATE TABLE trips (
    -- Primary Key
    trip_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    
    -- Trip Metadata
    VendorID INTEGER,
    tpep_pickup_datetime TIMESTAMP NOT NULL,
    tpep_dropoff_datetime TIMESTAMP NOT NULL,
    passenger_count INTEGER,
    trip_distance DECIMAL(10, 2),
    store_and_fwd_flag CHAR(1),
    
    -- Foreign Keys (Relationships)
    RatecodeID INTEGER,
    PULocationID INTEGER,
    DOLocationID INTEGER,
    
    -- Payment Information
    payment_type INTEGER,
    fare_amount DECIMAL(10, 2),
    extra DECIMAL(10, 2),
    mta_tax DECIMAL(10, 2),
    tip_amount DECIMAL(10, 2),
    tolls_amount DECIMAL(10, 2),
    improvement_surcharge DECIMAL(10, 2),
    total_amount DECIMAL(10, 2),
    congestion_surcharge DECIMAL(10, 2),
    
    -- Engineered Features (Derived Columns)
    trip_duration_minutes DECIMAL(10, 2),
    average_speed_mph DECIMAL(10, 2),
    tip_percentage DECIMAL(5, 2),
    
    -- Foreign Key Constraints
    CONSTRAINT fk_rate_code 
        FOREIGN KEY (RatecodeID) 
        REFERENCES rate_codes(RatecodeID)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_pickup_location 
        FOREIGN KEY (PULocationID) 
        REFERENCES taxi_zones(LocationID)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_dropoff_location 
        FOREIGN KEY (DOLocationID) 
        REFERENCES taxi_zones(LocationID)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    
    -- Data Integrity Constraints
    
    CONSTRAINT chk_passenger_count 
        CHECK (passenger_count >= 0 AND passenger_count <= 9),
    
    CONSTRAINT chk_trip_distance 
        CHECK (trip_distance >= 0),
    
    CONSTRAINT chk_fare_amount 
        CHECK (fare_amount >= 0),
    
    CONSTRAINT chk_total_amount 
        CHECK (total_amount >= 0)
);

-- INDEXES FOR QUERY OPTIMIZATION

-- Datetime indexes for time-based queries
CREATE INDEX idx_trips_pickup_datetime ON trips(tpep_pickup_datetime);
CREATE INDEX idx_trips_dropoff_datetime ON trips(tpep_dropoff_datetime);

-- Location indexes for geographic queries
CREATE INDEX idx_trips_pickup_location ON trips(PULocationID);
CREATE INDEX idx_trips_dropoff_location ON trips(DOLocationID);

-- Rate code index for trip type analysis
CREATE INDEX idx_trips_ratecode ON trips(RatecodeID);

-- Vendor index for vendor comparison
CREATE INDEX idx_trips_vendor ON trips(VendorID);

-- Payment type index for payment analysis
CREATE INDEX idx_trips_payment_type ON trips(payment_type);

-- Composite index for common location-based time queries
CREATE INDEX idx_trips_pickup_datetime_location ON trips(tpep_pickup_datetime, PULocationID);

CREATE INDEX idx_trips_fare_amount ON trips(fare_amount);

CREATE INDEX idx_trips_distance ON trips(trip_distance);

CREATE INDEX idx_trips_duration ON trips(trip_duration_minutes);

CREATE INDEX idx_trips_total_amount ON trips(total_amount);

-- VIEWS FOR CRITICAL API ENDPOINTS

-- View 1: trip_details

-- GET /api/trips (with filters)
CREATE VIEW trip_details AS
SELECT 
    -- Trip IDs and timestamps
    t.trip_id,
    t.VendorID,
    t.tpep_pickup_datetime,
    t.tpep_dropoff_datetime,
    
    -- Trip metrics
    t.passenger_count,
    t.trip_distance,
    t.fare_amount,
    t.tip_amount,
    t.total_amount,
    t.payment_type,
    
    -- Engineered features
    t.trip_duration_minutes,
    t.average_speed_mph,
    t.tip_percentage,
    
    -- Rate code details (from rate_codes dimension)
    rc.RatecodeID,
    rc.rate_code_name,
    rc.description as rate_description,
    
    -- Pickup location details (from taxi_zones dimension)
    t.PULocationID,
    pu_zone.Borough as pickup_borough,
    pu_zone.Zone as pickup_zone,
    pu_zone.service_zone as pickup_service_zone,
    
    -- Dropoff location details (from taxi_zones dimension)
    t.DOLocationID,
    do_zone.Borough as dropoff_borough,
    do_zone.Zone as dropoff_zone,
    do_zone.service_zone as dropoff_service_zone
    
FROM trips t
LEFT JOIN rate_codes rc ON t.RatecodeID = rc.RatecodeID
LEFT JOIN taxi_zones pu_zone ON t.PULocationID = pu_zone.LocationID
LEFT JOIN taxi_zones do_zone ON t.DOLocationID = do_zone.LocationID;


-- View 2: rate_code_statistics
--  GET /api/stats/by-rate-code

CREATE VIEW rate_code_statistics AS
SELECT 
    rc.RatecodeID,
    rc.rate_code_name,
    COUNT(*) as trip_count,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(AVG(t.tip_percentage), 2) as avg_tip_percentage,
    ROUND(AVG(t.trip_distance), 2) as avg_distance,
    ROUND(AVG(t.trip_duration_minutes), 2) as avg_duration,
    ROUND(SUM(t.total_amount), 2) as total_revenue
FROM trips t
JOIN rate_codes rc ON t.RatecodeID = rc.RatecodeID
GROUP BY rc.RatecodeID, rc.rate_code_name
ORDER BY trip_count DESC;


-- View 3: borough_statistics
-- GET /api/stats/by-borough
CREATE VIEW borough_statistics AS
SELECT 
    tz.Borough as pickup_borough,
    COUNT(*) as trip_count,
    ROUND(AVG(t.fare_amount), 2) as avg_fare,
    ROUND(AVG(t.trip_distance), 2) as avg_distance,
    ROUND(AVG(t.tip_percentage), 2) as avg_tip_percentage,
    ROUND(AVG(t.trip_duration_minutes), 2) as avg_duration,
    ROUND(SUM(t.total_amount), 2) as total_revenue
FROM trips t
JOIN taxi_zones tz ON t.PULocationID = tz.LocationID
WHERE tz.Borough IS NOT NULL
GROUP BY tz.Borough
ORDER BY trip_count DESC;




