from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db_init import init_database
from .logic import calculate_intercept, move_position


class RadarReport(BaseModel):
    #calculates where the interceptor will intercept the threat
    speed_ms: float
    altitude_m: float
    heading_deg: float
    latitude: float
    longitude: float
    report_time: float | datetime


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database on application startup
    init_database()
    yield

# Mount static files directory for HTML/CSS/JS
APP_DIR = Path(__file__).resolve().parent
static_dir = APP_DIR / "static"

app = FastAPI(lifespan=lifespan)

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def root():
    return {"Hello": "World"}


@app.get("/health")
def health():
    return {"status": "ok"}


async def _radar_stream_generator(
    latitude: float,
    longitude: float,
    speed_ms: float,
    altitude_m: float,
    heading_deg: float,
    max_seconds: int,
):
    #Yield SSE events at 1 Hz: radar sends updated threat position to the client.
    report_time: datetime | float = datetime.now()
    lat, lon = latitude, longitude
    for second in range(max_seconds + 1):
        payload = {
            "second": second,
            "latitude": lat,
            "longitude": lon,
            "speed_ms": speed_ms,
            "altitude_m": altitude_m,
            "heading_deg": heading_deg,
            "report_time": report_time.isoformat() if isinstance(report_time, datetime) else report_time,
        }
        # Log each sent update in terminal
        print(f"radar/stream: sending update t={second}", flush=True)
        yield f"data: {json.dumps(payload)}\n\n"
        if second >= max_seconds:
            break
        lat, lon = move_position(lat, lon, heading_deg, speed_ms, 1.0)
        if isinstance(report_time, datetime):
            report_time = report_time + timedelta(seconds=1)
        else:
            report_time = report_time + 1.0
        await asyncio.sleep(1.0)


@app.get("/radar/stream")
async def radar_stream(
    latitude: float = Query(..., description="Initial threat latitude"),
    longitude: float = Query(..., description="Initial threat longitude"),
    speed_ms: float = Query(..., description="Threat speed m/s"),
    altitude_m: float = Query(..., description="Threat altitude m"),
    heading_deg: float = Query(..., description="Threat heading degrees"),
    max_seconds: int = Query(600, ge=1, le=3600, description="Max events to send (1/second)"),
):
    
    #Server-Sent Events stream: radar sends threat position updates to the demo at 1 Hz.
    #The radar system updates the information with new coordinates every second (frequency 1/second).
    
    #Note: Ensure max_seconds is >= time_to_intercept_s (from /intercept) + buffer (e.g. 30s)
    #to avoid the stream ending before the interceptor reaches the target.
    
    return StreamingResponse(
        _radar_stream_generator(latitude, longitude, speed_ms, altitude_m, heading_deg, max_seconds),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
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
        seconds_since_launch=0.0,
    )
    
    return InterceptDecision(**result)


@app.get("/demo", response_class=HTMLResponse)
def demo() -> FileResponse:
    
    #Simple HTML page to demonstrate 1/second updates of interceptor location
    #toward a static intercept point, using the /intercept endpoint.
    
    #Serves the demo.html file from app/static/ directory.
    demo_file = APP_DIR / "static" / "demo.html"
    return FileResponse(demo_file, media_type="text/html")
