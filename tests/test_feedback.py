from physicsmind.feedback import save_feedback, feedback_count

def test_feedback_saved(tmp_path):
    db = tmp_path / "test.db"
    save_feedback(
        response_id="response-1",
        response_type="numerical",
        question="Find displacement",
        answer="s = 20 m",
        rating="helpful",
        db_path=db
    )
    assert feedback_count(db_path=db) == 1
