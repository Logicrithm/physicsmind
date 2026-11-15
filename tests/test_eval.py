"""The evaluation set (evals/questions.json) is sound, and PhysicsMind keeps its score on it."""
import math

from evals.run_eval import CATEGORIES, CORRECT, DANGEROUS, load, run

ITEMS = load()
# Score after the fixes of 15 Nov 2026. The first, blind run scored 96 (2 dangerous); see evals/first-run-2026-11-15.md.
BEST_SCORE = 100


def test_the_set_has_the_planned_shape():
    assert len(ITEMS) == 100 and len({i["id"] for i in ITEMS}) == 100
    sizes = {c: sum(i["category"] == c for i in ITEMS) for c in CATEGORIES}
    assert sizes == {"straightforward": 30, "units_and_angles": 30, "ambiguous": 20, "outside": 20}
    for item in ITEMS:
        assert item["expect"] in {"solvable", "unclear", "not_mine"} and item["question"].strip()
        assert ("given" in item) == (item["expect"] == "solvable")


def test_every_expected_height_matches_its_hand_conversion():
    # Worked again here with plain arithmetic, never with PhysicsMind's own code.
    for item in (i for i in ITEMS if i["expect"] == "solvable"):
        given, g = item["given"], item["given"].get("g", 9.8)
        if "uy" in given:
            uy = given["uy"]
        elif "t_top" in given:
            uy = g * given["t_top"]
        else:
            uy = given["u"] * math.sin(math.radians(given["angle"]))
        assert math.isclose(item["rise"], uy * uy / (2 * g), rel_tol=1e-6), item["id"]
        if "h0" in given:
            assert math.isclose(item["above_ground"], given["h0"] + item["rise"], rel_tol=1e-6), item["id"]


def test_no_wrong_or_unwanted_numbers_and_the_score_does_not_drop():
    results = run(ITEMS)
    dangerous = [f"{r.item['id']}: {r.what}" for r in results if r.kind == DANGEROUS]
    assert dangerous == []
    assert sum(r.kind == CORRECT for r in results) >= BEST_SCORE, [
        f"{r.item['id']}: {r.what}" for r in results if r.kind != CORRECT]
