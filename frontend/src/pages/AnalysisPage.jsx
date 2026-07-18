import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { analyzeStock } from '../services/api.js';
import Chart from '../components/Chart.jsx';
import SignalsList from '../components/SignalsList.jsx';
import Recommendations from '../components/Recommendations.jsx';
import NavBar from '../components/NavBar.jsx';

export default function AnalysisPage() {
  const [symbol, setSymbol] = useState('AAPL');
  const [period, setPeriod] = useState('2y');
  const [interval, setInterval] = useState('1d');

  const mutation = useMutation({
    mutationFn: analyzeStock,
    onError: (err) => toast.error(`خطأ: ${err.response?.data?.detail || err.message}`),
  });

  const handleAnalyze = () => {
    if (!symbol.trim()) return toast.error('أدخل رمز السهم');
    mutation.mutate({ symbol: symbol.toUpperCase(), period, interval });
  };

  const data = mutation.data;

  return (
    <div className="min-h-screen bg-dark">
      <NavBar />
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Header */}
        <div className="card flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">رمز السهم</label>
            <input
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white uppercase w-32 focus:outline-none focus:ring-2 focus:ring-primary"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">الفترة</label>
            <select
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              {['3mo', '6mo', '1y', '2y', '5y'].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">الفاصل الزمني</label>
            <select
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none"
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
            >
              {['1d', '1wk', '1mo'].map((iv) => (
                <option key={iv} value={iv}>{iv}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={mutation.isPending}
            className="bg-primary hover:bg-sky-400 disabled:opacity-50 text-white font-bold px-6 py-2 rounded-lg transition"
          >
            {mutation.isPending ? '⏳ جاري التحليل...' : '🔍 تحليل'}
          </button>
        </div>

        {/* Results */}
        {data && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Chart candles={data.candles} signals={data.signals} />
              </div>
              <Recommendations
                recommendation={data.latest_recommendation}
                confidence={data.latest_confidence}
                indicators={data.latest_indicators}
              />
            </div>
            <SignalsList signals={data.signals} />
            <StrategyAgreement agreement={data.strategy_agreement} />
          </>
        )}
      </div>
    </div>
  );
}

function StrategyAgreement({ agreement }) {
  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3 text-slate-200">🤝 اتفاق الاستراتيجيات</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
        {Object.entries(agreement).map(([name, sig]) => (
          <div key={name} className="bg-slate-800 rounded-lg px-3 py-2 text-center">
            <div className="text-xs text-slate-400 uppercase">{name}</div>
            <div
              className={`font-bold text-sm mt-1 ${
                sig === 1 ? 'text-success' : sig === -1 ? 'text-danger' : 'text-warning'
              }`}
            >
              {sig === 1 ? 'شراء ▲' : sig === -1 ? 'بيع ▼' : 'محايد'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
