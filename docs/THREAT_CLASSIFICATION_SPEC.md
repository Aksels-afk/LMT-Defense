# [AI] - For outlining specs
# Threat classification – rules and edge cases to test

## Input (from radar)

- `speed_ms` (float): speed in m/s  
- `altitude_m` (float): altitude in metres  
- (heading, lat, long, report_time are not used for classification)

## Output (one of four labels)

- `NOT_THREAT`
- `CAUTION`
- `THREAT`
- `POTENTIAL_THREAT`

## Rules

1. **NOT_THREAT**  
   If speed < 15 OR altitude < 200, not a threat.

2. **THREAT**  
   If speed > 50, threat.

3. **CAUTION**  
   If speed > 15 & < 50, caution.

4. **POTENTIAL_THREAT** All other cases.

So after step 1, only consider targets with speed ≥ 15 and altitude ≥ 200.  
Then: speed > 50 is THREAT; else speed > 15 - CAUTION; else - POTENTIAL_THREAT.

## Edge cases to test

| # | speed_ms | altitude_m | Expected      | Why |
|---|----------|------------|---------------|-----|
| 1 | 0        | 0          | NOT_THREAT    | Both below thresholds |
| 2 | 14.9     | 500        | NOT_THREAT    | Speed below 15 |
| 3 | 15.0     | 500        | POTENTIAL_THREAT | Speed not > 15, so counts as potential threat |
| 4 | 15.001   | 500        | CAUTION       | Speed > 15, not > 50 |
| 5 | 50.0     | 500        | CAUTION       | Speed > 15, 50 is not > 50 |
| 6 | 50.001   | 500        | THREAT        | Speed > 50 |
| 7 | 100      | 100        | NOT_THREAT    | Altitude < 200 (checked first) |
| 8 | 100      | 200        | THREAT        | Altitude ≥ 200, speed > 50 |
| 9 | 20       | 199        | NOT_THREAT    | Altitude < 200 |
|10 | 20       | 200        | CAUTION       | Altitude ≥ 200, 15 < speed ≤ 50 |

