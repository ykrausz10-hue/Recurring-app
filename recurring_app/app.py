from __future__ import annotations

from http import cookies
from typing import Callable
from urllib.parse import parse_qs

from .auth import SessionUser, make_session_token, verify_password
from .db import connect, init_db
from .seed import seed_default_users


class RecurringApp:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.sessions: dict[str, SessionUser] = {}

    def bootstrap(self) -> None:
        init_db(self.db_path)
        seed_default_users(self.db_path)

    def __call__(self, environ, start_response):
        method = environ["REQUEST_METHOD"]
        path = environ.get("PATH_INFO", "/")
        user = self._current_user(environ)

        if path == "/":
            return self._redirect(start_response, "/dashboard" if user else "/login")
        if path == "/login" and method == "GET":
            return self._ok(start_response, self._render_login())
        if path == "/login" and method == "POST":
            return self._handle_login(environ, start_response)
        if path == "/logout" and method == "POST":
            return self._handle_logout(environ, start_response)
        if path == "/dashboard" and method == "GET":
            if not user:
                return self._redirect(start_response, "/login")
            return self._ok(start_response, self._render_dashboard(user))
        if path == "/admin" and method == "GET":
            if not user:
                return self._redirect(start_response, "/login")
            if user.role != "admin":
                return self._forbidden(start_response, self._render_forbidden(user))
            return self._ok(start_response, self._render_admin())

        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Not Found"]

    def _parse_form(self, environ) -> dict[str, str]:
        length = int(environ.get("CONTENT_LENGTH") or "0")
        body = environ["wsgi.input"].read(length).decode("utf-8")
        parsed = parse_qs(body)
        return {k: v[0] for k, v in parsed.items()}

    def _handle_login(self, environ, start_response):
        data = self._parse_form(environ)
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        with connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if not row or not verify_password(password, row["password_hash"]):
            return self._unauthorized(start_response, self._render_login("Invalid email or password."))

        token = make_session_token()
        self.sessions[token] = SessionUser(
            user_id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            role=row["role"],
        )
        headers = self._cookie_headers(token)
        headers.append(("Location", "/dashboard"))
        start_response("302 Found", headers)
        return [b""]

    def _handle_logout(self, environ, start_response):
        token = self._session_token(environ)
        if token and token in self.sessions:
            del self.sessions[token]
        start_response("302 Found", [("Set-Cookie", "session=; Max-Age=0; Path=/"), ("Location", "/login")])
        return [b""]

    def _current_user(self, environ) -> SessionUser | None:
        token = self._session_token(environ)
        if not token:
            return None
        return self.sessions.get(token)

    def _session_token(self, environ) -> str | None:
        cookie_header = environ.get("HTTP_COOKIE", "")
        if not cookie_header:
            return None
        jar = cookies.SimpleCookie()
        jar.load(cookie_header)
        session = jar.get("session")
        return session.value if session else None

    def _cookie_headers(self, token: str) -> list[tuple[str, str]]:
        return [
            ("Set-Cookie", f"session={token}; Path=/; HttpOnly; SameSite=Lax"),
        ]

    def _redirect(self, start_response, location: str):
        start_response("302 Found", [("Location", location)])
        return [b""]

    def _ok(self, start_response, html: str):
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [html.encode("utf-8")]

    def _unauthorized(self, start_response, html: str):
        start_response("401 Unauthorized", [("Content-Type", "text/html; charset=utf-8")])
        return [html.encode("utf-8")]

    def _forbidden(self, start_response, html: str):
        start_response("403 Forbidden", [("Content-Type", "text/html; charset=utf-8")])
        return [html.encode("utf-8")]

    def _render_login(self, error: str = "") -> str:
        return f"""
<!doctype html><html><head><title>Login</title>{STYLE}</head><body>
<div class='shell'><div class='card'><h1>Recurring App Login</h1>
{'<p class="error">'+error+'</p>' if error else ''}
<form method='post' action='/login'>
<label>Email <input type='email' name='email' required></label>
<label>Password <input type='password' name='password' required></label>
<button type='submit'>Sign in</button></form>
<p class='hint'>admin@recurring.local / Admin123!</p></div></div></body></html>
"""

    def _render_dashboard(self, user: SessionUser) -> str:
        tiles = [
            ("Open Payroll Runs", "03", "all"),
            ("Pending Approvals", "12", "manager"),
            ("Timecard Exceptions", "07", "manager"),
            ("Benefit Enrollment", "24", "admin"),
            ("Compliance Alerts", "05", "admin"),
            ("My Tasks", "09", "employee"),
            ("Upcoming Check Date", "Fri", "all"),
        ]

        def visible(t):
            _, _, role = t
            return role == "all" or role == user.role or (user.role == "admin" and role in {"manager", "employee"})

        tile_html = "".join(
            f"<article class='tile'><p class='label'>{label}</p><p class='value'>{value}</p></article>"
            for label, value, _ in tiles
            if visible((label, value, _))
        )
        admin_link = "<a href='/admin'>Admin</a>" if user.role == "admin" else ""
        return f"""
<!doctype html><html><head><title>Dashboard</title>{STYLE}</head><body>
<header><h1>Recurring App</h1><nav>{admin_link}<form method='post' action='/logout'><button>Logout</button></form></nav></header>
<main><h2>Welcome, {user.full_name}</h2><p class='subtitle'>Role: {user.role}</p>
<section class='tiles'>{tile_html}</section></main></body></html>
"""

    def _render_admin(self) -> str:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT full_name, email, role FROM users ORDER BY role, full_name").fetchall()
        table_rows = "".join(f"<tr><td>{r['full_name']}</td><td>{r['email']}</td><td>{r['role']}</td></tr>" for r in rows)
        return f"""
<!doctype html><html><head><title>Admin</title>{STYLE}</head><body>
<header><h1>Recurring App</h1><nav><a href='/dashboard'>Dashboard</a></nav></header>
<main><h2>Admin User Directory</h2><table><tr><th>Name</th><th>Email</th><th>Role</th></tr>{table_rows}</table></main>
</body></html>
"""

    def _render_forbidden(self, user: SessionUser) -> str:
        return f"""
<!doctype html><html><head><title>Forbidden</title>{STYLE}</head><body>
<header><h1>Recurring App</h1></header>
<main><h2>Access denied for role: {user.role}</h2><a href='/dashboard'>Return to dashboard</a></main>
</body></html>
"""


