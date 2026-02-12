export default function LoginPage() {
  return (
    <main className="container" style={{ maxWidth: 480 }}>
      <h1>Login</h1>
      <form action="/api/auth/login" method="post">
        <input name="email" type="email" placeholder="Email" required />
        <input name="password" type="password" placeholder="Password" required />
        <button className="button" type="submit">Login</button>
      </form>
      <p className="muted">No account? <a href="/register">Create one</a></p>
    </main>
  );
}
