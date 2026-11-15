import json
import sqlite3
import urllib.error

import pytest

from physicsmind import feedback
from physicsmind.feedback import (FeedbackNotSaved, LocalStore, OnlineStore, choose_store, feedback_count,
                                  init_db, save_feedback)


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


# ---- added 15 Nov 2026: the app version column, and the online store used when PhysicsMind is live ----

ROW = dict(response_id="r1", response_type="solver", question="Find the maximum height", answer="20.41 m",
           rating="helpful", issue_category="No issue", comment="", model="PhysicsMind solver (SymPy)",
           verification_status="checked", app_version="0.2.0 · abc1234")


def test_an_old_feedback_file_gains_the_version_column_and_keeps_its_rows(tmp_path):
    db = tmp_path / "old.db"
    with sqlite3.connect(db) as conn:  # the layout used before 15 Nov 2026
        conn.execute("""CREATE TABLE response_feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, response_id TEXT NOT NULL,
            created_at TEXT NOT NULL, response_type TEXT NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL,
            model TEXT, rating TEXT NOT NULL, issue_category TEXT, comment TEXT, verification_status TEXT)""")
        conn.execute("INSERT INTO response_feedback (response_id, created_at, response_type, question, answer, rating) "
                     "VALUES ('old', '2026-11-12', 'numerical', 'q', 'a', 'helpful')")
    init_db(db)
    init_db(db)  # running twice is harmless
    LocalStore(db).save(**ROW)
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT response_id, question, app_version FROM response_feedback ORDER BY id").fetchall()
    assert rows == [("old", "q", None), ("r1", "Find the maximum height", "0.2.0 · abc1234")]


def test_a_bad_rating_is_refused():
    with pytest.raises(ValueError):
        LocalStore().save(**{**ROW, "rating": "great"})


class FakeResponse:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSend:
    def __init__(self, status=201, error=None):
        self.status, self.error, self.requests = status, error, []

    def __call__(self, request, timeout):
        self.requests.append(request)
        if self.error:
            raise self.error
        return FakeResponse(self.status)


def test_online_feedback_is_sent_as_one_row_with_the_publishable_key():
    send = FakeSend()
    OnlineStore("https://abc.supabase.co/", "sb_publishable_123", send).save(**ROW)
    (request,) = send.requests
    assert request.full_url == "https://abc.supabase.co/rest/v1/response_feedback"
    assert request.get_method() == "POST"
    assert request.get_header("Apikey") == "sb_publishable_123"
    assert request.get_header("Authorization") is None  # a publishable key is not a JWT
    assert request.get_header("Prefer") == "return=minimal"  # the key may add rows but not read them back
    body = json.loads(request.data)
    assert body["question"] == "Find the maximum height" and body["app_version"] == "0.2.0 · abc1234"
    assert body["created_at"].endswith("+00:00")


def test_an_older_jwt_anon_key_is_also_sent_as_a_bearer_token():
    send = FakeSend()
    OnlineStore("https://abc.supabase.co", "eyJhbGciOi.test", send).save(**ROW)
    assert send.requests[0].get_header("Authorization") == "Bearer eyJhbGciOi.test"


def test_very_long_text_is_cut_before_it_is_stored():
    send = FakeSend()
    OnlineStore("https://abc.supabase.co", "key", send).save(**{**ROW, "comment": "x" * 5000})
    assert len(json.loads(send.requests[0].data)["comment"]) == 1000


@pytest.mark.parametrize("error, says", [
    (urllib.error.HTTPError("u", 401, "Unauthorized", {}, None), "HTTP 401"),
    (urllib.error.URLError("offline"), "could not be reached"),
], ids=["refused", "offline"])
def test_a_failed_online_save_says_so_without_showing_the_key(error, says):
    with pytest.raises(FeedbackNotSaved) as caught:
        OnlineStore("https://abc.supabase.co", "secret-key", FakeSend(error=error)).save(**ROW)
    assert says in str(caught.value) and "secret-key" not in str(caught.value)


def test_the_online_store_is_used_only_when_both_settings_are_present(monkeypatch):
    assert isinstance(choose_store(), LocalStore)
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    assert isinstance(choose_store(), LocalStore)
    monkeypatch.setenv("SUPABASE_KEY", "sb_publishable_123")
    store = choose_store()
    assert isinstance(store, OnlineStore) and store.count() is None and store.where == "online"


def test_tests_never_use_the_real_feedback_file():
    assert feedback.DEFAULT_DB.name == "feedback.db"
    assert "physicsmind_phase1" not in str(feedback.DEFAULT_DB)


@pytest.mark.parametrize("pasted", ["https://abc.supabase.co", "https://abc.supabase.co/", "https://abc.supabase.co/rest/v1/",
                                    " https://abc.supabase.co/rest/v1 "])
def test_the_project_url_works_however_it_was_copied(pasted):
    send = FakeSend()
    OnlineStore(pasted, " sb_publishable_123 ", send).save(**ROW)
    assert send.requests[0].full_url == "https://abc.supabase.co/rest/v1/response_feedback"
    assert send.requests[0].get_header("Apikey") == "sb_publishable_123"
