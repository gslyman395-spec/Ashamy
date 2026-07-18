import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import { backtestStock } from '../services/api.js';
import NavBar from '../components/NavBar.jsx';

export default function BacktestPage() {
  const [symbol, setSymbol] = useState('AAPL');
  const [period, setPeriod] = useState('2y');
  const [capital, setCapital] = useState(100000);

  const mutation = useMutation({
    mutationFn: backtestStock,
    onError: (err) => toast.error(`خطأ: ${err.response?.data?.detail || err.message}`),
  });

  const handleBacktest = () => {
    if (!symbol.trim()) return toast.error('أدخل رمز السهم');
    mutation.mutate({
      symbol: symbol.toUpperCase(),
      period,
      initial_capital: Number(capital),
    });
  };

  const data = mutation.data;
  const m = data?.metrics;

  return (
    <div className="min-h-screen bg-dark">
      <NavBar />
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Controls */}
        <div className="card flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">رمز السهم</label>
            <input
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white uppercase w-32 focus:outline-none focus:ring-2 focus:ring-primary"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">الفترة</label>
            <select
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              {['1y', '2y', '5y'].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">رأس المال ($)</label>
            <input
              type="number"
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white w-40 focus:outline-none"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
            />
          </div>
          <button
            onClick={handleBacktest}
            disabled={mutation.isPending}
            className="bg-primary hover:bg-sky-400 disabled:opacity-50 text-white font-bold px-6 py-2 rounded-lg transition"
          >
            {mutation.isPending ? '⏳ جاري الاختبار...' : '🚀 اختبار'}
          </button>
        </div>

        {/* Metrics */}
        {m && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <MetricCard label="إجمالي العائد" value={`${m.total_return}%`} color={m.total_return >= 0 ? 'text-success' : 'text-danger'} />
            <MetricCard label="CAGR" value={`${m.cagr}%`} color={m.cagr >= 0 ? 'text-success' : 'text-danger'} />
            <MetricCard label="رأس المال النهائي" value={`$${m.final_equity.toLocaleString()}`} />
            <MetricCard label="أقصى تراجع" value={`${m.max_drawdown}%`} color="text-danger" />
            <MetricCard label="شارب" value={m.sharpe_ratio} />
            <MetricCard label="سورتينو" value={m.sortino_ratio} />
            <MetricCard label="عدد الصفقات" value={m.total_trades} />
            <MetricCard label="معدل الفوز" value={`${m.win_rate}%`} color={m.win_rate >= 50 ? 'text-success' : 'text-danger'} />
            <MetricCard label="متوسط الربح" value={`${m.avg_win_pct}%`} color="text-success" />
            <MetricCard label="متوسط الخسارة" value={`${m.avg_loss_pct}%`} color="text-danger" />
            <MetricCard label="معامل الربح" value={m.profit_factor} />
            <MetricCard label="التوقع الرياضي" value={`${m.expectancy}%`} />
          </div>
        )}

        {/* Equity Curve */}
        {data?.equity_curve?.length > 0 && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4 text-slate-200">📈 منحنى الأسهم</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={data.equity_curve}>
                <defs>
                  <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} interval="preserveStartEnd" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v) => [`$${v.toLocaleString()}`, 'القيمة']}
                />
                <Area type="monotone" dataKey="equity" stroke="#0ea5e9" fill="url(#equityGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Report */}
        {data?.report_text && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-3 text-slate-200">📄 التقرير</h2>
            <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
              {data.report_text}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, color = 'text-primary' }) {
  return (
    <div className="card text-center">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`font-bold text-xl ${color}`}>{value}</div>
    </div>
  );
}
