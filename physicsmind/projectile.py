"""Maximum height, time to the top, time of flight and horizontal range of a freely launched object, from a Reading
the question reader marked solvable.

Every quantity is worked out twice, by two different routes, and a number is given only when both agree:
- maximum height: SymPy solves v² = u² + 2as, and the direct formula h = u_y² / 2g;
- time to the top: SymPy solves v = u + at, and t = u_y / g;
- time of flight: SymPy solves s = ut + ½at² with s = −h₀ (it lands h₀ below the launch point), and the quadratic
  formula T = (u_y + √(u_y² + 2gh₀)) / g;
- range: SymPy solves the path equation y = x·u_y/u_x − gx²/(2u_x²) for where y = −h₀, and R = u_x·T.
Otherwise the caller is told the answer could not be checked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from sympy import Eq, Symbol, solve as sympy_solve

from .reader import HEIGHT, RANGE, SOLVABLE, T_FLIGHT, T_TOP, Reading, horizontal_launch_speed, vertical_launch_speed
from .solver import solve_kinematics

AGREEMENT = 1e-6  # relative; the SymPy result is rounded to 6 decimal places


@dataclass
class Solution:
    ok: bool
    rise: float = 0.0                   # metres above the launch point
    above_ground: float | None = None   # when it starts from a raised point
    upward_speed: float = 0.0
    sideways_speed: float | None = None
    time_to_top: float | None = None    # seconds
    time_of_flight: float | None = None  # seconds, until it reaches the ground
    range: float | None = None          # metres along the ground, from below the launch point
    problem: str = ""
    checks: list[str] = field(default_factory=list)


def _agree(first: float, second: float) -> bool:
    return math.isfinite(second) and abs(first - second) <= AGREEMENT * max(1.0, abs(second))


def _fail(problem: str) -> Solution:
    return Solution(False, problem=problem)


def solve_projectile(reading: Reading) -> Solution:
    if reading.status != SOLVABLE:
        return _fail("The question was not fully understood, so nothing was calculated.")
    asks = reading.asks or [HEIGHT]
    g, h0 = reading.g, reading.launch_height
    upward = vertical_launch_speed(reading)
    if upward is None:  # only the time to reach the top was given: v = u + at with v = 0 gives u
        found = solve_kinematics({"v": 0, "a": -g, "t": reading.time_to_top.value}, "u")
        if found["status"] != "solved":
            return _fail("The launch speed could not be worked out from the time given.")
        upward = found["value"]
        if not _agree(upward, g * reading.time_to_top.value):
            return _fail("Two ways of working out the launch speed disagreed.")
    rises = HEIGHT in asks or T_TOP in asks
    if upward < 0 or (rises and upward == 0):
        return _fail("It is not moving upward, so it does not rise.")
    solution = Solution(True, upward_speed=upward)

    if HEIGHT in asks:
        found = solve_kinematics({"u": upward, "v": 0, "a": -g}, "s")
        if found["status"] != "solved":
            return _fail(found.get("message", "The equations gave no single answer."))
        direct = upward ** 2 / (2 * g)
        if not _agree(found["value"], direct):
            return _fail(f"The two calculations of the height disagreed ({found['value']} m against {direct} m).")
        solution.rise = direct
        if reading.launch_height_written:
            solution.above_ground = h0 + direct
        solution.checks += ["SymPy solved v² = u² + 2as for s", "the direct formula h = u_y²/2g gives the same value"]

    if T_TOP in asks:
        found = solve_kinematics({"u": upward, "v": 0, "a": -g}, "t")
        direct = upward / g
        if found["status"] != "solved" or not _agree(found["value"], direct):
            return _fail("The two calculations of the time to the top disagreed.")
        solution.time_to_top = direct
        solution.checks += ["SymPy solved v = u + at for t", "t = u_y/g gives the same value"]

    if T_FLIGHT in asks or RANGE in asks:
        found = solve_kinematics({"u": upward, "a": -g, "s": -h0}, "t")
        roots = [found["value"]] if found["status"] == "solved" else found.get("values", [])
        later = [t for t in roots if t > 1e-9]  # t = 0 is the launch itself; a negative time is before the launch
        if len(later) != 1:
            return _fail("The time it reaches the ground could not be pinned down to one value.")
        direct = (upward + math.sqrt(upward ** 2 + 2 * g * h0)) / g
        if not _agree(later[0], direct):
            return _fail(f"The two calculations of the time of flight disagreed ({later[0]} s against {direct} s).")
        solution.time_of_flight = direct
        if T_FLIGHT in asks:
            solution.checks += ["SymPy solved s = ut + ½at² for t", "the quadratic formula gives the same time of flight"]

    if RANGE in asks:
        sideways = horizontal_launch_speed(reading)
        if sideways is None or sideways <= 0:
            return _fail("It has no sideways speed, so there is no range to give.")
        direct = sideways * solution.time_of_flight
        x = Symbol("x", positive=True)
        path = Eq(x * upward / sideways - g * x ** 2 / (2 * sideways ** 2), -h0)
        landings = [float(root) for root in sympy_solve(path, x) if root.is_real and float(root) > 1e-9]
        if len(landings) != 1 or not _agree(landings[0], direct):
            return _fail("The two calculations of the range disagreed.")
        solution.sideways_speed, solution.range = sideways, direct
        solution.checks += ["SymPy solved the path equation y = x·u_y/u_x − gx²/(2u_x²) for where it lands",
                            "R = u_x × T gives the same range"]
    return solution
