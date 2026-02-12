import './globals.css';
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="nav">
          <Link href="/">Nursing Homes Talent Hub</Link>
          <div style={{ display: 'flex', gap: 12 }}>
            <Link href="/careers">Careers</Link>
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/login">Login</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
