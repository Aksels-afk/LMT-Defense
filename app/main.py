from __future__ import annotations

from datetime import datetime
from typing import Optional

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db_init import init_database
from .logic import calculate_intercept, move_position


class RadarReport(BaseModel):
    speed_ms: float
    altitude_m: float
    heading_deg: float
    latitude: float
    longitude: float
    report_time: float | datetime
    seconds_since_launch: Optional[float] = 0.0  # Time elapsed since interceptor launch (for tracking current position)


class InterceptDecision(BaseModel):
    threat_level: str
    base_name: Optional[str] = None
    interceptor_type: Optional[str] = None
    base_latitude: Optional[float] = None  # Base location A (for visualization)
    base_longitude: Optional[float] = None  # Base location A (for visualization)
    intercept_latitude: Optional[float] = None  # Static intercept point C (calculated once)
    intercept_longitude: Optional[float] = None  # Static intercept point C (calculated once)
    time_to_intercept_s: Optional[float] = None  # Time to reach intercept point (for visualization)
    interceptor_current_latitude: Optional[float] = None  # Interceptor's current location (updated 1/second)
    interceptor_current_longitude: Optional[float] = None  # Interceptor's current location (updated 1/second)
    calculated_cost_eur: Optional[float] = None
    note: Optional[str] = None
    map_url: Optional[str] = None


class SimulationRequest(BaseModel):
    #Initial threat parameters for simulation.
    initial_latitude: float
    initial_longitude: float
    speed_ms: float
    altitude_m: float
    heading_deg: float
    duration_seconds: int = 10  # How many seconds to simulate
    report_time_start: float = 0.0  # Starting timestamp


class SimulationStep(BaseModel):
    #One second of simulation.
    second: int
    threat_latitude: float
    threat_longitude: float
    decision: InterceptDecision


class SimulationResponse(BaseModel):
    #Complete simulation results.
    initial_params: SimulationRequest
    steps: list[SimulationStep]


app = FastAPI()

# Mount static files directory for HTML/CSS/JS
APP_DIR = Path(__file__).resolve().parent
static_dir = APP_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def startup_event():
    #Initialize database on application startup.
    init_database()


@app.get("/")
def root():
    return {"Hello": "World"}


@app.get("/health")
def health():
    return {"status": "ok"}


class RadarUpdate(BaseModel):
    #Radar system update per second.
    speed_ms: float
    altitude_m: float
    heading_deg: float
    latitude: float
    longitude: float
    report_time: float | datetime


@app.post("/radar/next", response_model=RadarUpdate)
def radar_next(current: RadarUpdate) -> RadarUpdate:
    
    #Simulate radar system sending next update (1 second later).
    
    #Takes current threat position and returns where it will be after 1 second,
    #based on speed and heading. This simulates the radar system updating at 1/second frequency.
    # Move threat 1 second forward
    new_lat, new_lon = move_position(
        current.latitude,
        current.longitude,
        current.heading_deg,
        current.speed_ms,
        1.0
    )
    
    # Increment report_time by 1 second
    if isinstance(current.report_time, datetime):
        from datetime import timedelta
        new_report_time = current.report_time + timedelta(seconds=1)
    else:
        new_report_time = current.report_time + 1.0
    
    return RadarUpdate(
        speed_ms=current.speed_ms,
        altitude_m=current.altitude_m,
        heading_deg=current.heading_deg,
        latitude=new_lat,
        longitude=new_lon,
        report_time=new_report_time,
    )


@app.post("/intercept", response_model=InterceptDecision)
def intercept(report: RadarReport) -> InterceptDecision:
    #Process radar report and return interception decision.
    #Delegates to logic.calculate_intercept() for the core calculation.
    
    result = calculate_intercept(
        speed_ms=report.speed_ms,
        altitude_m=report.altitude_m,
        heading_deg=report.heading_deg,
        latitude=report.latitude,
        longitude=report.longitude,
        seconds_since_launch=report.seconds_since_launch or 0.0,
    )
    
    return InterceptDecision(**result)


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    
    #Simulate radar system sending updates every second (1/second frequency).
    
    #This endpoint demonstrates how the interceptor's current location updates every second
    #as it moves toward the static intercept point. Each second:
    #1. Threat position is updated based on speed and heading
    #2. Intercept point remains STATIC (calculated once based on initial threat position)
    #3. Interceptor's current location is updated as it moves from base toward intercept point
    
    #Takes initial threat parameters and simulates movement for duration_seconds.
    #Returns all results showing how interceptor position evolves over time.
    
    steps: list[SimulationStep] = []
    
    current_lat = request.initial_latitude
    current_lon = request.initial_longitude
    current_time = request.report_time_start
    
    for second in range(request.duration_seconds):
        # Calculate intercept decision for this position
        # seconds_since_launch tracks how long interceptor has been moving toward intercept point
        result = calculate_intercept(
            speed_ms=request.speed_ms,
            altitude_m=request.altitude_m,
            heading_deg=request.heading_deg,
            latitude=current_lat,
            longitude=current_lon,
            seconds_since_launch=float(second),  # Update interceptor position every second
        )
        
        decision = InterceptDecision(**result)
        
        # Store this step
        steps.append(SimulationStep(
            second=second,
            threat_latitude=current_lat,
            threat_longitude=current_lon,
            decision=decision,
        ))
        
        # Move threat to next position (1 second forward)
        current_lat, current_lon = move_position(
            current_lat, current_lon, request.heading_deg, request.speed_ms, 1.0
        )
        current_time += 1.0
    
    return SimulationResponse(
        initial_params=request,
        steps=steps,
    )


@app.get("/demo", response_class=HTMLResponse)
def demo() -> FileResponse:
    
    #Simple HTML page to demonstrate 1/second updates of interceptor location
    #toward a static intercept point, using the /intercept endpoint.
    
    #Serves the demo.html file from app/static/ directory.
    demo_file = APP_DIR / "static" / "demo.html"
    return FileResponse(demo_file, media_type="text/html")
