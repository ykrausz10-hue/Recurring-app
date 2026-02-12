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


def test_admin_can_create_update_and_delete_job(tmp_path):
    db_path = str(tmp_path / "app.db")
    app = RecurringApp(db_path)
    app.bootstrap()
    session_cookie = login_admin(app)

    create_payload = "title=Payroll+Specialist&department=Finance&location=Remote&description=Run+weekly+payroll"
    status, headers, _ = call(app, build_environ("/admin/jobs", "POST", create_payload, session_cookie))
    assert status.startswith("302")
    assert headers["Location"] == "/admin/jobs"

    with connect(db_path) as conn:
        job = conn.execute("SELECT * FROM jobs WHERE title = 'Payroll Specialist'").fetchone()
        assert job is not None
        job_id = job["id"]

    update_payload = "title=Senior+Payroll+Specialist&department=Finance&location=Remote&description=Lead+payroll&status=closed"
    status, _, _ = call(app, build_environ(f"/admin/jobs/{job_id}/update", "POST", update_payload, session_cookie))
    assert status.startswith("302")

    with connect(db_path) as conn:
        updated = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        assert updated["title"] == "Senior Payroll Specialist"
        assert updated["status"] == "closed"

    status, _, _ = call(app, build_environ(f"/admin/jobs/{job_id}/delete", "POST", cookie=session_cookie))
    assert status.startswith("302")

    with connect(db_path) as conn:
        deleted = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        assert deleted is None


def test_admin_jobs_form_shows_errors_and_new_job_in_existing_list(tmp_path):
    db_path = str(tmp_path / "app.db")
    app = RecurringApp(db_path)
    app.bootstrap()
    session_cookie = login_admin(app)

    status, _, body = call(app, build_environ("/admin/jobs", cookie=session_cookie))
    assert status.startswith("200")
    assert "type='submit'" in body
    assert ">Create Job<" in body

    invalid_payload = "title=&department=Finance&location=Remote&description="
    status, _, body = call(app, build_environ("/admin/jobs", "POST", invalid_payload, session_cookie))
    assert status.startswith("200")
    assert "All job fields are required." in body

    create_payload = "title=Office+Manager&department=Operations&location=Denver&description=Coordinate+office+operations"
    status, headers, _ = call(app, build_environ("/admin/jobs", "POST", create_payload, session_cookie))
    assert status.startswith("302")
    assert headers["Location"] == "/admin/jobs"

    status, _, body = call(app, build_environ("/admin/jobs", cookie=session_cookie))
    assert status.startswith("200")
    assert "Existing Jobs" in body
    assert "Office Manager" in body


def test_public_jobs_page_and_apply_flow(tmp_path):
    db_path = str(tmp_path / "app.db")
    app = RecurringApp(db_path)
    app.bootstrap()
    session_cookie = login_admin(app)

    create_payload = "title=HR+Generalist&department=People+Ops&location=Austin%2C+TX&description=Support+employee+lifecycle"
    call(app, build_environ("/admin/jobs", "POST", create_payload, session_cookie))

    status, _, body = call(app, build_environ("/jobs"))
    assert status.startswith("200")
    assert "HR Generalist" in body

    with connect(db_path) as conn:
        job = conn.execute("SELECT id FROM jobs WHERE title = 'HR Generalist'").fetchone()
        job_id = job["id"]

    status, _, body = call(app, build_environ(f"/jobs/{job_id}/apply"))
    assert status.startswith("200")
    assert "Apply for HR Generalist" in body

    apply_payload = "full_name=Taylor+Green&email=taylor%40mail.com&resume_text=5+years+in+HR"
    status, _, body = call(app, build_environ(f"/jobs/{job_id}/apply", "POST", apply_payload))
    assert status.startswith("200")
    assert "Application submitted" in body

    with connect(db_path) as conn:
        app_row = conn.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,)).fetchone()
        assert app_row is not None
        assert app_row["email"] == "taylor@mail.com"
