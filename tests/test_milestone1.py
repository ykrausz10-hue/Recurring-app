from wsgiref.util import setup_testing_defaults

from recurring_app.app import RecurringApp


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


def test_login_and_dashboard(tmp_path):
    db_path = str(tmp_path / "app.db")
    app = RecurringApp(db_path)
    app.bootstrap()

    status, _, _ = call(app, build_environ("/dashboard"))
    assert status.startswith("302")

    payload = "email=admin%40recurring.local&password=Admin123%21"
    status, headers, _ = call(app, build_environ("/login", "POST", payload))
    assert status.startswith("302")
    assert headers["Location"] == "/dashboard"

    session_cookie = headers["Set-Cookie"].split(";", 1)[0]
    status, _, body = call(app, build_environ("/dashboard", cookie=session_cookie))
    assert status.startswith("200")
    assert "Benefit Enrollment" in body


def test_rbac_forbidden_for_employee(tmp_path):
    db_path = str(tmp_path / "app.db")
    app = RecurringApp(db_path)
    app.bootstrap()

    payload = "email=employee%40recurring.local&password=Employee123%21"
    _, headers, _ = call(app, build_environ("/login", "POST", payload))
    session_cookie = headers["Set-Cookie"].split(";", 1)[0]

    status, _, body = call(app, build_environ("/admin", cookie=session_cookie))
    assert status.startswith("403")
    assert "Access denied" in body
