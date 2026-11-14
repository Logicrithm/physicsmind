"""Deterministic constant-acceleration kinematics solver.

All inputs must be numeric SI values:
u, v in m/s; a in m/s^2; s in m; t in seconds.
"""
from sympy import Eq, symbols, solve, sympify

UNITS = {"u": "m/s", "v": "m/s", "a": "m/s²", "s": "m", "t": "s"}
u, v, a, s, t = symbols("u v a s t", real=True)
SYMBOLS = {"u": u, "v": v, "a": a, "s": s, "t": t}

EQUATIONS = [
    Eq(v, u + a * t),
    Eq(s, u * t + a * t**2 / 2),
    Eq(v**2, u**2 + 2 * a * s),
    Eq(s, (u + v) * t / 2),
]

def solve_kinematics(known: dict, unknown: str) -> dict:
    if unknown not in SYMBOLS:
        return {"status": "error", "message": "Unsupported unknown variable."}
    if len(known) < 2:
        return {"status": "error", "message": "Enter at least two known values."}
    if unknown in known:
        return {"status": "error", "message": f"Remove the value for {unknown}; it is selected as the unknown."}
    if any(key not in SYMBOLS for key in known):
        return {"status": "error", "message": "Unsupported variable supplied."}

    try:
        substitutions = {SYMBOLS[key]: sympify(value) for key, value in known.items()}
    except (TypeError, ValueError):
        return {"status": "error", "message": "Values must be valid numbers."}

    target = SYMBOLS[unknown]
    candidates = []
    for equation in EQUATIONS:
        reduced = equation.subs(substitutions)
        if target not in reduced.free_symbols:
            continue
        try:
            solutions = solve(reduced, target)
        except (NotImplementedError, ValueError):
            continue
        for candidate in solutions:
            try:
                numeric = complex(candidate.evalf())
                if abs(numeric.imag) < 1e-10:
                    value = float(numeric.real)
                    if all(abs(value - old) > 1e-8 for old in candidates):
                        candidates.append(value)
            except (TypeError, ValueError):
                continue

    if not candidates:
        return {
            "status": "error",
            "message": "No solution found from the supported equations. Check the values, SI units and whether enough information was provided."
        }

    candidates.sort()
    if len(candidates) > 1:
        return {
            "status": "ambiguous",
            "values": [round(value, 6) for value in candidates],
            "unit": UNITS[unknown],
            "steps": ["The equations produce multiple mathematical solutions.", "Additional physical context is needed to choose the applicable solution."]
        }

    value = candidates[0]
    steps = [
        "Identify the known quantities and the unknown.",
        "Use a standard constant-acceleration kinematics equation.",
        "Substitute the supplied SI values and solve for the unknown.",
        f"Result: {unknown} = {value:.6g} {UNITS[unknown]}."
    ]
    return {"status": "solved", "value": round(value, 6), "unit": UNITS[unknown], "steps": steps}
