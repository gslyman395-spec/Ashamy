import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AnalysisPage from './pages/AnalysisPage.jsx';
import BacktestPage from './pages/BacktestPage.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/analysis" replace />} />
        <Route path="/analysis" element={<AnalysisPage />} />
        <Route path="/backtest" element={<BacktestPage />} />
      </Routes>
    </BrowserRouter>
  );
}
