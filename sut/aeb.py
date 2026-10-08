"""Reference implementation of the AEB-lite decision (the oracle).

Frozen copy of src/aeb.py from the automotive-sw-qa repository. Mutant IDs are
derived from this file, so any edit here changes them.
"""

from enum import Enum


class Action(Enum):
    NO_ACTION = "NO_ACTION"
    BRAKE = "BRAKE"
    FAULT = "FAULT"


SPEED_MIN, SPEED_MAX = 0.0, 250.0
BRAKE_SPEED_KPH = 30.0
DETECT_RANGE_M = 20.0
SENSOR_TIMEOUT_MS = 200


def decide(speed_kph, obstacle_m, sensor_age_ms):
    if not (SPEED_MIN <= speed_kph <= SPEED_MAX):
        return Action.FAULT
    if sensor_age_ms >= SENSOR_TIMEOUT_MS:
        return Action.FAULT
    if (
        speed_kph >= BRAKE_SPEED_KPH
        and obstacle_m is not None
        and obstacle_m <= DETECT_RANGE_M
    ):
        return Action.BRAKE
    return Action.NO_ACTION
