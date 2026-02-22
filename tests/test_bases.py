# Test if bases are intercepting threats correctly, based on rules of available interceptors and taking consideration of costs.
# Test 1.1: ~2 km from Liepaja base at low altitude, should send drone (drone range 3000 m).
# Test 1.2: 1Km from Liepaja base at low altitude, should send 50Cal.
# Test 2.1: 20Km from Riga base at high altitude, should send Rocket.
# Test 2.2: 1Km from Riga base at high altitude, should send Fighter jet.
# Test 2.3: 1Km from Riga base at low altitude, should send 50Cal.
# Test 2.4: 20Km from Riga base at low altitude, should send Rocket (drone range 3000 m).
# Test 3.1: 20Km from Daugavpils base at low altitude, should send Rocket (drone range 3000 m).
# Test 3.2: 1Km from Daugavpils base at low altitude, should send 50Cal.
# Test 3.3: 20Km from Daugavpils base at high altitude, should send Rocket.

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# Test 1.1: 2.5 km from Liepaja base, should send drone
def test_liepaja_20km_uses_drone() -> None:
    
    # Threat 2.5 km from Liepaja at low altitude
    # Should send drone
    
    threat_lat = 56.504919
    threat_lon = 21.052076

    payload = {
        "speed_ms": 60.0,
        "altitude_m": 500.0,
        "heading_deg": 270.0,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Liepaja"
    assert data["interceptor_type"] == "Interceptor drone"

# Test 1.2: 1KM from liepaja base, should send 50Cal.
def test_liepaja_1km_uses_50cal() -> None:
    # Given the threat is about 1km from Liepaja base,
    # We should send 50Cal since it would be the cost-effective option.

    # Approximate 1km from Liepaja base.
    threat_lat = 56.515189
    threat_lon = 21.022489

    payload = {
        "speed_ms": 500,
        "altitude_m": 1900,
        "heading_deg": 60,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Liepaja"
    assert data["interceptor_type"] == "50Cal"

# Test 2.1: 20Km from Riga base, should send Rocket.
def test_riga_20km_uses_rocket() -> None:
    # Given the threat is about 20km from Riga base,
    # We should send Rocket

    #Approximate 20km from Riga base
    threat_lat = 56.946797
    threat_lon = 24.275403

    payload = {
        "speed_ms": 1400,
        "altitude_m": 15000,
        "heading_deg": 90,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["base_name"] == "Riga"
    assert data["interceptor_type"] == "Rocket"

# Test 2.2: 1Km from Riga base at high altitude, should send Fighter jet.
def test_riga_1km_uses_fighter_jet() -> None:
    # Given the threat is about 1km from Riga base at high altitude,
    # We should send Fighter jet

    #Approximate 1km from Riga base at high altitude
    threat_lat = 56.975734
    threat_lon = 24.175480

    payload = {
        "speed_ms": 600,
        "altitude_m": 14000,
        "heading_deg": 270,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Riga"
    assert data["interceptor_type"] == "Fighter jet"

# Test 2.3: 1Km from Riga base at low altitude, should send 50Cal.
def test_riga_1km_uses_50cal() -> None:
    # Given the threat is about 1km from Riga base and at low altitude,
    # We should use 50Cal.

    #Approximate 1km from Riga base at low altitude
    threat_lat = 56.976967
    threat_lon = 24.164971

    payload = {
        "speed_ms": 500,
        "altitude_m": 200,
        "heading_deg": 180,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Riga"
    assert data["interceptor_type"] == "50Cal"

# Test 2.4: 20Km from Riga base at low altitude, should send Rocket (drone range only 3000 m).
def test_riga_20km_uses_drone() -> None:
    # Given the threat is about 20 km from Riga base at low altitude,
    # Drone (3000 m) and Fighter (3500 m) and 50Cal (2000 m) are out of range; Rocket (100 km) is used.

    threat_lat = 56.946479
    threat_lon = 24.104754

    payload = {
        "speed_ms": 60,
        "altitude_m": 1000,
        "heading_deg": 60,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Riga"
    assert data["interceptor_type"] == "Rocket"

# Test 3.1: 20Km from Daugavpils base at low altitude, should send Rocket (drone range only 3000 m).
def test_daugavpils_20km_uses_drone() -> None:
    # Threat ~20 km from Daugavpils at low altitude; drone (3000 m) and 50Cal (2000 m) out of range; Rocket (100 km) used.

    threat_lat = 55.887715
    threat_lon = 26.608051

    payload = {
        "speed_ms": 60,
        "altitude_m": 1000,
        "heading_deg": 0,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Daugavpils"
    assert data["interceptor_type"] == "Rocket"

# Test 3.2: 1Km from Daugavpils base at low altitude, should send 50Cal.
def test_daugavpils_1km_uses_50cal() -> None:
    #Given the threat is about 1km from Daugavpils base at low altitude,
    # Should send 50Cal.

    #Approximate 1km from Daugavpils base at low altitude
    threat_lat = 55.874434
    threat_lon = 26.524831

    payload = {
        "speed_ms": 500,
        "altitude_m": 200,
        "heading_deg": 180,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }

    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Daugavpils"
    assert data["interceptor_type"] == "50Cal"

# Test 3.3: 20Km from Daugavpils base at high altitude, should send Rocket.
def test_daugavpils_20km_uses_rocket() -> None:
    # Given the threat is about 20km from Daugavpils base at high altitude,
    # We should use Rocket

    # Approximate 20km from Daugavpils base at high altitude
    threat_lat = 55.887715
    threat_lon = 26.608051

    payload = {
        "speed_ms": 1400,
        "altitude_m": 15000,
        "heading_deg": 10,
        "latitude": threat_lat,
        "longitude": threat_lon,
        "report_time": datetime.now().isoformat(),
    }
    
    response = client.post("/intercept", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["base_name"] == "Daugavpils"
    assert data["interceptor_type"] == "Rocket"

