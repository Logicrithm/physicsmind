"""The evaluation set (evals/questions.json) is sound, and PhysicsMind keeps its score on it."""
import math

from evals.run_eval import CATEGORIES, CORRECT, DANGEROUS, load, run

ITEMS = load()
# Score after the fixes of 15 Nov 2026. Blind first runs: 96 / 100 with 2 dangerous (evals/first-run-2026-11-15.md),
# then 139 / 140 with none dangerous once time of flight and range were added (evals/first-run-flight-2026-11-15.md).
BEST_SCORE = 140


def test_the_set_has_the_planned_shape():
    assert len(ITEMS) == 140 and len({i["id"] for i in ITEMS}) == 140
    sizes = {c: sum(i["category"] == c for i in ITEMS) for c in CATEGORIES}
    assert sizes == {"straightforward": 30, "units_and_angles": 30, "flight_and_range": 30, "ambiguous": 30, "outside": 20}
    for item in ITEMS:
        assert item["expect"] in {"solvable", "unclear", "not_mine"} and item["question"].strip()
        assert ("given" in item) == (item["expect"] == "solvable")
        if item["expect"] == "solvable":
            assert item["asks"] and set(item["asks"]) <= {"height", "t_top", "t_flight", "range"}


def test_every_expected_value_matches_its_hand_working():
    # Worked again here with plain arithmetic, never with PhysicsMind's own code.
    for item in (i for i in ITEMS if i["expect"] == "solvable"):
        given, g = item["given"], item["given"].get("g", 9.8)
        h0, ux = given.get("h0", 0.0), None
        if "uy" in given:
            uy = given["uy"]
        elif "t_top" in given:
            uy = g * given["t_top"]
        else:
            uy = given["u"] * math.sin(math.radians(given["angle"]))
            ux = given["u"] * math.cos(math.radians(given["angle"]))
        flight = (uy + math.sqrt(uy * uy + 2 * g * h0)) / g
        want = {}
        if "height" in item["asks"]:
            want["rise"] = uy * uy / (2 * g)
            if "h0" in given:
                want["above_ground"] = h0 + uy * uy / (2 * g)
        if "t_top" in item["asks"]:
            want["t_top"] = uy / g
        if "t_flight" in item["asks"]:
            want["t_flight"] = flight
        if "range" in item["asks"]:
            want["range"] = ux * flight
        stored = {k: item[k] for k in ("rise", "above_ground", "t_top", "t_flight", "range") if k in item}
        assert stored.keys() == want.keys(), item["id"]
        for key, value in want.items():
            assert math.isclose(stored[key], value, rel_tol=1e-6), (item["id"], key)


def test_spot_checks_worked_by_hand():
    # A few answers worked on paper, so a shared mistake in the formulas above would still be caught.
    by_id = {i["id"]: i for i in ITEMS}
    assert math.isclose(by_id["E10"]["t_flight"], 3.0) and math.isclose(by_id["E10"]["range"], 45.0)  # √(2·45/10) = 3 s; 15·3
    assert math.isclose(by_id["E07"]["t_flight"], 4.0)    # 2 · 19.6 / 9.8
    assert math.isclose(by_id["E03"]["range"], 22.5)      # 15² · sin 90° / 10
    assert math.isclose(by_id["E20"]["t_flight"], 2.0)    # √(2 · 19.6 / 9.8)


def test_no_wrong_or_unwanted_numbers_and_the_score_does_not_drop():
    results = run(ITEMS)
    dangerous = [f"{r.item['id']}: {r.what}" for r in results if r.kind == DANGEROUS]
    assert dangerous == []
    assert sum(r.kind == CORRECT for r in results) >= BEST_SCORE, [
        f"{r.item['id']}: {r.what}" for r in results if r.kind != CORRECT]
