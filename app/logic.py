# Core intercept calculation logic.



from __future__ import annotations

import math
from pathlib import Path
import sqlite3
from typing import Any, Optional

from .classification import NOT_THREAT, classify_threat


# DB lives next to this file: app/lmt_defence.db
APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "lmt_defence.db"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:  # [3]
    #Haversine formula: great-circle distance between two points on Earth.
    #Returns distance in metres (rest of app uses range_m, distance_m).
    
    d_lat = (lat2 - lat1) * math.pi / 180.0  # distance between latitudes
    d_lon = (lon2 - lon1) * math.pi / 180.0  # and longitudes

    lat1_rad = lat1 * math.pi / 180.0  # convert to radians
    lat2_rad = lat2 * math.pi / 180.0  # convert to radians

    a = (  # apply formula
        pow(math.sin(d_lat / 2), 2)
        + pow(math.sin(d_lon / 2), 2) * math.cos(lat1_rad) * math.cos(lat2_rad)
    )
    c = 2 * math.asin(math.sqrt(a))
    rad_km = 6371
    return rad_km * c * 1000  # convert km to metres


def move_position(lat: float, lon: float, heading_deg: float, speed_ms: float, time_s: float) -> tuple[float, float]:
    #Calculate new position after moving at constant speed and heading for time_s seconds. [5]
    #Returns (new_lat, new_lon).
    
    heading_rad = math.radians(heading_deg)
    v_north = speed_ms * math.cos(heading_rad)
    v_east = speed_ms * math.sin(heading_rad)
    
    delta_north = v_north * time_s  # metres
    delta_east = v_east * time_s    # metres
    
    lat_rad = math.radians(lat)
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(lat_rad)
    if m_per_deg_lon == 0:
        m_per_deg_lon = 1.0
    
    new_lat = lat + delta_north / m_per_deg_lat
    new_lon = lon + delta_east / m_per_deg_lon
    
    return new_lat, new_lon


def _connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def load_base_interceptor_options() -> list[dict[str, Any]]:
    #Load all (base, interceptor) pairs from SQLite
    with _connect_db() as conn:
        rows = conn.execute(
            """
            SELECT
                b.id AS base_id,
                b.name AS base_name,
                b.latitude AS base_latitude,
                b.longitude AS base_longitude,
                it.id AS interceptor_id,
                it.name AS interceptor_name,
                it.speed_ms,
                it.range_m,
                it.max_altitude_m,
                it.price_model,
                it.price_value_eur
            FROM bases b
            JOIN base_interceptors bi ON bi.base_id = b.id
            JOIN interceptor_types it ON it.id = bi.interceptor_id
            ORDER BY b.id, it.id;
            """
        ).fetchall()
    return [dict(r) for r in rows]


