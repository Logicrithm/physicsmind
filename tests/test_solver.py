from physicsmind.solver import solve_kinematics

def test_maximum_height():
    result = solve_kinematics({"u": 20, "v": 0, "a": -9.8}, "s")
    assert result["status"] == "solved"
    assert abs(result["value"] - 20.408163) < 1e-5
    assert result["unit"] == "m"

def test_too_few_values():
    result = solve_kinematics({"u": 10}, "s")
    assert result["status"] == "error"

def test_unknown_already_known():
    result = solve_kinematics({"u": 10, "v": 0}, "u")
    assert result["status"] == "error"

def test_ambiguous_time():
    # s=10, u=0, a=2 -> t = +/- sqrt(10); math solver reports both.
    result = solve_kinematics({"s": 10, "u": 0, "a": 2}, "t")
    assert result["status"] == "ambiguous"
    assert len(result["values"]) == 2
