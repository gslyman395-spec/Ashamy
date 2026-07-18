import clsx from 'clsx';

/**
 * Renders a scrollable list of trading signals detected in the analysis.
 */
export default function SignalsList({ signals = [] }) {
  if (signals.length === 0) {
    return (
      <div className="card text-center text-slate-400 py-8">
        لا توجد إشارات في الفترة المحددة
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3 text-slate-200">
        📡 الإشارات ({signals.length})
      </h2>
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {signals
          .slice()
          .reverse()
          .map((s, i) => (
            <SignalRow key={i} signal={s} />
          ))}
      </div>
    </div>
  );
}

function SignalRow({ signal }) {
  const isBuy = signal.signal === 1;
  return (
    <div
      className={clsx(
        'flex items-center justify-between rounded-lg px-3 py-2 text-sm',
        isBuy ? 'bg-emerald-900/40 border border-emerald-700' : 'bg-red-900/40 border border-red-700'
      )}
    >
      <div className="flex items-center gap-2">
        <span className={clsx('font-bold', isBuy ? 'text-success' : 'text-danger')}>
          {isBuy ? '▲ شراء' : '▼ بيع'}
        </span>
        <span className="text-slate-400">{signal.date}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-slate-100">${signal.price.toFixed(2)}</span>
        <span
          className={clsx(
            'text-xs px-2 py-0.5 rounded-full font-semibold',
            isBuy ? 'bg-emerald-700 text-white' : 'bg-red-700 text-white'
          )}
        >
          {Math.round(signal.confidence * 100)}%
        </span>
      </div>
    </div>
  );
}
