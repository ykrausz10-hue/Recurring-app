from __future__ import annotations

from http import cookies
from urllib.parse import parse_qs

from .auth import SessionUser, make_session_token, verify_password
from .db import connect, init_db
from .seed import seed_default_users


PIPELINE_STATUSES = ["submitted", "screening", "interview", "offer", "hired", "rejected"]


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

        if path == "/admin/jobs" and method == "GET":
            if not user:
                return self._redirect(start_response, "/login")
            if user.role != "admin":
                return self._forbidden(start_response, self._render_forbidden(user))
            return self._ok(start_response, self._render_admin_jobs())

        if path == "/admin/jobs" and method == "POST":
            if not user:
                return self._redirect(start_response, "/login")
            if user.role != "admin":
                return self._forbidden(start_response, self._render_forbidden(user))
            return self._handle_create_job(environ, start_response)

        if path.startswith("/admin/jobs/") and method == "POST":
            if not user:
                return self._redirect(start_response, "/login")
            if user.role != "admin":
                return self._forbidden(start_response, self._render_forbidden(user))
            return self._handle_job_action(path, environ, start_response)

        if path == "/admin/ats" and method == "GET":
            if not user:
                return self._redirect(start_response, "/login")
            if user.role != "admin":
                return self._forbidden(start_response, self._render_forbidden(user))
            return self._ok(start_response, self._render_ats_board())

        if path.startswith("/admin/applications/") and method == "GET":
            if not user:
                return self._redirect(start_response, "/login")
            if user.role != "admin":
                return self._forbidden(start_response, self._render_forbidden(user))
            app_id = self._parse_admin_application_id(path)
            return self._ok(start_response, self._render_candidate_profile(app_id)) if app_id else self._not_found(start_response)

        if path.startswith("/admin/applications/") and method == "POST":
            if not user:
                return self._redirect(start_response, "/login")
            if user.role != "admin":
                return self._forbidden(start_response, self._render_forbidden(user))
            app_id = self._parse_admin_application_id(path)
            return self._handle_application_action(app_id, path, environ, start_response, user) if app_id else self._not_found(start_response)

        if path == "/jobs" and method == "GET":
            return self._ok(start_response, self._render_public_jobs())

        if path.startswith("/jobs/") and path.endswith("/apply") and method == "GET":
            job_id = self._parse_job_id(path, suffix="/apply")
            return self._ok(start_response, self._render_apply_form(job_id)) if job_id else self._not_found(start_response)

        if path.startswith("/jobs/") and path.endswith("/apply") and method == "POST":
            job_id = self._parse_job_id(path, suffix="/apply")
            return self._handle_apply(job_id, environ, start_response) if job_id else self._not_found(start_response)

        return self._not_found(start_response)

    def _not_found(self, start_response):
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Not Found"]

    def _parse_form(self, environ) -> dict[str, str]:
        length = int(environ.get("CONTENT_LENGTH") or "0")
        body = environ["wsgi.input"].read(length).decode("utf-8")
        parsed = parse_qs(body)
        return {k: v[0] for k, v in parsed.items()}

    def _parse_job_id(self, path: str, suffix: str = "") -> int | None:
        base = path[: -len(suffix)] if suffix else path
        parts = [p for p in base.split("/") if p]
        if len(parts) < 2:
            return None
        try:
            return int(parts[1] if parts[0] == "jobs" else parts[2])
        except (ValueError, IndexError):
            return None

    def _parse_admin_application_id(self, path: str) -> int | None:
        parts = [p for p in path.split("/") if p]
        if len(parts) < 3:
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

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

    def _handle_create_job(self, environ, start_response):
        data = self._parse_form(environ)
        title = data.get("title", "").strip()
        department = data.get("department", "").strip()
        location = data.get("location", "").strip()
        description = data.get("description", "").strip()

        if not all([title, department, location, description]):
            return self._ok(
                start_response,
                self._render_admin_jobs(
                    error="All job fields are required.",
                    form_data={
                        "title": title,
                        "department": department,
                        "location": location,
                        "description": description,
                    },
                ),
            )

        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO jobs(title, department, location, description, status)
                VALUES (?, ?, ?, ?, 'open')
                """,
                (title, department, location, description),
            )
            conn.commit()

        return self._redirect(start_response, "/admin/jobs")

    def _handle_job_action(self, path: str, environ, start_response):
        if path.endswith("/update"):
            job_id = self._parse_job_id(path, suffix="/update")
            if not job_id:
                return self._not_found(start_response)
            data = self._parse_form(environ)
            title = data.get("title", "").strip()
            department = data.get("department", "").strip()
            location = data.get("location", "").strip()
            description = data.get("description", "").strip()
            status = data.get("status", "open").strip()
            if status not in {"open", "closed"}:
                status = "open"
            with connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE jobs
                    SET title = ?, department = ?, location = ?, description = ?, status = ?
                    WHERE id = ?
                    """,
                    (title, department, location, description, status, job_id),
                )
                conn.commit()
            return self._redirect(start_response, "/admin/jobs")

        if path.endswith("/delete"):
            job_id = self._parse_job_id(path, suffix="/delete")
            if not job_id:
                return self._not_found(start_response)
            with connect(self.db_path) as conn:
                conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                conn.commit()
            return self._redirect(start_response, "/admin/jobs")

        return self._not_found(start_response)

    def _handle_apply(self, job_id: int, environ, start_response):
        with connect(self.db_path) as conn:
            job = conn.execute("SELECT id, title, status FROM jobs WHERE id = ?", (job_id,)).fetchone()

        if not job:
            return self._not_found(start_response)

        if job["status"] != "open":
            return self._ok(start_response, self._render_apply_form(job_id, error="This job is no longer accepting applications."))

        data = self._parse_form(environ)
        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip().lower()
        resume_text = data.get("resume_text", "").strip()

        if not all([full_name, email, resume_text]):
            return self._ok(start_response, self._render_apply_form(job_id, "All fields are required."))

        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO applications(job_id, full_name, email, resume_text, status)
                VALUES (?, ?, ?, ?, 'submitted')
                """,
                (job_id, full_name, email, resume_text),
            )
            conn.commit()

        return self._ok(start_response, self._render_apply_success(job["title"]))

    def _handle_application_action(self, application_id: int, path: str, environ, start_response, user: SessionUser):
        with connect(self.db_path) as conn:
            exists = conn.execute("SELECT id FROM applications WHERE id = ?", (application_id,)).fetchone()
            if not exists:
                return self._not_found(start_response)

            if path.endswith("/status"):
                status = self._parse_form(environ).get("status", "submitted").strip()
                if status not in PIPELINE_STATUSES:
                    status = "submitted"
                conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, application_id))
                conn.commit()
                return self._redirect(start_response, f"/admin/applications/{application_id}")

            if path.endswith("/notes"):
                note_text = self._parse_form(environ).get("note_text", "").strip()
                if note_text:
                    conn.execute(
                        """
                        INSERT INTO candidate_notes(application_id, author_user_id, note_text)
                        VALUES (?, ?, ?)
                        """,
                        (application_id, user.user_id, note_text),
                    )
                    conn.commit()
                return self._redirect(start_response, f"/admin/applications/{application_id}")

            if path.endswith("/tasks"):
                data = self._parse_form(environ)
                title = data.get("title", "").strip()
                due_date = data.get("due_date", "").strip()
                if title:
                    conn.execute(
                        """
                        INSERT INTO candidate_tasks(application_id, assignee_user_id, title, due_date)
                        VALUES (?, ?, ?, ?)
                        """,
                        (application_id, user.user_id, title, due_date or None),
                    )
                    conn.commit()
                return self._redirect(start_response, f"/admin/applications/{application_id}")

            if path.endswith("/tasks/complete"):
                task_id_raw = self._parse_form(environ).get("task_id", "0")
                try:
                    task_id = int(task_id_raw)
                except ValueError:
                    task_id = 0
                if task_id:
                    conn.execute(
                        "UPDATE candidate_tasks SET status = 'done' WHERE id = ? AND application_id = ?",
                        (task_id, application_id),
                    )
                    conn.commit()
                return self._redirect(start_response, f"/admin/applications/{application_id}")

        return self._not_found(start_response)

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
<header><h1>Recurring App</h1><nav>{admin_link}<a href='/jobs'>Jobs</a><form method='post' action='/logout'><button>Logout</button></form></nav></header>
<main><h2>Welcome, {user.full_name}</h2><p class='subtitle'>Role: {user.role}</p>
<section class='tiles'>{tile_html}</section></main></body></html>
"""

    def _render_admin(self) -> str:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT full_name, email, role FROM users ORDER BY role, full_name").fetchall()
        table_rows = "".join(f"<tr><td>{r['full_name']}</td><td>{r['email']}</td><td>{r['role']}</td></tr>" for r in rows)
        return f"""
<!doctype html><html><head><title>Admin</title>{STYLE}</head><body>
<header><h1>Recurring App</h1><nav><a href='/dashboard'>Dashboard</a><a href='/admin/jobs'>Manage Jobs</a><a href='/admin/ats'>ATS Pipeline</a></nav></header>
<main><h2>Admin User Directory</h2><table><tr><th>Name</th><th>Email</th><th>Role</th></tr>{table_rows}</table></main>
</body></html>
"""

    def _render_admin_jobs(self, error: str = "", form_data: dict[str, str] | None = None) -> str:
        form_data = form_data or {}
        with connect(self.db_path) as conn:
            jobs = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
            counts = {row["job_id"]: row["total"] for row in conn.execute("SELECT job_id, COUNT(*) as total FROM applications GROUP BY job_id").fetchall()}

        job_rows = "".join(
            f"""
            <article class='job-card'>
              <form method='post' action='/admin/jobs/{job['id']}/update'>
                <label>Title <input name='title' value='{job['title']}' required></label>
                <label>Department <input name='department' value='{job['department']}' required></label>
                <label>Location <input name='location' value='{job['location']}' required></label>
                <label>Description <textarea name='description' required>{job['description']}</textarea></label>
                <label>Status
                  <select name='status'>
                    <option value='open' {'selected' if job['status'] == 'open' else ''}>Open</option>
                    <option value='closed' {'selected' if job['status'] == 'closed' else ''}>Closed</option>
                  </select>
                </label>
                <p class='hint'>Applications: {counts.get(job['id'], 0)}</p>
                <button type='submit'>Update Job</button>
              </form>
              <form method='post' action='/admin/jobs/{job['id']}/delete'>
                <button class='danger' type='submit'>Delete Job</button>
              </form>
            </article>
            """
            for job in jobs
        )
        return f"""
<!doctype html><html><head><title>Admin Jobs</title>{STYLE}</head><body>
<header><h1>Recurring App</h1><nav><a href='/admin'>Admin</a><a href='/admin/ats'>ATS Pipeline</a><a href='/jobs'>Public Jobs</a></nav></header>
<main>
  <h2>Job Posting Management</h2>
  {'<p class="error">'+error+'</p>' if error else ''}
  <section class='card'>
    <h3>Create Job</h3>
    <form method='post' action='/admin/jobs' id='create-job-form'>
      <label>Title <input name='title' value='{form_data.get("title", "")}' required></label>
      <label>Department <input name='department' value='{form_data.get("department", "")}' required></label>
      <label>Location <input name='location' value='{form_data.get("location", "")}' required></label>
      <label>Description <textarea name='description' required>{form_data.get("description", "")}</textarea></label>
      <button class='action create-job-button' type='submit'>Create Job</button>
    </form>
  </section>
  <section><h3>Existing Jobs</h3><div class='jobs-grid'>{job_rows or '<p>No jobs yet.</p>'}</div></section>
</main>
</body></html>
"""

    def _render_ats_board(self) -> str:
        with connect(self.db_path) as conn:
            apps = conn.execute(
                """
                SELECT a.id, a.full_name, a.email, a.status, j.title AS job_title
                FROM applications a
                JOIN jobs j ON j.id = a.job_id
                ORDER BY a.created_at DESC
                """
            ).fetchall()

        columns = []
        for status in PIPELINE_STATUSES:
            cards = "".join(
                f"<article class='kanban-card'><h4>{a['full_name']}</h4><p>{a['job_title']}</p><a class='action' href='/admin/applications/{a['id']}'>View profile</a></article>"
                for a in apps
                if a["status"] == status
            )
            empty = "<p class='hint'>No candidates</p>"
            columns.append(f"<section class='kanban-col'><h3>{status.title()}</h3>{cards or empty}</section>")

        return f"""
<!doctype html><html><head><title>ATS Pipeline</title>{STYLE}</head><body>
<header><h1>Recurring App</h1><nav><a href='/admin'>Admin</a><a href='/admin/jobs'>Manage Jobs</a></nav></header>
<main>
  <h2>ATS Pipeline Board</h2>
  <div class='kanban-board'>{''.join(columns)}</div>
</main>
</body></html>
"""

    def _render_candidate_profile(self, application_id: int, error: str = "") -> str:
        with connect(self.db_path) as conn:
            app_row = conn.execute(
                """
                SELECT a.*, j.title AS job_title, j.department, j.location
                FROM applications a
                JOIN jobs j ON j.id = a.job_id
                WHERE a.id = ?
                """,
                (application_id,),
            ).fetchone()
            if not app_row:
                return "<!doctype html><html><body><h1>Candidate not found</h1></body></html>"

            notes = conn.execute(
                """
                SELECT n.note_text, n.created_at, COALESCE(u.full_name, 'System') AS author
                FROM candidate_notes n
                LEFT JOIN users u ON u.id = n.author_user_id
                WHERE n.application_id = ?
                ORDER BY n.created_at DESC
                """,
                (application_id,),
            ).fetchall()
            tasks = conn.execute(
                """
                SELECT t.id, t.title, t.status, t.due_date, COALESCE(u.full_name, 'Unassigned') AS assignee
                FROM candidate_tasks t
                LEFT JOIN users u ON u.id = t.assignee_user_id
                WHERE t.application_id = ?
                ORDER BY t.created_at DESC
                """,
                (application_id,),
            ).fetchall()

        note_items = "".join(f"<li><strong>{n['author']}</strong> ({n['created_at']}): {n['note_text']}</li>" for n in notes)
        task_items = "".join(
            f"<li>{t['title']} · {t['status']} · {t['assignee']} · due {t['due_date'] or 'TBD'}"
            + (
                ""
                if t["status"] == "done"
                else f"<form method='post' action='/admin/applications/{application_id}/tasks/complete'><input type='hidden' name='task_id' value='{t['id']}'><button type='submit'>Mark done</button></form>"
            )
            + "</li>"
            for t in tasks
        )
        options = "".join(
            f"<option value='{status}' {'selected' if app_row['status'] == status else ''}>{status.title()}</option>"
            for status in PIPELINE_STATUSES
        )

        return f"""
<!doctype html><html><head><title>Candidate Profile</title>{STYLE}</head><body>
<header><h1>Recurring App</h1><nav><a href='/admin/ats'>ATS Pipeline</a><a href='/admin/jobs'>Manage Jobs</a></nav></header>
<main>
  <h2>Candidate Profile: {app_row['full_name']}</h2>
  <p class='subtitle'>Applied for {app_row['job_title']} · {app_row['department']} · {app_row['location']}</p>
  <p>Email: {app_row['email']}</p>
  <section class='card'>
    <h3>Resume</h3>
    <p>{app_row['resume_text']}</p>
  </section>
  <section class='card'>
    <h3>Pipeline Stage</h3>
    <form method='post' action='/admin/applications/{application_id}/status'>
      <label>Status <select name='status'>{options}</select></label>
      <button class='action' type='submit'>Update status</button>
    </form>
  </section>
  <section class='card'>
    <h3>Interview Notes</h3>
    {'<p class="error">'+error+'</p>' if error else ''}
    <form method='post' action='/admin/applications/{application_id}/notes'>
      <label>Add note <textarea name='note_text' required></textarea></label>
      <button class='action' type='submit'>Save note</button>
    </form>
    <ul>{note_items or '<li>No notes yet.</li>'}</ul>
  </section>
  <section class='card'>
    <h3>Tasks</h3>
    <form method='post' action='/admin/applications/{application_id}/tasks'>
      <label>Task title <input name='title' required></label>
      <label>Due date <input name='due_date' placeholder='YYYY-MM-DD'></label>
      <button class='action' type='submit'>Create task</button>
    </form>
    <ul>{task_items or '<li>No tasks yet.</li>'}</ul>
  </section>
</main>
</body></html>
"""

    def _render_public_jobs(self) -> str:
        with connect(self.db_path) as conn:
            jobs = conn.execute("SELECT id, title, department, location, description FROM jobs WHERE status = 'open' ORDER BY id DESC").fetchall()

        cards = "".join(
            f"""
            <article class='job-card'>
              <h3>{job['title']}</h3>
              <p class='subtitle'>{job['department']} · {job['location']}</p>
              <p>{job['description']}</p>
              <a class='action' href='/jobs/{job['id']}/apply'>Apply</a>
            </article>
            """
            for job in jobs
        )

        return f"""
<!doctype html><html><head><title>Open Jobs</title>{STYLE}</head><body>
<header><h1>Recurring Careers</h1><nav><a href='/login'>Employee Login</a></nav></header>
<main><h2>Open Roles</h2><div class='jobs-grid'>{cards or '<p>No open jobs right now.</p>'}</div></main>
</body></html>
"""

    def _render_apply_form(self, job_id: int, error: str = "") -> str:
        with connect(self.db_path) as conn:
            job = conn.execute("SELECT id, title, department, location, status FROM jobs WHERE id = ?", (job_id,)).fetchone()

        if not job:
            return "<!doctype html><html><body><h1>Job not found</h1></body></html>"

        closed_note = "<p class='error'>This job is closed.</p>" if job["status"] != "open" else ""
        disabled = "disabled" if job["status"] != "open" else ""

        return f"""
<!doctype html><html><head><title>Apply - {job['title']}</title>{STYLE}</head><body>
<header><h1>Recurring Careers</h1><nav><a href='/jobs'>Back to Jobs</a></nav></header>
<main>
  <h2>Apply for {job['title']}</h2>
  <p class='subtitle'>{job['department']} · {job['location']}</p>
  {closed_note}
  {'<p class="error">'+error+'</p>' if error else ''}
  <section class='card'>
    <form method='post' action='/jobs/{job['id']}/apply'>
      <label>Full name <input name='full_name' required {disabled}></label>
      <label>Email <input type='email' name='email' required {disabled}></label>
      <label>Resume summary <textarea name='resume_text' required {disabled}></textarea></label>
      <button type='submit' {disabled}>Submit Application</button>
    </form>
  </section>
</main>
</body></html>
"""

    def _render_apply_success(self, title: str) -> str:
        return f"""
<!doctype html><html><head><title>Application Submitted</title>{STYLE}</head><body>
<header><h1>Recurring Careers</h1></header>
<main><section class='card'><h2>Application submitted</h2><p>Thanks for applying to {title}.</p><a class='action' href='/jobs'>View other jobs</a></section></main>
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
body{margin:0;font-family:Arial,sans-serif;background:#f4f7fb;color:#1b2230}header{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:#1b4c9b;color:#fff}nav{display:flex;gap:10px;align-items:center;flex-wrap:wrap}a,button{border:1px solid #ffffff99;padding:6px 10px;border-radius:7px;background:transparent;color:#fff;text-decoration:none;cursor:pointer}.action{border-color:#1b4c9b;background:#1b4c9b;color:#fff;display:inline-block}.create-job-button{font-weight:700}.shell{display:flex;justify-content:center;padding-top:60px}.card{width:min(720px,100%);background:#fff;padding:18px;border-radius:12px;box-shadow:0 7px 20px #1b4c9b30;margin-bottom:12px}label{display:block;margin-bottom:10px}input,textarea,select{width:100%;margin-top:5px;padding:8px;box-sizing:border-box}.hint{color:#516079}.error{background:#ffdede;padding:8px;border-radius:8px}.subtitle{color:#516079}.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}.tile{background:linear-gradient(145deg,#fff,#edf4ff);border:1px solid #d4e2ff;border-radius:14px;padding:12px;min-height:100px}.label{margin:0;color:#45608b}.value{margin-top:10px;font-size:2rem;color:#123b7a;font-weight:700}main{max-width:1100px;margin:18px auto;padding:0 12px}table{width:100%;border-collapse:collapse;background:#fff}th,td{border:1px solid #dfe7f2;padding:8px;text-align:left}.jobs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}.job-card,.kanban-card{background:#fff;border:1px solid #dfe7f2;border-radius:12px;padding:12px}.danger{border-color:#b20d2d;color:#b20d2d;background:#fff}.kanban-board{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px}.kanban-col{background:#e9f0ff;border-radius:12px;padding:10px}ul{padding-left:20px}li{margin-bottom:8px}
</style>
"""


def make_app(db_path: str = "instance/recurring.db") -> RecurringApp:
    app = RecurringApp(db_path)
    app.bootstrap()
    return app
