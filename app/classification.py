# Valid return values
NOT_THREAT = "NOT_THREAT"
CAUTION = "CAUTION"
THREAT = "THREAT"
POTENTIAL_THREAT = "POTENTIAL_THREAT"


def classify_threat(speed_ms: float, altitude_m: float) -> str:
    """
    Classify a track as NOT_THREAT, CAUTION, THREAT, or POTENTIAL_THREAT.

    Args:
        speed_ms: Speed in metres per second.
        altitude_m: Altitude in metres.

    Returns:
        One of: NOT_THREAT, CAUTION, THREAT, POTENTIAL_THREAT.
    """
    # Rule order (first match wins):
    # 1. If speed < 15 OR altitude < 200 then NOT_THREAT
    # 2. If speed > 50 then THREAT
    # 3. If speed > 15 then CAUTION
    # 4. Else then POTENTIAL_THREAT
    
    if speed_ms < 15 or altitude_m < 200:
        return NOT_THREAT
    
    if speed_ms > 50:
        return THREAT
    
    if speed_ms > 15:
        return CAUTION
    
    return POTENTIAL_THREAT