def calculate_intercept(
    speed_ms: float,
    altitude_m: float,
    heading_deg: float,
    latitude: float,
    longitude: float,
    seconds_since_launch: float = 0.0,
) -> dict[str, Any]:
   
    #Calculate best intercept option for a threat.
    
    #IMPORTANT: 
    # The intercept point (where interceptor will meet threat) is STATIC - calculated once
    # The interceptor's current location is updated every second (1/second frequency)
    #  as it moves from the base toward the static intercept point
    
    #Args:
    #    speed_ms: Threat speed in m/s
    #    altitude_m: Threat altitude in metres
    #    heading_deg: Threat heading in degrees
    #    latitude: Threat latitude (current position)
    #    longitude: Threat longitude (current position)
    #    seconds_since_launch: Time elapsed since interceptor launch (for tracking current position)
    
    #Returns:
    #    dict with keys: threat_level, base_name, interceptor_type, intercept_latitude,
    #    intercept_longitude, interceptor_current_latitude, interceptor_current_longitude,
    #    calculated_cost_eur, note, map_url
    
    threat_level = classify_threat(speed_ms, altitude_m)

    # Policy: only "THREAT" triggers an intercept action.
    if threat_level != "THREAT":
        return {
            "threat_level": threat_level,
            "base_name": None,
            "interceptor_type": None,
            "base_latitude": None,
            "base_longitude": None,
            "intercept_latitude": None,
            "intercept_longitude": None,
            "time_to_intercept_s": None,
            "interceptor_current_latitude": None,
            "interceptor_current_longitude": None,
            "calculated_cost_eur": None,
            "note": f"No interception: threat level {threat_level}",
            "map_url": None,
        }

    options = load_base_interceptor_options()

    best: Optional[dict[str, Any]] = None
    best_cost: Optional[float] = None
    best_intercept_lat: Optional[float] = None
    best_intercept_lon: Optional[float] = None
    best_intercept_time: Optional[float] = None  # Time to intercept (for calculating current position)
    best_base_lat: Optional[float] = None
    best_base_lon: Optional[float] = None
    best_speed: Optional[float] = None

    for opt in options:
        if altitude_m > float(opt["max_altitude_m"]):
            continue

        distance_m = haversine_m(
            float(opt["base_latitude"]),
            float(opt["base_longitude"]),
            latitude,
            longitude,
        )
        if distance_m > float(opt["range_m"]):
            continue

        speed_interceptor = float(opt["speed_ms"])
        if speed_interceptor <= 0:
            continue

        # Constant-velocity intercept: solve quadratic for intercept time
        # Set up coordinate system: base at origin (0,0), target at r0 with velocity vt
        base_lat = float(opt["base_latitude"])
        base_lon = float(opt["base_longitude"])

        # Convert lat/lon differences to local metres (flat-earth approximation)
        lat0_rad = math.radians(latitude)
        m_per_deg_lat = 111_320.0
        m_per_deg_lon = 111_320.0 * math.cos(lat0_rad)
        if m_per_deg_lon == 0:
            m_per_deg_lon = 1.0

        # Target position relative to base (in metres)
        delta_lat_deg = latitude - base_lat
        delta_lon_deg = longitude - base_lon
        x0 = delta_lon_deg * m_per_deg_lon  # east
        y0 = delta_lat_deg * m_per_deg_lat  # north

        # Target velocity vector (from heading + speed)
        heading_rad = math.radians(heading_deg)
        v_target = speed_ms
        v_tx = v_target * math.sin(heading_rad)  # east component
        v_ty = v_target * math.cos(heading_rad)  # north component

        # Quadratic: A*t^2 + B*t + C = 0
        # where A = ||vt||^2 - s^2, B = 2*(r0·vt), C = ||r0||^2
        v_t_squared = v_tx * v_tx + v_ty * v_ty
        s_squared = speed_interceptor * speed_interceptor
        A = v_t_squared - s_squared
        B = 2 * (x0 * v_tx + y0 * v_ty)
        C = x0 * x0 + y0 * y0

        # Solve quadratic
        discriminant = B * B - 4 * A * C
        if discriminant < 0:
            # No real intercept (interceptor too slow or geometry impossible)
            continue

        sqrt_d = math.sqrt(discriminant)
        if abs(A) < 1e-10:
            # Degenerate case: A ≈ 0 (target speed ≈ interceptor speed)
            if abs(B) < 1e-10:
                continue
            t = -C / B
            if t <= 0:
                continue
        else:
            t1 = (-B - sqrt_d) / (2 * A)
            t2 = (-B + sqrt_d) / (2 * A)
            # Choose smallest positive time
            if t1 > 0 and t2 > 0:
                t = min(t1, t2)
            elif t1 > 0:
                t = t1
            elif t2 > 0:
                t = t2
            else:
                continue  # No positive solution

        # Intercept point in local metres: r0 + vt*t
        x_intercept = x0 + v_tx * t
        y_intercept = y0 + v_ty * t

        # Convert back to lat/lon
        intercept_lat = base_lat + y_intercept / m_per_deg_lat
        intercept_lon = base_lon + x_intercept / m_per_deg_lon

        # Check range constraint at intercept point
        distance_m = haversine_m(base_lat, base_lon, intercept_lat, intercept_lon)
        if distance_m > float(opt["range_m"]):
            continue

        time_s = t

        price_model = str(opt["price_model"])
        price_value = float(opt["price_value_eur"])

        if price_model == "flat":
            cost = price_value
        elif price_model == "per_minute":
            cost = math.ceil(time_s / 60.0) * price_value
        elif price_model == "per_shot":
            cost = price_value

        if best_cost is None or cost < best_cost:
            best = opt
            best_cost = cost
            best_intercept_lat = intercept_lat
            best_intercept_lon = intercept_lon
            best_intercept_time = time_s
            best_base_lat = base_lat
            best_base_lon = base_lon
            best_speed = speed_interceptor

    if best is None or best_cost is None or math.isinf(best_cost):
        return {
            "threat_level": threat_level,
            "base_name": None,
            "interceptor_type": None,
            "base_latitude": None,
            "base_longitude": None,
            "intercept_latitude": None,
            "intercept_longitude": None,
            "time_to_intercept_s": None,
            "interceptor_current_latitude": None,
            "interceptor_current_longitude": None,
            "calculated_cost_eur": None,
            "note": "No interceptor found from available bases",
            "map_url": None,
        }

    # Build Google Maps directions URL showing triangle: base -> threat -> intercept point
    base_lat = best_base_lat
    base_lon = best_base_lon
    
    map_url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={base_lat},{base_lon}"
        f"&waypoints={latitude},{longitude}"
        f"&destination={best_intercept_lat},{best_intercept_lon}"
        if best_intercept_lat is not None and best_intercept_lon is not None
        else None
    )
    
    # Calculate interceptor's current position (updated every second)
    # Interceptor moves from base toward intercept point
    interceptor_current_lat: Optional[float] = None
    interceptor_current_lon: Optional[float] = None
    
    if best_intercept_lat is not None and best_intercept_lon is not None:
        # Calculate distance from base to intercept point
        total_distance_m = haversine_m(base_lat, base_lon, best_intercept_lat, best_intercept_lon)
        
        # Calculate how far interceptor has traveled
        distance_traveled_m = best_speed * seconds_since_launch
        
        if distance_traveled_m >= total_distance_m:
            # Interceptor has reached or passed intercept point
            interceptor_current_lat = best_intercept_lat
            interceptor_current_lon = best_intercept_lon
        elif distance_traveled_m > 0:
            # Calculate heading from base to intercept point
            lat0_rad = math.radians(base_lat)
            m_per_deg_lat = 111_320.0
            m_per_deg_lon = 111_320.0 * math.cos(lat0_rad)
            
            delta_lat_deg = best_intercept_lat - base_lat
            delta_lon_deg = best_intercept_lon - base_lon
            
            # Distance in metres
            delta_north_m = delta_lat_deg * m_per_deg_lat
            delta_east_m = delta_lon_deg * m_per_deg_lon
            
            # Heading angle
            heading_to_intercept_rad = math.atan2(delta_east_m, delta_north_m)
            
            # Current position along the path
            current_north_m = math.cos(heading_to_intercept_rad) * distance_traveled_m
            current_east_m = math.sin(heading_to_intercept_rad) * distance_traveled_m
            
            interceptor_current_lat = base_lat + current_north_m / m_per_deg_lat
            interceptor_current_lon = base_lon + current_east_m / m_per_deg_lon
        else:
            # Interceptor hasn't launched yet (still at base)
            interceptor_current_lat = base_lat
            interceptor_current_lon = base_lon
    
    return {
        "threat_level": threat_level,
        "base_name": str(best["base_name"]),
        "interceptor_type": str(best["interceptor_name"]),
        "base_latitude": best_base_lat,  # Base location A
        "base_longitude": best_base_lon,  # Base location A
        "intercept_latitude": best_intercept_lat,  # Static intercept point C
        "intercept_longitude": best_intercept_lon,  # Static intercept point C
        "time_to_intercept_s": best_intercept_time,  # Time to reach intercept point
        "interceptor_current_latitude": interceptor_current_lat,  # Updated every second
        "interceptor_current_longitude": interceptor_current_lon,  # Updated every second
        "calculated_cost_eur": round(best_cost, 2),
        "note": "Chosen cheapest feasible option; intercept point predicted from target heading and speeds",
        "map_url": map_url,
    }