STYLE = """
<style>
body{margin:0;font-family:Arial,sans-serif;background:#f4f7fb;color:#1b2230}header{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:#1b4c9b;color:#fff}nav{display:flex;gap:10px;align-items:center}a,button{border:1px solid #ffffff99;padding:6px 10px;border-radius:7px;background:transparent;color:#fff;text-decoration:none}.shell{display:flex;justify-content:center;padding-top:60px}.card{width:380px;background:#fff;padding:18px;border-radius:12px;box-shadow:0 7px 20px #1b4c9b30}label{display:block;margin-bottom:10px}input{width:100%;margin-top:5px;padding:8px}.hint{color:#516079}.error{background:#ffdede;padding:8px;border-radius:8px}.subtitle{color:#516079}.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}.tile{background:linear-gradient(145deg,#fff,#edf4ff);border:1px solid #d4e2ff;border-radius:14px;padding:12px;min-height:100px}.label{margin:0;color:#45608b}.value{margin-top:10px;font-size:2rem;color:#123b7a;font-weight:700}main{max-width:1000px;margin:18px auto;padding:0 12px}table{width:100%;border-collapse:collapse;background:#fff}th,td{border:1px solid #dfe7f2;padding:8px;text-align:left}
</style>
"""


def make_app(db_path: str = "instance/recurring.db") -> RecurringApp:
    app = RecurringApp(db_path)
    app.bootstrap()
    return app
