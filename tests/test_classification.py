# Unit tests for threat classification.

import pytest

from app.classification import (
    NOT_THREAT,
    CAUTION,
    THREAT,
    POTENTIAL_THREAT,
    classify_threat,
)


# Edge cases from the spec

@pytest.mark.parametrize("speed_ms,altitude_m,expected", [
    (0, 0, NOT_THREAT),
    (14.9, 500, NOT_THREAT),
    (15.0, 500, POTENTIAL_THREAT),
    (15.001, 500, CAUTION),
    (50.0, 500, CAUTION),
    (50.001, 500, THREAT),
    (100, 100, NOT_THREAT),
    (100, 200, THREAT),
    (20, 199, NOT_THREAT),
    (20, 200, CAUTION),
])
def test_classify_threat_spec_cases(speed_ms: float, altitude_m: float, expected: str) -> None:
    """All 10 spec edge cases."""
    assert classify_threat(speed_ms, altitude_m) == expected


# Boundary 15 m/s

def test_speed_just_below_15_is_not_threat() -> None:
    assert classify_threat(14.999999, 1000) == NOT_THREAT


def test_speed_exactly_15_is_potential_threat() -> None:
    assert classify_threat(15.0, 200) == POTENTIAL_THREAT


def test_speed_just_above_15_is_caution() -> None:
    assert classify_threat(15.000001, 200) == CAUTION


# Boundary 50 m/s

def test_speed_just_below_50_is_caution() -> None:
    assert classify_threat(49.999999, 200) == CAUTION


def test_speed_exactly_50_is_caution() -> None:
    assert classify_threat(50.0, 200) == CAUTION


def test_speed_just_above_50_is_threat() -> None:
    assert classify_threat(50.000001, 200) == THREAT


# Boundary 200 m altitude

def test_altitude_just_below_200_is_not_threat_even_fast() -> None:
    assert classify_threat(100, 199.999) == NOT_THREAT


def test_altitude_exactly_200_with_high_speed_is_threat() -> None:
    assert classify_threat(60, 200.0) == THREAT

# Return value is one of the four possible

def test_return_value_is_known_label() -> None:
    known = {NOT_THREAT, CAUTION, THREAT, POTENTIAL_THREAT}
    for speed in (0, 20, 60):
        for alt in (0, 300):
            result = classify_threat(speed, alt)
            assert result in known, f"classify_threat({speed}, {alt}) returned {result!r}"
