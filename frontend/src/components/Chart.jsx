import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

/**
 * Candlestick chart using TradingView's lightweight-charts library.
 * Renders OHLCV bars and overlays buy/sell signal markers.
 */
export default function Chart({ candles = [], signals = [] }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;

    // Clean up previous instance
    if (chartRef.current) {
      chartRef.current.remove();
    }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 420,
      layout: {
        background: { color: '#1e293b' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#334155' },
        horzLines: { color: '#334155' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#475569' },
      timeScale: { borderColor: '#475569', rightOffset: 5 },
    });
    chartRef.current = chart;

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    const chartData = candles.map((c) => ({
      time: c.date,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleSeries.setData(chartData);

    // Signal markers
    const markers = signals.map((s) => ({
      time: s.date,
      position: s.signal === 1 ? 'belowBar' : 'aboveBar',
      color: s.signal === 1 ? '#22c55e' : '#ef4444',
      shape: s.signal === 1 ? 'arrowUp' : 'arrowDown',
      text: s.signal === 1 ? 'شراء' : 'بيع',
    }));
    if (markers.length > 0) {
      candleSeries.setMarkers(markers);
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [candles, signals]);

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3 text-slate-200">📊 رسم الشموع</h2>
      <div ref={containerRef} />
    </div>
  );
}
