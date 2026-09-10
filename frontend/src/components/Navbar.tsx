import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard', exact: true },
  { path: '/problems', label: 'Problems' },
  { path: '/history', label: 'History' },
];

export function Navbar() {
  const location = useLocation();

  return (
    <header className="fixed top-0 left-0 right-0 z-50"
      style={{ background: '#0C0F13', borderBottom: '1px solid #1E252E' }}>
      <div className="max-w-6xl mx-auto px-5">
        <div className="flex items-center justify-between h-12">

          {/* Product mark */}
          <Link to="/" className="flex items-center gap-2.5 group focus:outline-none">
            <div style={{
              width: 22, height: 22,
              background: '#0EA5A0',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700,
                color: '#0C0F13', lineHeight: 1,
              }}>L</span>
            </div>
            <span style={{
              fontWeight: 600, fontSize: 13, color: '#E8EDF2',
              letterSpacing: '-0.01em',
            }}>
              LLD Lab
            </span>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 9,
              color: '#56636F', letterSpacing: '0.06em', textTransform: 'uppercase',
              background: '#1E252E', padding: '1px 5px',
            }}>
              v1
            </span>
          </Link>

          {/* Nav */}
          <nav className="flex items-center gap-1">
            {navItems.map(({ path, label, exact }) => {
              const active = exact
                ? location.pathname === path
                : location.pathname === path || location.pathname.startsWith(path + '/');
              return (
                <Link
                  key={path}
                  to={path}
                  style={{
                    fontSize: 12,
                    fontWeight: 500,
                    padding: '4px 10px',
                    color: active ? '#2DD4BF' : '#8B97A4',
                    borderBottom: active ? '1px solid #0EA5A0' : '1px solid transparent',
                    transition: 'color 0.15s, border-color 0.15s',
                    textDecoration: 'none',
                    letterSpacing: '0.01em',
                  }}
                  onMouseEnter={e => {
                    if (!active) (e.currentTarget as HTMLElement).style.color = '#E8EDF2';
                  }}
                  onMouseLeave={e => {
                    if (!active) (e.currentTarget as HTMLElement).style.color = '#8B97A4';
                  }}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
