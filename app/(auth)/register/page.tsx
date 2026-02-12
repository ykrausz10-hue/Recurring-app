export default function RegisterPage() {
  return (
    <main className="container" style={{ maxWidth: 520 }}>
      <h1>Create account</h1>
      <form action="/api/auth/register" method="post">
        <input name="name" placeholder="Full name" required />
        <input name="email" type="email" placeholder="Email" required />
        <input name="password" type="password" placeholder="Password" required minLength={8} />
        <select name="role" defaultValue="CANDIDATE">
          <option value="CANDIDATE">Candidate</option>
          <option value="RECRUITER">Recruiter</option>
          <option value="HIRING_MANAGER">Hiring Manager</option>
          <option value="ADMIN">Admin</option>
        </select>
        <button className="button" type="submit">Register</button>
      </form>
    </main>
  );
}
