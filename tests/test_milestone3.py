from wsgiref.util import setup_testing_defaults

from recurring_app.app import RecurringApp
from recurring_app.db import connect


def build_environ(path="/", method="GET", body="", cookie=""):
    environ = {}
    setup_testing_defaults(environ)
    environ["PATH_INFO"] = path
    environ["REQUEST_METHOD"] = method
    encoded = body.encode("utf-8")
    environ["wsgi.input"] = __import__("io").BytesIO(encoded)
    environ["CONTENT_LENGTH"] = str(len(encoded))
    if cookie:
        environ["HTTP_COOKIE"] = cookie
    return environ


def call(app, environ):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    body = b"".join(app(environ, start_response)).decode("utf-8")
    return captured["status"], dict(captured["headers"]), body


def login_admin(app):
    payload = "email=admin%40recurring.local&password=Admin123%21"
    _, headers, _ = call(app, build_environ("/login", "POST", payload))
    return headers["Set-Cookie"].split(";", 1)[0]


def test_ats_pipeline_board_and_candidate_profile(tmp_path):
    db_path = str(tmp_path / "app.db")
    app = RecurringApp(db_path)
    app.bootstrap()
    session_cookie = login_admin(app)

    create_payload = "title=Recruiter&department=People+Ops&location=Remote&description=Build+pipeline"
    call(app, build_environ("/admin/jobs", "POST", create_payload, session_cookie))

    with connect(db_path) as conn:
        job_id = conn.execute("SELECT id FROM jobs WHERE title='Recruiter'").fetchone()["id"]

    apply_payload = "full_name=Jordan+Lee&email=jordan%40mail.com&resume_text=8+years+recruiting"
    call(app, build_environ(f"/jobs/{job_id}/apply", "POST", apply_payload))

    with connect(db_path) as conn:
        application_id = conn.execute("SELECT id FROM applications WHERE email='jordan@mail.com'").fetchone()["id"]

    status, _, body = call(app, build_environ("/admin/ats", cookie=session_cookie))
    assert status.startswith("200")
    assert "ATS Pipeline Board" in body
    assert "Jordan Lee" in body
    assert f"/admin/applications/{application_id}" in body

    status, _, body = call(app, build_environ(f"/admin/applications/{application_id}", cookie=session_cookie))
    assert status.startswith("200")
    assert "Candidate Profile: Jordan Lee" in body
    assert "Interview Notes" in body
    assert "Tasks" in body


def test_candidate_notes_tasks_and_status_updates(tmp_path):
    db_path = str(tmp_path / "app.db")
    app = RecurringApp(db_path)
    app.bootstrap()
    session_cookie = login_admin(app)

    create_payload = "title=HRBP&department=People+Ops&location=NYC&description=Partner+with+leaders"
    call(app, build_environ("/admin/jobs", "POST", create_payload, session_cookie))

    with connect(db_path) as conn:
        job_id = conn.execute("SELECT id FROM jobs WHERE title='HRBP'").fetchone()["id"]

    apply_payload = "full_name=Alex+Kim&email=alex%40mail.com&resume_text=Strong+HR+background"
    call(app, build_environ(f"/jobs/{job_id}/apply", "POST", apply_payload))

    with connect(db_path) as conn:
        application_id = conn.execute("SELECT id FROM applications WHERE email='alex@mail.com'").fetchone()["id"]

    status_payload = "status=interview"
    status, headers, _ = call(
        app,
        build_environ(f"/admin/applications/{application_id}/status", "POST", status_payload, session_cookie),
    )
    assert status.startswith("302")
    assert headers["Location"] == f"/admin/applications/{application_id}"

    notes_payload = "note_text=Strong+communication+and+culture+fit"
    call(app, build_environ(f"/admin/applications/{application_id}/notes", "POST", notes_payload, session_cookie))

    tasks_payload = "title=Schedule+panel+interview&due_date=2026-03-01"
    call(app, build_environ(f"/admin/applications/{application_id}/tasks", "POST", tasks_payload, session_cookie))

    with connect(db_path) as conn:
        updated = conn.execute("SELECT status FROM applications WHERE id = ?", (application_id,)).fetchone()
        note = conn.execute("SELECT note_text FROM candidate_notes WHERE application_id = ?", (application_id,)).fetchone()
        task = conn.execute("SELECT id, status FROM candidate_tasks WHERE application_id = ?", (application_id,)).fetchone()
        assert updated["status"] == "interview"
        assert "Strong communication" in note["note_text"]
        task_id = task["id"]

    complete_payload = f"task_id={task_id}"
    call(app, build_environ(f"/admin/applications/{application_id}/tasks/complete", "POST", complete_payload, session_cookie))

    with connect(db_path) as conn:
        completed_task = conn.execute("SELECT status FROM candidate_tasks WHERE id = ?", (task_id,)).fetchone()
        assert completed_task["status"] == "done"

    status, _, body = call(app, build_environ(f"/admin/applications/{application_id}", cookie=session_cookie))
    assert "Strong communication and culture fit" in body
    assert "Schedule panel interview" in body
