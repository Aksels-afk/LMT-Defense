from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from .logic import calculate_intercept, move_position


class RadarReport(BaseModel):
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
    intercept_latitude: Optional[float] = None
    intercept_longitude: Optional[float] = None
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


@app.get("/")
def root():
    return {"Hello": "World"}


@app.get("/health")
def health():
    return {"status": "ok"}


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
    )
    
    return InterceptDecision(**result)


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    #Simulate radar system sending updates every second.
    #Takes initial threat parameters and simulates movement for duration_seconds.
    #Each second, calculates new threat position and runs intercept logic.
    #Returns all results showing how intercept point evolves over time.
    
    steps: list[SimulationStep] = []
    
    current_lat = request.initial_latitude
    current_lon = request.initial_longitude
    current_time = request.report_time_start
    
    for second in range(request.duration_seconds):
        # Calculate intercept decision for this position
        result = calculate_intercept(
            speed_ms=request.speed_ms,
            altitude_m=request.altitude_m,
            heading_deg=request.heading_deg,
            latitude=current_lat,
            longitude=current_lon,
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
