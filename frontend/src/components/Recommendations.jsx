import clsx from 'clsx';

/**
 * Displays the current recommendation badge and key indicator values.
 */
export default function Recommendations({ recommendation, confidence, indicators }) {
  const color =
    recommendation === 'BUY'
      ? 'bg-success'
      : recommendation === 'SELL'
      ? 'bg-danger'
      : 'bg-warning';

  const label =
    recommendation === 'BUY'
      ? '🟢 شراء'
      : recommendation === 'SELL'
      ? '🔴 بيع'
      : '🟡 انتظار';

  const pct = Math.round((confidence || 0) * 100);

  return (
    <div className="card space-y-4">
      <h2 className="text-lg font-semibold text-slate-200">🎯 التوصية</h2>

      <div className="flex items-center gap-4">
        <span className={clsx('px-5 py-2 rounded-full text-white font-bold text-xl', color)}>
          {label}
        </span>
        <div className="flex flex-col">
          <span className="text-xs text-slate-400">مستوى الثقة</span>
          <span className="text-2xl font-bold text-primary">{pct}%</span>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="w-full bg-slate-700 rounded-full h-2">
        <div
          className={clsx('h-2 rounded-full', color)}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Key indicators */}
      {indicators && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          {indicators.rsi != null && (
            <Stat label="RSI" value={indicators.rsi.toFixed(2)} />
          )}
          {indicators.macd != null && (
            <Stat label="MACD" value={indicators.macd.toFixed(4)} />
          )}
          {indicators.sma_20 != null && (
            <Stat label="SMA 20" value={indicators.sma_20.toFixed(2)} />
          )}
          {indicators.sma_50 != null && (
            <Stat label="SMA 50" value={indicators.sma_50.toFixed(2)} />
          )}
          {indicators.bb_upper != null && (
            <Stat label="BB علوي" value={indicators.bb_upper.toFixed(2)} />
          )}
          {indicators.bb_lower != null && (
            <Stat label="BB سفلي" value={indicators.bb_lower.toFixed(2)} />
          )}
          {indicators.stoch_k != null && (
            <Stat label="Stoch %K" value={indicators.stoch_k.toFixed(2)} />
          )}
          {indicators.atr != null && (
            <Stat label="ATR" value={indicators.atr.toFixed(4)} />
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-slate-800 rounded-lg px-3 py-2 flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-mono text-slate-100">{value}</span>
    </div>
  );
}
