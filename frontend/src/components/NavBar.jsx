import { Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';

export default function NavBar() {
  const { pathname } = useLocation();
  return (
    <nav className="bg-card border-b border-slate-700 px-4 py-3 flex items-center gap-6">
      <span className="text-primary font-bold text-xl">📈 Ashamy</span>
      <Link
        to="/analysis"
        className={clsx(
          'text-sm font-medium px-3 py-1 rounded-lg transition',
          pathname === '/analysis' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
        )}
      >
        التحليل
      </Link>
      <Link
        to="/backtest"
        className={clsx(
          'text-sm font-medium px-3 py-1 rounded-lg transition',
          pathname === '/backtest' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
        )}
      >
        الباك تست
      </Link>
    </nav>
  );
}
