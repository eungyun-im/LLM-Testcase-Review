"""Hand-seeded defect versions of the AEB-lite decision (F1 to F7).

Each one is a mistake a developer could plausibly make. They are used only to
evaluate test sets, never as feedback to the generator.
"""

from sut.aeb import (
    Action,
    BRAKE_SPEED_KPH,
    DETECT_RANGE_M,
    SENSOR_TIMEOUT_MS,
    SPEED_MAX,
    SPEED_MIN,
)


def _decide(speed_kph, obstacle_m, sensor_age_ms, *, speed_ok=None, stale=None, brake=None):
    """Reference structure with one replaceable predicate."""
    speed_ok = speed_ok or (lambda v: SPEED_MIN <= v <= SPEED_MAX)
    stale = stale or (lambda age: age >= SENSOR_TIMEOUT_MS)
    brake = brake or (
        lambda v, d: v >= BRAKE_SPEED_KPH and d is not None and d <= DETECT_RANGE_M
    )
    if not speed_ok(speed_kph):
        return Action.FAULT
    if stale(sensor_age_ms):
        return Action.FAULT
    if brake(speed_kph, obstacle_m):
        return Action.BRAKE
    return Action.NO_ACTION


def f1_speed_threshold_exclusive(speed_kph, obstacle_m, sensor_age_ms):
    return _decide(
        speed_kph, obstacle_m, sensor_age_ms,
        brake=lambda v, d: v > BRAKE_SPEED_KPH and d is not None and d <= DETECT_RANGE_M,
    )


def f2_range_exclusive(speed_kph, obstacle_m, sensor_age_ms):
    return _decide(
        speed_kph, obstacle_m, sensor_age_ms,
        brake=lambda v, d: v >= BRAKE_SPEED_KPH and d is not None and d < DETECT_RANGE_M,
    )


def f3_timeout_exclusive(speed_kph, obstacle_m, sensor_age_ms):
    return _decide(
        speed_kph, obstacle_m, sensor_age_ms, stale=lambda age: age > SENSOR_TIMEOUT_MS
    )


def f4_upper_speed_unchecked(speed_kph, obstacle_m, sensor_age_ms):
    return _decide(speed_kph, obstacle_m, sensor_age_ms, speed_ok=lambda v: v >= SPEED_MIN)


def f5_no_obstacle_as_zero(speed_kph, obstacle_m, sensor_age_ms):
    return _decide(
        speed_kph, obstacle_m, sensor_age_ms,
        brake=lambda v, d: v >= BRAKE_SPEED_KPH and (d or 0.0) <= DETECT_RANGE_M,
    )


def f6_brake_before_sensor_check(speed_kph, obstacle_m, sensor_age_ms):
    if not (SPEED_MIN <= speed_kph <= SPEED_MAX):
        return Action.FAULT
    if speed_kph >= BRAKE_SPEED_KPH and obstacle_m is not None and obstacle_m <= DETECT_RANGE_M:
        return Action.BRAKE
    if sensor_age_ms >= SENSOR_TIMEOUT_MS:
        return Action.FAULT
    return Action.NO_ACTION


def f7_distance_rounded(speed_kph, obstacle_m, sensor_age_ms):
    return _decide(
        speed_kph, obstacle_m, sensor_age_ms,
        brake=lambda v, d: v >= BRAKE_SPEED_KPH and d is not None and round(d) <= DETECT_RANGE_M,
    )


SEEDED = {
    "F1": ("boundary operator", "Brake threshold uses > instead of >=", f1_speed_threshold_exclusive),
    "F2": ("boundary operator", "Detection range uses < instead of <=", f2_range_exclusive),
    "F3": ("boundary operator", "Sensor timeout uses > instead of >=", f3_timeout_exclusive),
    "F4": ("missing check", "Upper speed limit is not checked", f4_upper_speed_unchecked),
    "F5": ("null handling", "No obstacle is treated as distance 0", f5_no_obstacle_as_zero),
    "F6": ("check order", "Brake condition is evaluated before the sensor age check", f6_brake_before_sensor_check),
    "F7": ("numeric conversion", "Distance is rounded before the range comparison", f7_distance_rounded),
}
