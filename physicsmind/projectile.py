"""Maximum height of a freely launched object, from a Reading the question reader marked solvable.

The kinematics equations are solved with SymPy (solver.py), then the result is recomputed with the direct
formula h = u_y² / 2g. Only when both agree is a number given; otherwise the caller is told it could not be checked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from .reader import Reading, SOLVABLE, vertical_launch_speed
from .solver import solve_kinematics

AGREEMENT = 1e-6  # relative; the SymPy result is rounded to 6 decimal places


@dataclass
class Solution:
    ok: bool
    rise: float = 0.0                 # metres above the launch point
    above_ground: float | None = None  # when it starts from a raised point
    upward_speed: float = 0.0
    problem: str = ""
    checks: list[str] = field(default_factory=list)


def solve_max_height(reading: Reading) -> Solution:
    if reading.status != SOLVABLE:
        return Solution(False, problem="The question was not fully understood, so nothing was calculated.")
    g = reading.g
    upward = vertical_launch_speed(reading)
    if upward is None:  # only the time to reach the top was given: v = u + at with v = 0 gives u
        found = solve_kinematics({"v": 0, "a": -g, "t": reading.time_to_top.value}, "u")
        if found["status"] != "solved":
            return Solution(False, problem="The launch speed could not be worked out from the time given.")
        upward = found["value"]
        if abs(upward - g * reading.time_to_top.value) > AGREEMENT * max(1.0, upward):
            return Solution(False, problem="Two ways of working out the launch speed disagreed.")
    if upward <= 0:
        return Solution(False, problem="It is not moving upward, so it does not rise.")

    found = solve_kinematics({"u": upward, "v": 0, "a": -g}, "s")
    if found["status"] != "solved":
        return Solution(False, problem=found.get("message", "The equations gave no single answer."))
    direct = upward ** 2 / (2 * g)
    if not math.isfinite(direct) or abs(found["value"] - direct) > AGREEMENT * max(1.0, direct):
        return Solution(False, problem=f"The two calculations disagreed ({found['value']} m against {direct} m).")
    solution = Solution(True, rise=direct, upward_speed=upward,
                        checks=["SymPy solved v² = u² + 2as for s", "the direct formula h = u_y²/2g gives the same value"])
    if reading.launch_height_written:
        solution.above_ground = reading.launch_height + direct
    return solution
