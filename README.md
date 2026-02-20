# LMT Defence Threat Classification & Interception python program

A containerized Python application that classifies air threats from radar data and selects the best (most cost-effective or only feasible) interception method from three air defense bases in Latvia.

## Features

**Threat classification** by speed and altitude (NOT_THREAT, CAUTION, THREAT, POTENTIAL_THREAT)
**Interceptor selection** from bases (Riga, Liepāja, Daugavpils) and four interceptor types in SQLite database
**Static intercept point** calculated once
**Threat updates** System receives updates of threat location and shows how the threat is approaching the intercept point in 0.0.0.0:8000/demo
**API** (FastAPI) with `/intercept`, `/radar/stream` (Server Sent Events), and `/demo`
**Unit and API tests** (pytest)

## Prerequisites

Docker & Docker Compose
macOS or Linux, developed and tested on M2 Pro Macbook Pro, MacOS 15.7.3

## Quick Start (Docker)

```
docker-compose build
docker-compose up
```

API: **http://0.0.0.0:8000**
Interactive docs: **http://0.0.0.0:8000/docs**
Demo: **http://0.0.0.0:8000/demo**

The SQLite database is created on first run from `app/schema.sql`.
The SQLite database contains information of bases and each base's available interceptors.


### Example: Request interception

**POST** `/intercept`

```json
{
  "speed_ms": 60.0,
  "altitude_m": 500.0,
  "heading_deg": 90.0,
  "latitude": 56.516441,
  "longitude": 21.109256,
  "report_time": "2026-02-20T12:00:00"
}
```

**Response**: `threat_level`, `base_name`, `interceptor_type`, `base_latitude`, `base_longitude`, `intercept_latitude`, `intercept_longitude`, `time_to_intercept_s`, `calculated_cost_eur`, `map_url`

### Radar stream (1/second updates)

**GET** `/radar/stream?latitude=56.516&longitude=21.109&speed_ms=60&altitude_m=500&heading_deg=90&max_seconds=300`

Server-Sent Events stream: the radar sends one event per second with updated threat position. The radar sends info to the demo at 1 Hz.

---

## Threat Classification

**NOT_THREAT**: speed &lt; 15 m/s **or** altitude &lt; 200 m  
**CAUTION**: speed &gt; 15 m/s and speed ≤ 50 m/s (and altitude ≥ 200 m)  
**THREAT**: speed &gt; 50 m/s (and altitude ≥ 200 m)  
**POTENTIAL_THREAT**: all other cases  

See `docs/THREAT_CLASSIFICATION_SPEC.md` for information.